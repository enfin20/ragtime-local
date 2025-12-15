# ------------------------------------------
# FICHIER : repositories/user.py
# ------------------------------------------
from sqlalchemy.orm import Session
from database.models.user import LoginModel
from schemas.user import LoginCreate, LoginResponse 
from .base import BaseRepository

class UserRepository(BaseRepository):
    
    def get_by_employee(self, employee: str) -> LoginResponse | None:
        with self.get_session() as db:
            user = db.query(LoginModel).filter(LoginModel.employee == employee).first()
            if user:
                return LoginResponse.model_validate(user)
            return None

    def create_user(self, user_data: LoginCreate) -> LoginResponse:
        with self.get_session() as db:
            user = LoginModel(
                employee=user_data.employee,
                company=user_data.company,
                lastname=user_data.lastname,
                firstname=user_data.firstname,
                credit=user_data.credit,
                password=user_data.password, 
                services=user_data.services,
                api_key=user_data.api_key
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return LoginResponse.model_validate(user)

    # --- MÉTHODE MANQUANTE AJOUTÉE ICI ---
    def verify_credentials(self, employee: str, password: str) -> dict:
        """
        Vérifie les identifiants et retourne les droits (services).
        Equivalent strict de loginsRepository.verifyCredentials en Node.js
        """
        with self.get_session() as db:
            # Recherche user avec employee ET password
            # (En prod, on utiliserait un hash, mais on calque la logique Node fournie)
            user = db.query(LoginModel).filter(
                LoginModel.employee == employee,
                LoginModel.password == password
            ).first()

            if not user:
                return {"isValid": False, "services": False}

            # Gestion des services (JSON/Dict)
            # Si user.services est vide ou None -> False
            has_services = user.services and len(user.services) > 0
            
            return {
                "isValid": True, 
                "services": user.services if has_services else False
            }

user_repository = UserRepository()