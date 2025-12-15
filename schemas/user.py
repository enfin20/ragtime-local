from pydantic import BaseModel, Field
from typing import Dict, Optional

class LoginBase(BaseModel):
    employee: str
    company: str 
    lastname: str
    firstname: str
    credit: float = 0.0
    services: Dict[str, bool] = Field(default_factory=dict)

class LoginCreate(LoginBase):
    password: str
    api_key: Optional[str] = None

class LoginResponse(LoginBase):
    id: int
    # On ne renvoie jamais le mot de passe !
    
    class Config:
        from_attributes = True # Permet de convertir l'objet SQLAlchemy en Pydantic

class LoginRequest(BaseModel):
    employee: str
    password: str

# AJOUT : Schéma pour la réponse de login
class LoginSuccessResponse(BaseModel):
    status: str
    message: str
    token: str
    services: Dict[str, bool] | bool # Peut être un dict ou False