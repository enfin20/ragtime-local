from pydantic import BaseModel
from typing import Optional

class PromptBase(BaseModel):
    name: str
    prompt: str
    user: str = "system"
    description: Optional[str] = None

class PromptCreate(PromptBase):
    pass

class PromptResponse(PromptBase):
    id: int
    
    class Config:
        from_attributes = True