# Fichier : schemas/chat.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequestLegacy(BaseModel):
    """
    Schéma strict correspondant à la requête du frontend Node.js.
    Gère les filtres d'exclusion et l'historique.
    """
    question: str
    employee: str
    tags: List[str] = []
    
    # Filtres avancés (Exclusion, Historique, Prompt spécifique)
    exclude: Optional[Dict[str, Any]] = None 
    history: Optional[List[Any]] = None
    prompt: Optional[str] = None
    strict_context: Optional[bool] = False
    
    # Contexte technique
    job_id: Optional[str] = None