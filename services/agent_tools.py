import logging
import json
import math
from typing import List, Dict, Any
from enum import Enum  # <--- Nouvel import

from repositories.chunk import chunk_repository
from repositories.prompt import prompt_repository
from services.llm import llm_service
from utils.json_parser import robust_json_parse

logger = logging.getLogger(__name__)

# --- 1. Définition des Stratégies (En haut du fichier) ---
class SearchStrategy(Enum):
    GLOBAL = "global_summary"   # Pour comprendre un document entier
    SPECIFIC = "specific_fact"  # Pour trouver une info précise

class AgentToolExecutor:
    
    def __init__(self, employee: str):
        self.employee = employee

    # --- 2. Le Cerveau (Nouvelle Méthode) ---
    def _detect_strategy(self, query: str) -> SearchStrategy:
        """
        Détermine si l'utilisateur veut un résumé global ou un fait précis.
        """
        # Mots-clés qui forcent le mode GLOBAL (pas besoin de payer un appel LLM)
        keywords_global = ["résumé", "synthèse", "analyse", "global", "pass", "aperçu", "about", "sujet", "thème", "topo", "c'est quoi"]
        if any(k in query.lower() for k in keywords_global):
            return SearchStrategy.GLOBAL

        # Sinon, on demande au LLM (Routeur sémantique)
        system_prompt = (
            "Tu es un routeur de recherche. Classifie la demande utilisateur.\n"
            "CHOIX POSSIBLES :\n"
            "1. 'GLOBAL' : Pour des résumés, analyses de fond, compréhension générale, 'de quoi ça parle'.\n"
            "2. 'SPECIFIC' : Pour une question précise, un fait, une date, un nom, un chiffre, une définition technique.\n"
            "Réponds UNIQUEMENT par le mot 'GLOBAL' ou 'SPECIFIC'."
        )
        
        try:
            # Appel rapide au LLM
            decision = llm_service.generate_response(
                system_prompt=system_prompt, 
                user_input=f"Requete: {query}"
            ).strip().upper()
            
            if "GLOBAL" in decision: 
                return SearchStrategy.GLOBAL
            return SearchStrategy.SPECIFIC
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur Router : {e}. Fallback sur SPECIFIC.")
            return SearchStrategy.SPECIFIC

    # --- 3. La Méthode Maîtresse (Celle que le ChatService va appeler) ---
    def smart_retrieve(self, query: str, tags: List[str], exclude: dict) -> dict:
        """
        Point d'entrée principal : Orchestre la recherche selon la stratégie.
        """
        # A. Décision
        strategy = self._detect_strategy(query)
        logger.info(f"🧠 [Router] Stratégie choisie : {strategy.value} pour '{query}'")

        chunks = []
        
        # B. Exécution
        if strategy == SearchStrategy.GLOBAL:
            # STRATÉGIE 1 : VUE D'ENSEMBLE
            # On cherche large, on ne filtre pas trop, on veut du volume.
            
            # 1. Recherche Vectorielle (Large : 50 résultats)
            # On utilise la requête brute ou légèrement nettoyée
            candidates = self.exploratory_search(query, tags, exclude, limit=50)
            
            # 2. Reranking (Doux : On garde le Top 30)
            # On veut garder beaucoup de contexte pour que le ChatService puisse remplir
            chunks = self.rerank_chunks(query, candidates, top_k=30)
            
        else:
            # STRATÉGIE 2 : PRÉCISION (SPECIFIC)
            # On cherche une aiguille dans une botte de foin.
            
            # 1. Recherche Vectorielle (Ciblée : 30 résultats)
            # exploratory_search s'occupera de nettoyer la query (rewriting)
            candidates = self.exploratory_search(query, tags, exclude, limit=30)
            
            # 2. Reranking (Aggressif : On ne garde que le Top 7)
            # On élimine tout le bruit pour ne pas polluer la réponse
            chunks = self.rerank_chunks(query, candidates, top_k=7)

        return {"chunks": chunks, "strategy": strategy}

    # --- 4. Les Outils de base (Vos méthodes existantes, légèrement adaptées) ---

    def exploratory_search(self, query: str, tags: List[str], exclude: dict, limit: int = 50) -> List[dict]:
        """
        Récupère des candidats via recherche vectorielle.
        """
        search_query = query

        # Query Rewriting (uniquement si longue requête et pas déjà traitée)
        if len(query) > 100:
            logger.info("   ✂️ Optimisation de la requête (Rewriting)...")
            system_prompt = (
                "Transforme cette demande en 3 à 5 mots-clés techniques de recherche."
                "Réponds UNIQUEMENT par les mots-clés."
            )
            try:
                keywords = llm_service.generate_response(system_prompt=system_prompt, user_input=f"Demande : {query}")
                search_query = keywords.strip().replace('"', '').replace('\n', ' ')
                logger.info(f"   🤖 Requête réécrite : '{search_query}'")
            except Exception:
                pass

        # Recherche Vectorielle
        from repositories.doc import doc_repository
        doc_ids = doc_repository.get_filtered_doc_ids(self.employee, tags)
        
        if not doc_ids:
            return []

        results = chunk_repository.search(
            query=search_query,
            employee=self.employee,
            limit=limit, # <--- Paramètre dynamique ici
            doc_ids_filter=doc_ids
        )

        candidates = []
        if results and results['documents']:
            docs = results['documents'][0] if results['documents'] else []
            ids = results['ids'][0] if results['ids'] else []
            metas = results['metadatas'][0] if results['metadatas'] else []
            dists = results['distances'][0] if 'distances' in results else [0.0]*len(ids)

            for i, content in enumerate(docs):
                meta = metas[i]
                if exclude.get('sources') and meta.get('source') in exclude['sources']: continue
                
                dist = dists[i]
                sim_score = 1 / (1 + dist) if dist is not None else 0.5

                candidates.append({
                    "content": content,
                    "metadata": meta,
                    "id": ids[i],
                    "vector_score": sim_score 
                })
        
        return candidates

    def rerank_chunks(self, question: str, chunks: List[dict], top_k: int = 10) -> List[dict]:
        """
        Reranking par lots (Batching).
        Paramètre top_k ajouté pour contrôler la sévérité du filtrage.
        """
        if not chunks:
            return []

        # On ne rerank que les N premiers candidats vectoriels pour aller vite
        # (Si on a demandé 50 candidats vectoriels, on n'en rerank que 20 par exemple pour gagner du temps)
        candidates_to_process = chunks[:20] 
        
        prompt_doc = prompt_repository.get_by_name("agent_rerank")
        if not prompt_doc:
            return candidates_to_process[:top_k]

        BATCH_SIZE = 5
        scored_chunks = []
        
        num_batches = math.ceil(len(candidates_to_process) / BATCH_SIZE)
        
        logger.info(f"⚖️ [Tool] Reranking de {len(candidates_to_process)} chunks ({num_batches} batches)...")

        for i in range(num_batches):
            start = i * BATCH_SIZE
            end = start + BATCH_SIZE
            batch = candidates_to_process[start:end]
            
            context_text = ""
            for idx, c in enumerate(batch):
                preview = c['content'][:800].replace("\n", " ") 
                context_text += f"--- Chunk {idx} ---\n{preview}\n\n"

            final_prompt = prompt_doc.prompt.replace("{question}", question).replace("{context}", context_text)

            try:
                llm_response = llm_service.generate_response(
                    system_prompt="Tu es un système de scoring JSON. Réponds UNIQUEMENT avec un tableau JSON strict.",
                    user_input=final_prompt
                )
                scores_data = robust_json_parse(llm_response)
                if isinstance(scores_data, dict): scores_data = [scores_data]
                
                if isinstance(scores_data, list):
                    for item in scores_data:
                        local_idx = item.get("chunk_index")
                        score = item.get("score", 0.0)
                        if local_idx is not None and isinstance(local_idx, int) and 0 <= local_idx < len(batch):
                            real_chunk = batch[local_idx]
                            real_chunk["score"] = score
                            if score >= 0.4: # Seuil un peu plus bas pour ne pas trop jeter
                                scored_chunks.append(real_chunk)
            except Exception:
                continue

        # Tri final
        scored_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # On coupe selon la demande (Global = 30, Specific = 5)
        final_selection = scored_chunks[:top_k]
        
        if not final_selection and chunks:
            return chunks[:3]

        return final_selection