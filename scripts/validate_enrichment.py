import sys
import os
import logging
import json

# Config logs
logging.basicConfig(level=logging.INFO)

# Ajout du dossier parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CORRECTION ICI : On importe engine et Base au lieu de init_db
from database.connection import engine
from database.models import Base
from services.chunking.enrichment import enrichment_service

def run_enrichment_test():
    print("🚀 Démarrage Test Enrichissement LLM...")
    
    # CORRECTION ICI : Initialisation explicite via SQLAlchemy
    Base.metadata.create_all(bind=engine)

    # 1. Texte "About" type LinkedIn
    about_text = """
    Développeur Full Stack avec 5 ans d'expérience. 
    Expert en Python, FastAPI et React. 
    J'ai géré des projets cloud sur AWS et Azure. 
    Je suis reconnu pour ma capacité à résoudre des problèmes complexes et mon esprit d'équipe.
    Certifié AWS Solutions Architect.
    """

    print(f"\n--- Texte à analyser ---\n{about_text.strip()}\n")

    # 2. Appel du service (utilise le prompt 'chunk_about' en base)
    try:
        print("⏳ Appel au LLM (Ollama) via EnrichmentService...")
        metadata = enrichment_service.extract_metadata(about_text, "chunk_about")
        
        print("\n✅ Résultat Structuré (JSON) :")
        print("-" * 30)
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print("-" * 30)

        # Vérifications
        if metadata and ("hard_skills" in metadata or "technologies" in metadata):
            print("🎉 SUCCÈS : Des compétences ont été extraites !")
        else:
            print("⚠️ AVERTISSEMENT : Le JSON est valide mais vide. Vérifiez que le prompt 'chunk_about' est bien en base (seed_prompts.py).")

    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    run_enrichment_test()