import os
import shutil

# --- NOUVEAUX IMPORTS OFFICIELS (Plus d'erreur rouge) ---
from langchain_ollama import OllamaLLM, OllamaEmbeddings 
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- CONFIGURATION ---
MODEL_LLM = "llama3.2"       # Assurez-vous d'avoir fait: ollama pull qwen2.5:3b
MODEL_EMBEDDING = "nomic-embed-text" 
DB_PATH = "./chroma_db_data"

def main():
    print(f"--- 1. Initialisation ({MODEL_LLM}) ---")
    
    # On utilise OllamaLLM au lieu de Ollama (nouvelle norme)
    llm = OllamaLLM(model=MODEL_LLM)
    embeddings = OllamaEmbeddings(model=MODEL_EMBEDDING)

    print("--- 2. Création des données ---")
    docs = [Document(page_content="Le code secret du coffre est 1234. Le mot de passe admin est 'Admin123!'.")]

    print("--- 3. Indexation Vectorielle ---")
    # Nettoyage préalable
    if os.path.exists(DB_PATH):
        try: shutil.rmtree(DB_PATH)
        except: pass

    # Création de la base
    vectorstore = Chroma.from_documents(
        documents=docs, 
        embedding=embeddings, 
        persist_directory=DB_PATH
    )
    retriever = vectorstore.as_retriever()

    print("--- 4. Question ---")
    
    # Construction du Prompt
    template = """Réponds uniquement basé sur ce contexte:
    {context}
    
    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    # Chaîne RAG
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Lancement
    response = rag_chain.invoke("Quel est le mot de passe admin ?")
    
    print("\n🤖 Réponse :")
    print(response)

if __name__ == "__main__":
    main()