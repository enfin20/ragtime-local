import logging
from repositories.prompt import prompt_repository
from services.llm import llm_service
from schemas.chat import ChatRequestNode
from services.agent_tools import AgentToolExecutor

logger = logging.getLogger(__name__)

class ChatService:
    
    def handle_node_chat(self, request: ChatRequestNode) -> dict:
        logger.info(f"🚀 [CHAT] Demande reçue: Prompt='{request.prompt}' | Q='{request.question}'")

        # 1. Initialisation des outils
        tools = AgentToolExecutor(request.employee)
        
        # 2. Gestion Exclusion (Standard)
        exclude = request.exclude if isinstance(request.exclude, dict) else {}
        if "archive" not in exclude.get("categories", []):
            exclude.setdefault("categories", []).append("archive")

        # ==========================================================
        # BRANCHE 1 : WORKFLOW EXPERT (Prompt défini)
        # Logique: Search -> Rerank -> Inject -> Execute Prompt
        # ==========================================================
        if request.prompt:
            return self._handle_expert_workflow(request, tools, exclude)

        # ==========================================================
        # BRANCHE 2 : WORKFLOW STANDARD (Chat Agentique)
        # ==========================================================
        return self._handle_standard_workflow(request, tools, exclude)

    def _handle_expert_workflow(self, request: ChatRequestNode, tools: AgentToolExecutor, exclude: dict) -> dict:
        logger.info("🧠 [Workflow] Démarrage mode EXPERT (Data-First)")

        # A. Récupération du Prompt Expert
        prompt_doc = prompt_repository.get_by_name(request.prompt)
        if not prompt_doc:
            return {"response": f"Erreur: Prompt '{request.prompt}' introuvable.", "sources": []}

        # B. Définition de la cible (Target Input)
        # Node: const targetInput = question ... ? question : "Analyse globale..."
        target_input = request.question if request.question and request.question.strip() else "Analyse globale du contenu principal"
        
        # C. ÉTAPE 1 : Exploratory Search (Vectorielle pure)
        raw_candidates = tools.exploratory_search(target_input, request.tags, exclude)
        
        # D. ÉTAPE 2 : Reranking Intelligent (LLM)
        # C'est ici que la magie opère : le LLM décide si "Article IA" correspond à "Analyse globale"
        relevant_chunks = tools.rerank_chunks(target_input, raw_candidates)

        # E. Construction du Contexte pour le Prompt
        context_str = ""
        sources_list = []
        
        if relevant_chunks:
            context_str = "\n\n".join([
                f"--- Document {i+1} (Source: {c['metadata'].get('doc')}) ---\n{c['content']}" 
                for i, c in enumerate(relevant_chunks)
            ])
            # Formatage des sources pour la réponse API
            seen_docs = set()
            for c in relevant_chunks:
                doc_name = c['metadata'].get('doc', 'inconnu')
                if doc_name not in seen_docs:
                    sources_list.append({"name": doc_name, "score": c.get("score", 1.0)})
                    seen_docs.add(doc_name)
        else:
            logger.warning("⚠️ [Expert] Aucun chunk pertinent après Reranking.")

        # F. Construction du Message Final (Prompt Engineering)
        # Structure Node.js :
        # 1. System Prompt (Le prompt expert chargé)
        # 2. User Message : "Voici les données... CONTEXTE... INSTRUCTION..."
        
        system_msg = prompt_doc.prompt
        
        user_msg_content = f"""
        Voici les données contextuelles récupérées concernant "{target_input}".
        
        CONTEXTE:
        {context_str}
        
        INSTRUCTION:
        Exécute maintenant ta mission d'expert en utilisant ces données.
        """
        
        if not relevant_chunks:
            user_msg_content = f"Aucune donnée spécifique trouvée pour '{target_input}'. Fais de ton mieux."

        # G. Appel final LLM
        # On concatène l'historique si présent
        history_block = ""
        if request.history:
            history_block = "HISTORIQUE DE CONVERSATION:\n" + "\n".join(
                [f"{m.get('role','').upper()}: {m.get('content','')}" for m in request.history]
            ) + "\n\n"

        # Note: On triche un peu en mettant tout dans le user_input pour simplifier l'appel à llm_service
        # mais on respecte la structure logique.
        full_prompt = f"{system_msg}\n\n{history_block}\nUSER TASK:\n{user_msg_content}"

        response = llm_service.generate_response(
            system_prompt="Tu es un expert qualifié.",
            user_input=full_prompt
        )

        return {
            "response": response,
            "sources": sources_list
        }

    def _handle_standard_workflow(self, request: ChatRequestNode, tools: AgentToolExecutor, exclude: dict) -> dict:
        # Implémentation simplifiée du chat standard utilisant aussi le reranking
        query = request.question if request.question.strip() else "Résumé"
        
        raw = tools.exploratory_search(query, request.tags, exclude)
        refined = tools.rerank_chunks(query, raw)
        
        context_str = "\n".join([c['content'] for c in refined])
        
        answer = llm_service.generate_response(
            system_prompt="Tu es un assistant utile. Réponds en français.",
            user_input=query,
            context=context_str
        )
        
        sources = [{"name": c['metadata'].get('doc'), "score": c.get("score")} for c in refined]
        
        return {"response": answer, "sources": sources}

chat_service = ChatService()