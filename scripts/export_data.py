import sys
import os
import json
import datetime
from sqlalchemy.orm import Session
from pathlib import Path

# Path hack
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, get_chroma_client
from database.models import LoginModel, DocModel, ApiLogModel, PromptModel, Base

# Configuration
EXPORT_PATH = Path("docs/export_python")

# Helper pour gérer les dates dans le JSON
def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def sqlalchemy_to_dict(obj):
    """Convertit un objet SQLAlchemy en dictionnaire propre"""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

def export_data():
    print("📦 Démarrage de l'export Data (SQLite + Chroma)...")
    
    # Création dossier
    if not EXPORT_PATH.exists():
        EXPORT_PATH.mkdir(parents=True, exist_ok=True)
        print(f"📂 Dossier créé : {EXPORT_PATH}")

    # 1. EXPORT SQLITE
    with Session(engine) as session:
        # Docs
        docs = session.query(DocModel).all()
        docs_data = [sqlalchemy_to_dict(d) for d in docs]
        with open(EXPORT_PATH / "Docs.json", "w", encoding="utf-8") as f:
            json.dump(docs_data, f, default=json_serial, indent=2, ensure_ascii=False)
        print(f"✅ [SQLite] Docs exportés : {len(docs_data)}")

        # Logins
        users = session.query(LoginModel).all()
        users_data = [sqlalchemy_to_dict(u) for u in users]
        with open(EXPORT_PATH / "Logins.json", "w", encoding="utf-8") as f:
            json.dump(users_data, f, default=json_serial, indent=2, ensure_ascii=False)
        print(f"✅ [SQLite] Logins exportés : {len(users_data)}")

        # Prompts
        prompts = session.query(PromptModel).all()
        prompts_data = [sqlalchemy_to_dict(p) for p in prompts]
        with open(EXPORT_PATH / "Prompts.json", "w", encoding="utf-8") as f:
            json.dump(prompts_data, f, default=json_serial, indent=2, ensure_ascii=False)
        print(f"✅ [SQLite] Prompts exportés : {len(prompts_data)}")

    # 2. EXPORT CHROMA (Chunks)
    try:
        chroma_client = get_chroma_client()
        collection = chroma_client.get_collection("rag_chunks")
        # On récupère tout
        results = collection.get()
        
        # Reformatage pour lisibilité
        chunks_data = []
        if results["ids"]:
            for i, id_val in enumerate(results["ids"]):
                chunks_data.append({
                    "id": id_val,
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })

        with open(EXPORT_PATH / "Chunks_Chroma.json", "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        print(f"✅ [Chroma] Chunks exportés : {len(chunks_data)}")

    except Exception as e:
        print(f"⚠️ Erreur export Chroma (collection vide ?) : {e}")

    print(f"\n🎉 Export terminé dans : {EXPORT_PATH.absolute()}")

if __name__ == "__main__":
    export_data()