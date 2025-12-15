from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class LLMService:
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.llm = ChatOllama(model=model_name, temperature=0)

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

# Instance par défaut (facile à importer)
llm_service = LLMService()