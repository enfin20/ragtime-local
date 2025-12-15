import sys
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from services.ingestion import ingestion_service
from repositories.chunk import chunk_repository

def run_entity_test():
    print("🚀 Test: Extraction d'Entités (NER)...")
    Base.metadata.create_all(bind=engine)
    
    # Texte riche en entités
    text = """
    Hier, Satya Nadella, le CEO de Microsoft, a annoncé un partenariat avec Mistral AI.
    L'accord a été signé à Paris en présence de Brad Smith.
    Ils vont intégrer leurs modèles dans Azure AI Studio pour concurrencer Google.
    """
    
    doc_id = "test_ner_microsoft"
    employee_id = "tester_ner"

    print(f"\n--- Texte ---\n{text.strip()}\n")

    # Ingestion
    ingestion_service.process_input(
        input_data=text,
        employee=employee_id,
        tags=["tech", "ia"],
        origin="test_ner"
    )

    # Vérification
    print("\n🔍 Vérification des métadonnées du chunk...")
    results = chunk_repository.search("Microsoft", employee_id, limit=1)
    
    if results['metadatas'] and len(results['metadatas'][0]) > 0:
        meta = results['metadatas'][0][0]
        
        print("\n📊 Métadonnées trouvées :")
        print(json.dumps(meta, indent=2))
        
        # Tests
        has_people = "Satya Nadella" in meta.get("entities_people", "")
        has_company = "Microsoft" in meta.get("entities_companies", "")
        has_location = "Paris" in meta.get("entities_locations", "")

        if has_people and has_company:
            print("\n✅ SUCCÈS : Entités 'Satya Nadella' et 'Microsoft' détectées !")
        else:
            print("\n⚠️ AVERTISSEMENT : Certaines entités manquent.")
    else:
        print("❌ Erreur : Chunk introuvable.")

if __name__ == "__main__":
    run_entity_test()