# Fichier : api/routes/auth.py
import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from repositories.user import user_repository
from schemas.user import LoginRequest, LoginSuccessResponse
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter()

# Récupération de la clé secrète (Comme en Node)
JWT_SECRET = os.getenv("JWT_SECRET", "votre_secret_par_defaut_a_changer")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8 # Comme le '8h' de Node

@router.post("/login", response_model=LoginSuccessResponse)
async def login(credentials: LoginRequest):
    """
    Authentifie l'utilisateur et retourne un token JWT valide 8h.
    """
    try:
        # 1. Vérification DB via Repository
        result = user_repository.verify_credentials(
            employee=credentials.employee, 
            password=credentials.password
        )
        
        # 2. Gestion échec (401)
        if not result["isValid"]:
            # Message exact de Node.js
            raise HTTPException(status_code=401, detail="INVALID_IDENTIFIERS")

        # 3. Création du Payload JWT
        # Node: { employeeId: employee, employee: employee }
        expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        payload = {
            "employeeId": credentials.employee,
            "employee": credentials.employee,
            "exp": expire
        }

        # 4. Signature du Token
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        # 5. Réponse Succès (Structure exacte Node)
        logger.info(f"✅ Connexion réussie pour : {credentials.employee}")
        
        return {
            "status": "success",
            "message": "CONNEXION_SUCCESS",
            "token": token,
            "services": result["services"]
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"❌ Erreur Login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")