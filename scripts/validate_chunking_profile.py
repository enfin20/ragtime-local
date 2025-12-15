import sys
import os
import time
import logging

# Config logs
logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from services.ingestion import ingestion_service
from services.chat import chat_service

def run_profile_test():
    print("🚀 Démarrage Test Chunking (Profil Structuré)...")
    Base.metadata.create_all(bind=engine)
    
    employee_id = "recruiter_bob"
    
    # 1. Donnée structurée (Comme si elle venait d'un scraping LinkedIn)
    fake_profile = {
        "name": "Alice Wonderland",
        "about": "Experte en Data Science passionnée par les lapins blancs.",
        "experience": [
            {
                "title": "Lead Data Scientist",
                "company": "Wonder Corp",
                "date_range": "2020 - Present",
                "description": "Gestion de l'équipe IA, déploiement de modèles LLM."
            },
            {
                "title": "Junior Analyst",
                "company": "Rabbit Hole Inc",
                "date_range": "2018 - 2020",
                "description": "Analyse de données temporelles."
            }
        ],
        "education": [
            {
                "school": "University of Hearts",
                "degree": "Master in Magic"
            }
        ]
    }

    # 2. Ingestion (on passe le dict direct)
    print("\n--- [1] Ingestion du Profil JSON ---")
    result = ingestion_service.process_input(
        input_data=fake_profile,
        employee=employee_id,
        tags=["candidat", "data"],
        origin="api_push"
    )
    
    print(f"✅ Ingestion terminée.")
    print(f"   Stratégie utilisée : {result['strategy']}")
    print(f"   Chunks créés : {result['chunks_count']}")
    
    # On attend 3 chunks logiques : 1 About + 2 Experiences + 1 Education = 4 chunks
    # (Ou 3 si about est petit)
    
    time.sleep(1)

    # 3. Chat (Vérification RAG)
    print("\n--- [2] Question sur le CV ---")
    # On pose une question précise sur une expérience
    question = "Qu'a fait Alice chez Rabbit Hole Inc ?"
    
    answer = chat_service.chat(question, employee_id)
    
    print(f"🤖 Réponse IA :\n{answer['response']}")
    print(f"📚 Sources : {answer['sources']}")

if __name__ == "__main__":
    run_profile_test()