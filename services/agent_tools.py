import logging
import json
from typing import List, Dict, Any
from repositories.chunk import chunk_repository
from repositories.prompt import prompt_repository
from services.llm import llm_service
from utils.json_parser import robust_json_parse

logger = logging.getLogger(__name__)

class AgentToolExecutor:
    
    def __init__(self, employee: str):
        self.employee = employee

    def exploratory_search(self, query: str, tags: List[str], exclude: dict) -> List[dict]:
        """
        Récupère un large set de candidats (50) via recherche vectorielle pure.
        """
        logger.info(f"🔍 [Tool] Exploratory Search: '{query}'")
        
        # 1. Récupération des IDs valides
        from repositories.doc import doc_repository
        doc_ids = doc_repository.get_filtered_doc_ids(self.employee, tags)
        
        if not doc_ids:
            logger.warning("   ⚠️ Scope vide (aucun doc correspondant aux tags).")
            return []

        # 2. Recherche large (Limit 50)
        results = chunk_repository.search(
            query=query,
            employee=self.employee,
            limit=50, 
            doc_ids_filter=doc_ids
        )

        candidates = []
        if results['documents']:
            for i, content in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                
                # Exclusion basique
                if exclude.get('sources') and meta.get('source') in exclude['sources']: continue
                if exclude.get('origins') and meta.get('origin') in exclude['origins']: continue

                candidates.append({
                    "content": content,
                    "metadata": meta,
                    "id": results['ids'][0][i]
                })
        
        logger.info(f"   -> {len(candidates)} candidats vectoriels trouvés.")
        return candidates

    def rerank_chunks(self, question: str, chunks: List[dict]) -> List[dict]:
        """
        Évalue la pertinence sémantique via LLM (Prompt: agent_rerank).
        """
        if not chunks:
            return []

        # --- SÉCURITÉ LLM LOCAL ---
        # On limite à 5 ou 7 chunks max pour le reranking pour éviter que Llama3 ne sature
        candidates = chunks[:7] 
        logger.info(f"⚖️ [Tool] Reranking de {len(candidates)} chunks (sur {len(chunks)} reçus)...")
        
        prompt_doc = prompt_repository.get_by_name("agent_rerank")
        if not prompt_doc:
            logger.error("❌ Prompt 'agent_rerank' introuvable ! Fallback sur les 5 premiers.")
            return candidates[:5]

        # Préparation du contexte
        context_text = ""
        for i, c in enumerate(candidates):
            preview = c['content'][:1200].replace("\n", " ") # Nettoyage léger
            context_text += f"--- Chunk {i} ---\n{preview}\n\n"

        final_prompt = prompt_doc.prompt.replace("{question}", question).replace("{context}", context_text)

        try:
            # Appel LLM
            llm_response = llm_service.generate_response(
                system_prompt="Tu es un système de scoring JSON. Réponds UNIQUEMENT avec un tableau JSON.",
                user_input=final_prompt
            )
            
            # Parsing robuste (Gère les tableaux [...])
            scores_data = robust_json_parse(llm_response)
            
            if isinstance(scores_data, dict): scores_data = [scores_data]
            
            if not isinstance(scores_data, list):
                logger.warning(f"⚠️ Format JSON invalide du Reranker. Fallback.")
                return candidates[:3]

            scored_chunks = []
            for item in scores_data:
                idx = item.get("chunk_index")
                score = item.get("score", 0.0)
                
                # Validation des index
                if idx is not None and isinstance(idx, int) and 0 <= idx < len(candidates):
                    chunk = candidates[idx]
                    chunk["score"] = score
                    
                    # Seuil de pertinence (0.5 = Moyen/Bon)
                    if score >= 0.5:
                        scored_chunks.append(chunk)

            # Tri par pertinence
            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"   ✅ Reranking terminé. {len(scored_chunks)} chunks retenus.")
            
            # Fallback si tout est rejeté (pour éviter une réponse vide)
            if not scored_chunks and candidates:
                logger.warning("   ⚠️ Le Reranker a tout rejeté. Récupération de sécurité du Top 1.")
                candidates[0]["score"] = 0.4
                return [candidates[0]]

            return scored_chunks

        except Exception as e:
            logger.error(f"❌ Erreur critique durant le Reranking: {e}")
            return candidates[:3] # Fallback de sécurité