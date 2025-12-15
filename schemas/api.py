from pydantic import BaseModel
from typing import List, Optional, Any, Dict

# --- INGESTION ---
class IngestTextRequest(BaseModel):
    text: str
    tags: List[str] = []
    employee: str = "api_user"

class IngestUrlRequest(BaseModel):
    url: str
    tags: List[str] = []
    employee: str = "api_user"

class IngestResponse(BaseModel):
    status: str
    doc_id: str
    chunks_count: int
    strategy: str

# --- CHAT ---
class ChatRequest(BaseModel):
    question: str
    employee: str = "api_user"
    tags: Optional[List[str]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

# --- SEARCH (Debug) ---
class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    employee: str = "api_user"