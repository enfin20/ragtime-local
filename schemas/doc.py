from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- CHUNKS (Partie Vectorielle) ---
class ChunkMetadata(BaseModel):
    doc: str
    type: str = "general"
    page: Optional[int] = None
    source_type: Optional[str] = None
    # Permet d'accepter d'autres champs dynamiques
    class Config:
        extra = "allow"

class Chunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    embeddings: Optional[List[float]] = None

# --- DOCS (Partie Métadonnée) ---
class DocBase(BaseModel):
    doc: str
    category: str
    source: str
    origin: str
    tags: List[str] = []
    status: str = "Processing"
    quality: float = 0.0
    synthesis: str = ""
    suggested_tags: List[str] = []
    name: Optional[str] = None
    manual_comment: Optional[str] = None

class DocCreate(DocBase):
    employee: str
    job_id: str
    page_content: Dict[str, Any] # Le JSON complet du doc

class DocResponse(DocBase):
    id: int
    employee: str                # <--- AJOUTÉ
    job_id: str                  # <--- AJOUTÉ
    page_content: Dict[str, Any] # <--- AJOUTÉ
    
    # Champs optionnels qui viennent de la DB
    previous_page_content: Optional[Dict[str, Any]] = None
    modified_fields: Optional[str] = None
    
    date_init: datetime
    date_update: datetime
    
    class Config:
        from_attributes = True