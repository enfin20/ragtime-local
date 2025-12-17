import logging
from typing import List, Tuple

from repositories.prompt import prompt_repository
from services.llm import llm_service
from schemas.chat import ChatRequestNode
# Assurez-vous d'avoir bien ajouté SearchStrategy dans services/agent_tools.py comme vu précédemment
from services.agent_tools import AgentToolExecutor, SearchStrategy 

logger = logging.getLogger(__name__)

class ChatService:
    
    def handle_node_chat(self, request: ChatRequestNode) -> dict:
        """
        Point d'entrée principal du Chat.
        Dispatche vers le workflow Expert (avec Prompt) ou Standard.
        """
        logger.info(f"🚀 [CHAT] Demande reçue: Prompt='{request.prompt}' | Q='{request.question}'")

        tools = AgentToolExecutor(request.employee)
        
        # Gestion des exclusions (Toujours exclure les archives par défaut)
        exclude = request.exclude if isinstance(request.exclude, dict) else {}
        if "archive" not in exclude.get("categories", []):
            exclude.setdefault("categories", []).append("archive")

        # Sélection du workflow
        if request.prompt:
            return self._handle_expert_workflow(request, tools, exclude)
        
        return self._handle_standard_workflow(request, tools, exclude)

    def _build_dynamic_context(self, ranked_chunks: List[dict], sort_by: str = "index", max_chunks: int = 0) -> Tuple[str, List[dict]]:
        """
        Construit la chaîne de contexte (String) à partir des chunks bruts.
        
        Args:
            ranked_chunks: Liste des chunks (déjà triés par score/pertinence par smart_retrieve).
            sort_by: 'index' (pour lecture narrative) ou 'score' (pour pertinence pure).
            max_chunks: Limite optionnelle en nombre de chunks (ex: 5 pour du fact-checking).
        """
        selected_chunks = []
        current_chars = 0
        
        # 1. Récupération de la limite technique du modèle chargé
        max_chars_limit = llm_service.get_context_limit()
        
        # 2. Application de la limite numérique (si demandée)
        candidates = ranked_chunks
        if max_chunks > 0:
            candidates = ranked_chunks[:max_chunks]
        
        # 3. Remplissage intelligent (Context Stuffing)
        # On prend les chunks dans l'ordre de pertinence (candidates est trié par score)
        # tant qu'il y a de la place en mémoire.
        for chunk in candidates:
            content_len = len(chunk['content'])
            
            # Vérification de l'espace disponible (avec marge de sécurité)
            if current_chars + content_len < max_chars_limit:
                selected_chunks.append(chunk)
                current_chars += content_len
            else:
                logger.info(f"🛑 Limite contexte atteinte ({current_chars}/{max_chars_limit} chars). Arrêt.")
                break
        
        if not selected_chunks:
            return "", []

        # 4. Tri Final pour la consommation par le LLM
        if sort_by == "index":
            # Mode NARRATIF (Global) : On remet dans l'ordre du document (Page 1 -> Page 10)
            # C'est crucial pour que le LLM comprenne la structure.
            selected_chunks.sort(key=lambda x: x['metadata'].get('chunk_index', 0))
        else:
            # Mode PERTINENCE (Specific) : On garde les meilleurs scores en premier
            # Utile pour que le LLM voit la réponse la plus probable tout de suite.
            selected_chunks.sort(key=lambda x: x.get('score', 0), reverse=True)

        logger.info(f"📚 Contexte final construit : {len(selected_chunks)} chunks (~{current_chars} chars) | Tri: {sort_by}")

        # 5. Assemblage de la string
        context_str = "\n\n".join([
            f"--- Source: {c['metadata'].get('doc')} (Index: {c['metadata'].get('chunk_index', '?')}, Score: {c.get('score', 0):.2f}) ---\n{c['content']}" 
            for c in selected_chunks
        ])
        
        return context_str, selected_chunks

    def _handle_expert_workflow(self, request: ChatRequestNode, tools: AgentToolExecutor, exclude: dict) -> dict:
        logger.info("🧠 [Workflow] Démarrage mode EXPERT")

        # A. Chargement du Prompt Système
        prompt_doc = prompt_repository.get_by_name(request.prompt)
        if not prompt_doc:
            return {"response": f"Erreur: Prompt '{request.prompt}' introuvable.", "sources": []}

        target_input = request.question if request.question and request.question.strip() else "Analyse globale"
        
        # B. Récupération Intelligente (Router -> Search -> Rerank)
        retrieval_result = tools.smart_retrieve(target_input, request.tags, exclude)
        chunks = retrieval_result["chunks"]
        strategy = retrieval_result["strategy"]

        # C. Construction du Contexte Adaptative
        context_str = ""
        final_selection = []

        if strategy == SearchStrategy.GLOBAL:
            # Stratégie Résumé : On prend le max de chunks, triés par Index (lecture livre)
            context_str, final_selection = self._build_dynamic_context(chunks, sort_by="index")
        else:
            # Stratégie Précision : On prend max 5 chunks, triés par Score
            context_str, final_selection = self._build_dynamic_context(chunks, sort_by="score", max_chunks=5)

        # D. Assemblage du Prompt Final
        system_msg = prompt_doc.prompt
        user_msg_content = f"""
        Voici les données contextuelles récupérées (Mode: {strategy.value}) :
        
        CONTEXTE:
        {context_str}
        
        INSTRUCTION:
        En utilisant ces données, exécute la tâche demandée.
        """
        
        if not final_selection:
            user_msg_content = f"Aucune donnée pertinente trouvée pour '{target_input}'. Fais de ton mieux avec tes connaissances générales."

        # Historique (si présent)
        history_block = ""
        if request.history:
            history_block = "HISTORIQUE:\n" + "\n".join(
                [f"{m.get('role','').upper()}: {m.get('content','')}" for m in request.history]
            ) + "\n\n"

        full_prompt = f"{system_msg}\n\n{history_block}USER TASK:\n{user_msg_content}"
        
        # E. Génération
        try:
            response = llm_service.generate_response(
                system_prompt="Tu es un expert qualifié.",
                user_input=full_prompt
            )
        except Exception as e:
            logger.error(f"❌ Erreur génération : {e}")
            return {"response": "Désolé, une erreur technique est survenue lors de la génération.", "sources": []}

        # Formatage des sources pour le frontend
        unique_sources = {c['metadata'].get('doc'): c for c in final_selection}.values()
        sources_list = [{"name": c['metadata'].get('doc'), "score": c.get("score")} for c in unique_sources]

        return {"response": response, "sources": sources_list}

    def _handle_standard_workflow(self, request: ChatRequestNode, tools: AgentToolExecutor, exclude: dict) -> dict:
        """
        Workflow Chat standard (sans prompt expert prédéfini).
        """
        query = request.question if request.question.strip() else "Résumé"
        
        # A. Récupération Intelligente
        retrieval_result = tools.smart_retrieve(query, request.tags, exclude)
        chunks = retrieval_result["chunks"]
        strategy = retrieval_result["strategy"]
        
        # B. Contexte Adaptatif
        if strategy == SearchStrategy.GLOBAL:
            context_str, final_selection = self._build_dynamic_context(chunks, sort_by="index")
        else:
            context_str, final_selection = self._build_dynamic_context(chunks, sort_by="score", max_chunks=5)
        
        # C. Génération
        answer = llm_service.generate_response(
            system_prompt="Tu es un assistant utile et précis. Réponds en français en te basant sur le contexte fourni.",
            user_input=query,
            context=context_str
        )
        
        unique_sources = {c['metadata'].get('doc'): c for c in final_selection}.values()
        sources_list = [{"name": c['metadata'].get('doc'), "score": c.get("score")} for c in unique_sources]
        
        return {"response": answer, "sources": sources_list}

chat_service = ChatService()