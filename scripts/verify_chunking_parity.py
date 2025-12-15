import sys
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine
from database.models import Base
from services.ingestion import ingestion_service
from repositories.doc import doc_repository
from repositories.chunk import chunk_repository

def verify_parity():
    print("🚀 Démarrage Vérification Parité Node.js -> Python...")
    Base.metadata.create_all(bind=engine)
    
    employee_id = "parity_checker"

    # CAS 1 : Test du Post LinkedIn (Doit utiliser PostStrategy)
    post_text = """
    J'ai le plaisir d'annoncer que je rejoins OpenAI en tant que Lead Researcher.
    Après 5 ans chez Google DeepMind, c'est une nouvelle aventure qui commence !
    #AI #Career #NewJob
    """
    
    print("\n--- [1] Ingestion d'un Post LinkedIn ---")
    res_post = ingestion_service.process_input(
        input_data={"post_text": post_text}, # Format dict pour simuler structure
        employee=employee_id,
        tags=["news"],
        origin="linkedin_import"
    )
    
    # On force la catégorie 'post' car process_input détecte 'raw' par défaut pour les dicts
    # Note: Dans une vraie app, le routeur de catégorie ferait ce travail.
    # Ici, pour le test, on va vérifier si le 'synthesis' a fonctionné.

    # Vérification Synthèse
    doc_db = doc_repository.get_doc(res_post['doc_id'], employee_id)
    print(f"📄 Doc sauvegardé : {doc_db.doc}")
    print(f"   Synthèse générée : {doc_db.synthesis[:100]}...") # Doit ne pas être vide
    print(f"   Tags suggérés : {doc_db.suggested_tags}")

    if doc_db.synthesis:
        print("✅ SUCCÈS : La synthèse automatique (synthesis_tags) fonctionne !")
    else:
        print("❌ ÉCHEC : Pas de synthèse générée.")

    # CAS 2 : Vérification des métadonnées du Chunk
    # On cherche les chunks de ce doc
    chunks = chunk_repository.search("OpenAI", employee_id)
    if chunks and chunks['metadatas'] and len(chunks['metadatas'][0]) > 0:
        meta = chunks['metadatas'][0][0]
        # On vérifie si PostStrategy a bien tourné (elle ajoute le type 'post')
        print(f"📦 Metadata du Chunk : {meta}")
        if meta.get("type") == "post":
            print("✅ SUCCÈS : PostStrategy utilisée correctement.")
        else:
            print(f"⚠️ ATTENTION : Type de chunk inattendu ({meta.get('type')}).")

if __name__ == "__main__":
    verify_parity()