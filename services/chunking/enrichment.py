import logging
from repositories.prompt import prompt_repository
from services.llm import llm_service
from utils.json_parser import robust_json_parse

logger = logging.getLogger(__name__)

class EnrichmentService:
    
    def extract_metadata(self, text: str, prompt_name: str) -> dict:
        """
        Pour les prompts génériques (Profil, Post, Synthèse...) qui agissent comme une instruction Système.
        """
        prompt_doc = prompt_repository.get_by_name(prompt_name)
        if not prompt_doc:
            logger.warning(f"⚠️ Prompt '{prompt_name}' introuvable.")
            return {}

        if not text or len(text) < 10:
            return {}

        logger.info(f"🧠 [Enrichment] JSON Prompt '{prompt_name}'...")
        
        # Cas standard : Le prompt en base est le System Prompt
        raw_response = llm_service.generate_response(
            system_prompt=prompt_doc.prompt,
            user_input=f"Analyse ce texte :\n\n{text}",
        )

        return robust_json_parse(raw_response) or {}

    def generate_hypothetical_questions(self, text: str) -> str:
        """ Reverse HyDE (Questions) """
        prompt_name = "chunk_hypothetical_questions"
        prompt_doc = prompt_repository.get_by_name(prompt_name)
        
        if not prompt_doc:
            return ""

        formatted_prompt = prompt_doc.prompt.replace("${text}", text) # Syntaxe JS du prompt

        response = llm_service.generate_response(
            system_prompt="Tu es un expert en génération de questions.",
            user_input=formatted_prompt
        )
        return response.strip()

    def extract_entities(self, text: str) -> dict:
        """
        Spécifique pour 'chunk_entities' qui extrait People, Companies, Tools...
        """
        prompt_name = "chunk_entities"
        prompt_doc = prompt_repository.get_by_name(prompt_name)
        
        if not prompt_doc:
            logger.warning(f"⚠️ Prompt '{prompt_name}' introuvable.")
            return {}

        if len(text) < 50:
            return {}

        logger.info(f"🧠 [Enrichment] Extracting Entities (~{len(text)} chars)...")

        # Le prompt contient "{text}", on le remplace
        # Note : On utilise .replace() simple pour être sûr
        formatted_prompt = prompt_doc.prompt.replace("{text}", text)

        raw_response = llm_service.generate_response(
            system_prompt="Tu es un expert en extraction d'entités nommées (NER).",
            user_input=formatted_prompt
        )
        
        return robust_json_parse(raw_response) or {}

enrichment_service = EnrichmentService()