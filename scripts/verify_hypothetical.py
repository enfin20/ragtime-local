import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from services.ingestion import ingestion_service
from repositories.chunk import chunk_repository

def run_test():
    print("🚀 Test: Chunking avec Questions Hypothétiques...")
    Base.metadata.create_all(bind=engine)
    
    # Texte court mais factuel, propice aux questions
    text = """
    La tour Eiffel est une tour de fer puddlé de 330 m de hauteur située à Paris.
    Construite par Gustave Eiffel pour l'Exposition universelle de Paris de 1889.
    Elle a accueilli plus de 300 millions de visiteurs depuis son ouverture.
    """
    
    doc_id = "test_eiffel_questions"
    employee_id = "tester_hyde"

    # Ingestion
    ingestion_service.process_input(
        input_data=text,
        employee=employee_id,
        tags=["monument", "paris"],
        origin="test_script"
    )

    # Vérification
    print("\n🔍 Vérification du contenu du chunk...")
    # On récupère le dernier chunk inséré pour ce doc
    results = chunk_repository.search("tour eiffel", employee_id, limit=1)
    
    if results['documents'] and results['documents'][0]:
        content = results['documents'][0][0]
        print("-" * 40)
        print(content)
        print("-" * 40)
        
        if "--- Questions Potentielles ---" in content:
            print("✅ SUCCÈS : Les questions ont été générées et ajoutées !")
        else:
            print("❌ ÉCHEC : Pas de questions trouvées dans le texte.")
    else:
        print("❌ Erreur : Chunk introuvable.")

if __name__ == "__main__":
    run_test()