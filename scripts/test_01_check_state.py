import sys
import os
import requests
from sqlalchemy.orm import Session

# Ajout du dossier parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, get_chroma_client
from database.models import PromptModel, LoginModel, DocModel

# Liste des prompts critiques pour que le RAG fonctionne
REQUIRED_PROMPTS = ["synthesis_tags", "chunk_hypothetical_questions", "chunk_entities", "graph_extraction"]

def check_system_state():
    print("🔍 [DIAGNOSTIC] Vérification de l'état du système...\n")
    
    with Session(engine) as db:
        # 1. Vérification des Prompts (CRITIQUE)
        print("1️⃣  Vérification des Prompts...")
        existing_prompts = [p.name for p in db.query(PromptModel).all()]
        missing = [p for p in REQUIRED_PROMPTS if p not in existing_prompts]
        
        if missing:
            print(f"   ❌ ALERTE : Il manque ces prompts critiques : {missing}")
            print("      -> Lancez 'python scripts/seed_prompts.py' si vous les avez perdus.")
        else:
            print(f"   ✅ {len(existing_prompts)} prompts trouvés (dont les {len(REQUIRED_PROMPTS)} critiques).")

        # 2. Vérification des Docs (Doit être vide ou presque)
        count_docs = db.query(DocModel).count()
        print(f"\n2️⃣  Vérification des Documents : {count_docs} documents en base SQLite.")

    # 3. Vérification ChromaDB
    print("\n3️⃣  Vérification ChromaDB (Vecteurs)...")
    try:
        client = get_chroma_client()
        coll = client.get_or_create_collection("rag_chunks")
        count_vectors = coll.count()
        print(f"   ✅ Connexion Chroma OK. Contient {count_vectors} chunks.")
    except Exception as e:
        print(f"   ❌ ERREUR CHROMA : {e}")

    print("\n🏁 Diagnostic terminé.")

if __name__ == "__main__":
    check_system_state()