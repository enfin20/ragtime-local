import sys
import os

# Ajout du dossier parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database.models import LoginModel

def seed_user():
    print("🚀 Démarrage de l'initialisation utilisateur...")

    db = next(get_db())
    target_email = "cv@duhamel.xyz"
    
    try:
        # --- [1] Nettoyage préventif ---
        # On supprime l'utilisateur s'il existe déjà pour éviter les doublons/erreurs
        deleted_count = db.query(LoginModel).filter(LoginModel.employee == target_email).delete()
        db.commit()
        if deleted_count > 0:
            print(f"🧹 Utilisateur existant '{target_email}' supprimé.")

        # --- [2] Insertion de données ---
        new_user = LoginModel(
            employee=target_email,
            company="Local Corp",
            lastname="Dev",
            firstname="Junior",
            password="admin1",
            credit=1000,
            services={"graph_rag": True}
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ User inséré en DB avec succès : ID={new_user.id}, Services={new_user.services}")

    except Exception as e:
        db.rollback() # Important en cas d'erreur
        print(f"❌ Erreur lors de l'opération SQL : {e}")
    finally:
        db.close() # Bonne pratique pour libérer la connexion

if __name__ == "__main__":
    seed_user()