import sys
import os
import time

# Path hack
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from services.ingestion import ingestion_service
from services.chat import chat_service
from repositories.doc import doc_repository

def run_validation():
    print("🚀 Démarrage Validation Étape 3 (Services)...")
    
    # 1. Initialisation de la DB (Correction ici : on utilise engine direct)
    Base.metadata.create_all(bind=engine)
    print("✅ DB Initialisée.")

    employee_id = "tester@local.com"
    doc_name = "procedure_securite.txt"
    
    # 2. Texte de test (Contenu métier)
    content = """
    PROCÉDURE DE SÉCURITÉ - CODE ROUGE
    1. En cas d'incendie, ne prenez pas l'ascenseur.
    2. Le point de rassemblement est le Parking Sud, Zone B.
    3. Le code du coffre-fort des serveurs est 'K9-Alpha-77'.
    4. Le responsable de la sécurité est Mme Martin (poste 404).
    """

    # 3. Test Ingestion
    print(f"\n--- [1] Ingestion du document : {doc_name} ---")
    try:
        result = ingestion_service.process_text_document(
            doc_id=doc_name,
            text_content=content,
            employee=employee_id,
            tags=["sécurité", "interne"],
            origin="upload"
        )
        print(f"✅ Ingestion terminée. Chunks créés : {result['chunks_count']}")
    except Exception as e:
        print(f"❌ Erreur Ingestion: {e}")
        return
    
    # Vérification du statut en base
    doc_in_db = doc_repository.get_doc(doc_name, employee_id)
    if doc_in_db:
        print(f"   Statut en DB : {doc_in_db.status}")
    else:
        print("❌ Erreur: Document non trouvé en base SQLite après ingestion.")

    # Petite pause pour laisser Chroma indexer
    time.sleep(1)

    # 4. Test Chat (RAG)
    print("\n--- [2] Test du Chat RAG ---")
    question = "Quel est le code du coffre et où est le point de rassemblement ?"
    print(f"❓ Question : {question}")
    
    try:
        chat_result = chat_service.chat(question, employee_id)
        
        print("\n🤖 Réponse de l'IA :")
        print("-" * 40)
        print(chat_result['response'])
        print("-" * 40)
        print(f"📚 Sources utilisées : {chat_result['sources']}")

        # Validation simple du contenu
        if "K9-Alpha-77" in chat_result['response'] or "Parking Sud" in chat_result['response']:
            print("\n🎉 ÉTAPE 3 VALIDÉE : Le RAG complet fonctionne !")
        else:
            print("\n⚠️ ATTENTION : L'IA n'a pas donné la réponse attendue. Vérifiez que Ollama tourne bien.")
            
    except Exception as e:
        print(f"❌ Erreur Chat: {e}")

if __name__ == "__main__":
    run_validation()