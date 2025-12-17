from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

logger = logging.getLogger(__name__)

class LLMService:
    
    # Configuration des capacités (Tokens -> Char approx)
    # 1 token ~= 4 caractères. On garde une marge de sécurité de 20% pour le prompt système et la réponse.
    # Ex: Llama 3.2 supporte 128k tokens, mais en local sur Ollama par défaut c'est souvent 2k, 4k ou 8k selon la RAM.
    # Ici on définit des valeurs "safe" pour une machine standard (16/32GB RAM).
    MODEL_CAPABILITIES = {
        "llama3.2": 32000,      # ~8k tokens
        "llama3.2:1b": 16000,   # ~4k tokens (Version légère)
        "mistral": 16000,       # ~4k tokens
        "gemma": 8000,          # ~2k tokens
        "deepseek-r1": 64000    # ~16k tokens
    }
    
    # Valeur par défaut si modèle inconnu
    DEFAULT_LIMIT = 8000 

    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.llm = ChatOllama(model=model_name, temperature=0)
        
        # Définition dynamique de la limite au démarrage
        self.context_char_limit = self.MODEL_CAPABILITIES.get(model_name, self.DEFAULT_LIMIT)
        logger.info(f"🧠 [LLM] Modèle '{model_name}' chargé. Limite contexte : {self.context_char_limit} chars.")

    def get_context_limit(self) -> int:
        """Retourne la limite de caractères sécurisée pour le contexte."""
        return self.context_char_limit

    def generate_response(self, system_prompt: str, user_input: str, context: str = "") -> str:
        """
        Génère une réponse simple basée sur un prompt système et une entrée utilisateur.
        """
        prompt = ChatPromptTemplate.from_template("""
        {system_instruction}
        
        CONTEXTE (Si fourni) :
        {context}
        
        QUESTION : {input}
        """)

        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "system_instruction": system_prompt,
            "context": context,
            "input": user_input
        })

# Instance par défaut
llm_service = LLMService()