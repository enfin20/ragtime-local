# FICHIER : schemas/chat.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union

class ChatRequestNode(BaseModel):
    # CORRECTION : On ajoute = "" pour le rendre optionnel
    question: str = Field(default="", alias="input") 
    employee: str = Field(..., alias="user")
    
    tags: Union[List[str], str] = []
    
    # Rappel de la correction précédente pour exclude
    exclude: Union[Dict[str, Any], List[Any], None] = Field(default_factory=dict)
    
    history: Optional[List[Dict[str, Any]]] = []
    prompt: Optional[str] = None
    strict_context: Optional[bool] = True
    job_id: Optional[str] = None

    # ... (Garder les validateurs existants)
    
    class Config:
        extra = "ignore"
        populate_by_name = True