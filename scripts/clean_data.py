import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session

# Path hack
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, get_chroma_client
from database.models import DocModel, ApiLogModel

LOG_DIR = Path("logs")

def clean_data():
    print("🔥 Démarrage du nettoyage (Mode : Business Data Only)...")
    print("   (Les Users et Prompts seront conservés)")

    # --- 1. NETTOYAGE LOGS ---
    if LOG_DIR.exists():
        print("📝 Nettoyage des logs fichiers...")
        for log_file in LOG_DIR.glob("*.log"):
            with open(log_file, "w") as f:
                f.write("")
            print(f"   - Vidé : {log_file.name}")

    # --- 2. NETTOYAGE SQLITE (CIBLÉ) ---
    print("🗄️  Nettoyage SQLite (Docs & Logs)...")
    with Session(engine) as session:
        # On supprime uniquement les données métier
        deleted_docs = session.query(DocModel).delete()
        deleted_logs = session.query(ApiLogModel).delete()
        session.commit()
        print(f"✅ Supprimé : {deleted_docs} documents")
        print(f"✅ Supprimé : {deleted_logs} logs d'API")
        print("ℹ️  Users et Prompts conservés.")

    # --- 3. NETTOYAGE CHROMA ---
    print("🎨 Reset ChromaDB (Vecteurs)...")
    try:
        client = get_chroma_client()
        try:
            client.delete_collection("rag_chunks")
            print("✅ Collection 'rag_chunks' supprimée.")
        except ValueError:
            pass # N'existait pas
        
        # On recrée vide
        client.get_or_create_collection("rag_chunks")
        print("✅ Collection 'rag_chunks' recréée vide.")
        
    except Exception as e:
        print(f"❌ Erreur Chroma : {e}")

    print("\n🧹 Nettoyage terminé ! Prêt pour une nouvelle ingestion.")

if __name__ == "__main__":
    clean_data()