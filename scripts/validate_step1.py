import sys
import os

# Ajout du dossier parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, get_db
from database.models import Base, LoginModel, DocModel
from schemas.user import LoginCreate, LoginResponse
from schemas.doc import DocCreate

def run_validation():
    print("🚀 Démarrage de la validation Étape 1 (Database & Schemas)...")

    # 1. Création des Tables (Test des Models)
    print("\n--- [1] Initialisation SQLite ---")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables créées avec succès (logins, docs, api_logs).")
    except Exception as e:
        print(f"❌ Erreur création tables: {e}")
        return

    # 2. Insertion de données (Test Session + Models)
    print("\n--- [2] Test Insertion SQL ---")
    db = next(get_db())
    
    # Nettoyage préventif
    db.query(LoginModel).filter(LoginModel.employee == "test_dev").delete()
    db.commit()

    try:
        new_user = LoginModel(
            employee="cv@duhamel.xyz",
            company="Local Corp",
            lastname="Dev",
            firstname="Junior",
            password="admin1",
            services={"graph_rag": True}
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"✅ User inséré en DB: ID={new_user.id}, Services={new_user.services}")
    except Exception as e:
        print(f"❌ Erreur insertion SQL: {e}")
        return

    # 3. Validation Pydantic (Test Schemas -> Model -> Schema)
    print("\n--- [3] Test Validation Pydantic ---")
    try:
        # Conversion Model SQL -> Schema Pydantic
        user_schema = LoginResponse.model_validate(new_user)
        print(f"✅ Conversion SQL->Pydantic réussie: {user_schema.employee} (Pass masqué)")
        
        # Test Doc Schema
        doc_data = DocCreate(
            doc="https://linkedin.com/in/test",
            category="profile",
            source="linkedin",
            origin="extension",
            tags=["test"],
            employee="test_dev",
            job_id="job_123",
            page_content={"name": "Test Profile", "skills": ["Python"]}
        )
        print(f"✅ Schema Doc valide: {doc_data.doc}")
        
    except Exception as e:
        print(f"❌ Erreur validation Pydantic: {e}")
        return

    print("\n🎉 ÉTAPE 1 TERMINÉE AVEC SUCCÈS : Structure propre et modulaire validée.")

if __name__ == "__main__":
    run_validation()