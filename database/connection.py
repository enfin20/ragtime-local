from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import chromadb # <-- Import nécessaire
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION SQLITE ---
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "local_database.db")
DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CONFIGURATION CHROMADB ---
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "local_chroma_db")

def get_chroma_client():
    """Retourne une instance unique du client ChromaDB"""
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)