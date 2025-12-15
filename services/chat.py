import logging
from repositories.chunk import chunk_repository
from repositories.doc import doc_repository
from services.llm import llm_service
from schemas.chat import ChatRequestLegacy

logger = logging.getLogger(__name__)

class ChatService:
    def chat(self, question: str, employee: str, tags: list[str] = None):
        """Chat standard (API Python simple)"""
        logger.info(f"💬 [Chat] Question: '{question}' (User: {employee})")

        results = chunk_repository.search(question, employee, limit=7)
        
        retrieved_texts = []
        sources = []

        if results['documents']:
            for i, doc_text in enumerate(results['documents'][0]):
                retrieved_texts.append(doc_text)
                meta = results['metadatas'][0][i]
                sources.append(meta.get('doc', 'unknown'))

        context_block = "\n\n---\n\n".join(retrieved_texts)

        if not context_block:
            logger.warning("⚠️ [Chat] Aucun contexte trouvé.")
            return {
                "response": "Je n'ai trouvé aucun document correspondant dans la base de connaissances.",
                "sources": []
            }

        system_prompt = """
        Tu es un assistant intelligent de l'entreprise.
        Réponds à la question de l'utilisateur en t'aidant du CONTEXTE fourni.
        Si tu ne sais pas, dis-le.
        Réponds toujours en Français.
        """

        answer = llm_service.generate_response(
            system_prompt=system_prompt,
            user_input=question,
            context=context_block
        )

        return {
            "response": answer,
            "sources": list(set(sources))
        }
    
    def handle_legacy_chat(self, request: ChatRequestLegacy) -> dict:
        """
        Gère le flux Node.js : Filtre Tags/Exclusion -> Recherche -> LLM -> Retour Sources+Scores
        """
        logger.info(f"💬 [Legacy Chat] Question: '{request.question}' (User: {request.employee})")
        
        # 1. Gestion exclusion
        exclude_ids = []
        if request.exclude:
            if isinstance(request.exclude, dict):
                exclude_ids = [k for k, v in request.exclude.items() if v is True]
            elif isinstance(request.exclude, list):
                exclude_ids = request.exclude

        # 2. Récupération des IDs éligibles
        target_doc_ids = doc_repository.get_filtered_doc_ids(
            employee=request.employee,
            tags=request.tags,
            exclude_ids=exclude_ids
        )
        
        logger.info(f"🔍 [Filtre] Cibles={len(target_doc_ids)} docs éligibles")

        # 3. Recherche Vectorielle
        results = chunk_repository.search(
            query=request.question,
            employee=request.employee,
            limit=7, 
            doc_ids_filter=target_doc_ids
        )
        
        retrieved_texts = []
        sources_map = {} # Pour stocker le meilleur score par document

        if results['documents'] and len(results['documents'][0]) > 0:
            for i, doc_text in enumerate(results['documents'][0]):
                retrieved_texts.append(doc_text)
                
                # Métadonnées
                meta = results['metadatas'][0][i]
                doc_name = meta.get('doc', 'unknown')
                
                # Score (Distance Chroma -> Similitude approximative)
                # Chroma renvoie souvent une L2 distance ou Cosine distance.
                # On calcule une "confiance" basique : 1 - distance (si < 1)
                distance = 0.0
                if 'distances' in results and results['distances']:
                     distance = results['distances'][0][i]
                
                score = round(1 - distance, 3) 
                
                # On garde le meilleur score pour ce document
                if doc_name not in sources_map:
                    sources_map[doc_name] = score
                else:
                    if score > sources_map[doc_name]:
                        sources_map[doc_name] = score

        # 4. Construction Contexte
        context_block = "\n\n---\n\n".join(retrieved_texts)
        
        # Formatage des sources pour le front (Liste d'objets avec score)
        unique_sources = [
            {"name": doc, "score": score} 
            for doc, score in sources_map.items()
        ]
        # Tri par score décroissant
        unique_sources.sort(key=lambda x: x["score"], reverse=True)

        if not context_block:
            msg = "Je n'ai trouvé aucune information pertinente dans les documents sélectionnés."
            if not target_doc_ids:
                msg = "Aucun document ne correspond à vos filtres (tags/exclusion)."
            
            return {
                "response": msg,
                "sources": []
            }

        # 5. Génération LLM
        system_prompt = """
        Tu es un assistant IA professionnel.
        Réponds à la question en utilisant EXCLUSIVEMENT le CONTEXTE fourni.
        
        Règles :
        1. Si la réponse est dans le contexte, donne-la.
        2. Si le contexte ne suffit pas, dis-le poliment.
        3. Ne jamais inventer d'information hors du contexte.
        4. Réponds en Français.
        """

        answer = llm_service.generate_response(
            system_prompt=system_prompt,
            user_input=request.question,
            context=context_block
        )

        return {
            "response": answer,
            "sources": unique_sources
        }

chat_service = ChatService()