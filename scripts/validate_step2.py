import sys
import os

# Path hack pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from schemas.user import LoginCreate
from schemas.doc import DocCreate, Chunk as ChunkSchema
from repositories.user import user_repository
from repositories.doc import doc_repository
from repositories.chunk import chunk_repository

def run_validation():
    print("🚀 Démarrage Validation Étape 2 (Repositories)...")

    # 1. Reset DB
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ DB Reset OK.")

    # 2. Création User
    print("\n--- [User Repo] ---")
    user = user_repository.create_user(LoginCreate(
        employee="jean.dupont@local.fr",
        company="MyLocalCorp",
        lastname="Dupont",
        firstname="Jean",
        password="secret_pass",
        credit=100
    ))
    print(f"✅ User créé: {user.firstname} {user.lastname}")

    # 3. Création Doc (Métadonnées)
    print("\n--- [Doc Repo] ---")
    doc_data = DocCreate(
        doc="https://fr.wikipedia.org/wiki/Python_(langage)",
        category="wiki",
        source="web",
        origin="import",
        tags=["tech", "python"],
        employee="jean.dupont@local.fr",
        job_id="job_1",
        page_content={"title": "Python Langage", "summary": "Langage de programmation interprété."}
    )
    doc = doc_repository.upsert_doc(doc_data)
    print(f"✅ Doc inséré (SQLite): {doc.doc} (Status: {doc.status})")

    # 4. Ajout Chunks (Vecteurs)
    print("\n--- [Chunk Repo] ---")
    chunks = [
        ChunkSchema(
            content="Python est un langage de programmation interprété, multi-paradigme et multiplateformes.",
            metadata={"type": "intro", "page": 1}
        ),
        ChunkSchema(
            content="Il favorise la programmation impérative structurée, fonctionnelle et orientée objet.",
            metadata={"type": "details", "page": 1}
        )
    ]
    chunk_repository.add_chunks(doc.doc, doc.employee, chunks)
    
    # 5. Test Recherche
    print("\n--- [Search Test] ---")
    results = chunk_repository.search("programmation objet", "jean.dupont@local.fr", limit=1)
    
    if results['documents'] and len(results['documents'][0]) > 0:
        found_text = results['documents'][0][0]
        print(f"✅ Recherche Sémantique OK.\n   Question: 'programmation objet'\n   Trouvé: '{found_text}'")
    else:
        print("❌ Echec de la recherche sémantique.")

if __name__ == "__main__":
    run_validation()