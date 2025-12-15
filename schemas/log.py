from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ApiLogBase(BaseModel):
    employee: str
    job_id: str
    method: str
    original_url: str
    status_code: Optional[int] = None
    duration: Optional[float] = None
    total_cost: Optional[float] = None

class ApiLogCreate(ApiLogBase):
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    api: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None

class ApiLogResponse(ApiLogBase):
    id: int
    start_time: datetime
    
    class Config:
        from_attributes = True