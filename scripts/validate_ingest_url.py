import sys
import os
import time
import logging # <--- Import nécessaire

# Configuration des logs pour voir ce que dit Tavily
logging.basicConfig(level=logging.INFO)

# Ajout du dossier parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from services.ingestion import ingestion_service
from services.chat import chat_service

def run_url_test():
    print("🚀 Démarrage Test Ingestion URL (Tavily)...")
    
    # Init DB
    Base.metadata.create_all(bind=engine)

    employee_id = "web_tester"
    
    # URL de test : On utilise Wikipédia pour valider la connexion API (plus fiable que TDS)
    target_url = "https://fr.wikipedia.org/wiki/Intelligence_artificielle" 

    print(f"\n--- [1] Tentative d'ingestion de : {target_url} ---")
    try:
        # On appelle la nouvelle méthode unifiée 'process_input'
        result = ingestion_service.process_input(
            input_data=target_url,
            employee=employee_id,
            tags=["ia", "wiki", "web"],
            origin="test_script"
        )
        print(f"✅ Ingestion Web réussie !")
        print(f"   Source : {result['source']}")
        print(f"   Chunks : {result['chunks_count']}")
        
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        # On ne quitte pas, on veut voir les logs au dessus
        return

    # Pause pour l'indexation Chroma
    time.sleep(2)

    print("\n--- [2] Vérification RAG sur le contenu Web ---")
    question = "C'est quoi l'intelligence artificielle ?"
    
    answer = chat_service.chat(question, employee_id)
    
    print(f"🤖 Réponse IA :\n{answer['response']}")
    print(f"📚 Sources : {answer['sources']}")

if __name__ == "__main__":
    run_url_test()