from fastapi import APIRouter, HTTPException
from services.chat import chat_service
from schemas.api import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        result = chat_service.chat(
            question=request.question,
            employee=request.employee,
            tags=request.tags
        )
        return {
            "answer": result["response"],
            "sources": result["sources"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))