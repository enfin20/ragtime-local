import shutil
import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional

from utils.linkedin_cleaner import clean_linkedin_url
from services.ingestion import ingestion_service
from repositories.doc import doc_repository
from repositories.credits import credits_repository
from repositories.prompt import prompt_repository
from schemas.api import IngestTextRequest, IngestUrlRequest, IngestResponse
from schemas.chat import ChatRequestNode # Le bon schéma
from services.chat import chat_service     

logger = logging.getLogger(__name__)

router = APIRouter()

# ... [Garder les routes GET tags, prompts, etc. qui fonctionnaient] ...
# (Je ne les remets pas pour ne pas saturer la réponse, elles sont correctes dans votre version précédente)

@router.get("/tags")
async def get_tags_legacy(employee: str = Query(...), job_id: Optional[str] = Query(None)):
    tags_data = doc_repository.get_tags_with_count(employee)
    credit_info = credits_repository.get_current_credit(employee)
    return {"status": "success", "tags": tags_data, "currentUsage": credit_info["currentUsage"], "totalCredit": credit_info["totalCredit"], "job_id": job_id or f"job_{uuid.uuid4()}"}

@router.get("/prompts")
async def get_prompts_legacy(employee: str = Query(...)):
    prompts_list = prompt_repository.get_prompts_for_user(employee)
    return {"status": "success", "prompts": prompts_list}

@router.get("/docscategories")
async def get_docs_categories_legacy(employee: str = Query("system"), job_id: Optional[str] = Query(None)):
    categories_data = doc_repository.get_all_active_categories()
    credit_info = credits_repository.get_current_credit(employee)
    return {"status": "success", "docscategories": categories_data, "currentUsage": credit_info["currentUsage"], "totalCredit": credit_info["totalCredit"], "job_id": job_id or f"job_{uuid.uuid4()}"}

@router.get("/urls")
async def ingest_url_get_legacy(url: str = Query(...), employee: str = Query(...)):
    cleaned_url = clean_linkedin_url(url) if "linkedin.com" in url else url
    doc = doc_repository.get_doc(doc_id=cleaned_url, employee=employee)
    return {"status": "success", "message": "doc retrieved", "data": [doc] if doc else []}

@router.delete("/urls")
async def ingest_url_delete_legacy(url: str = Query(...), employee: str = Query(...)):
    cleaned_url = clean_linkedin_url(url) if "linkedin.com" in url else url
    return doc_repository.delete_doc(doc_id=cleaned_url, employee=employee)

@router.post("/urls", response_model=IngestResponse)
async def ingest_url_post_legacy(request: IngestUrlRequest, fields: Optional[str] = Query(None)):
    return ingestion_service.process_input(input_data=request.url, employee=request.employee, tags=request.tags, origin=f"legacy_post_{fields}" if fields else "legacy_post")

@router.post("/text", response_model=IngestResponse)
async def ingest_text(request: IngestTextRequest):
    return ingestion_service.process_input(input_data=request.text, employee=request.employee, tags=request.tags, origin="api_text")

@router.post("/url", response_model=IngestResponse)
async def ingest_url(request: IngestUrlRequest):
    return ingestion_service.process_input(input_data=request.url, employee=request.employee, tags=request.tags, origin="api_url")

@router.post("/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...), employee: str = Form("api_user"), tags: str = Form("")):
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        return ingestion_service.process_input(input_data=temp_file_path, employee=employee, tags=tag_list, origin="api_file")
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)

@router.get("/version")
async def get_version(): return {"version": "locale"}

@router.get("/tags/{tag}/docs")
async def get_tags_docs_legacy(tag: str, employee: str = Query(...), job_id: Optional[str] = Query(None)):
    docs_list = doc_repository.get_docs_by_tag(employee, tag)
    credit_info = credits_repository.get_current_credit(employee)
    return {"status": "success", "docs": docs_list, "currentUsage": credit_info["currentUsage"], "totalCredit": credit_info["totalCredit"], "job_id": job_id or f"job_{uuid.uuid4()}"}

# =====================================================================
# ROUTE /userchat CORRIGÉE
# =====================================================================

@router.post("/chat")
async def chat_legacy(request: ChatRequestNode):
    return await user_chat_legacy(request)

@router.post("/userchat")
async def user_chat_legacy(request: ChatRequestNode):
    """
    Route compatible Node.js pour le chat.
    Utilise ChatRequestNode avec validateur 'tags' pour éviter 422.
    """
    try:
        # Traitement
        chat_result = chat_service.handle_node_chat(request)
        
        # Info Crédits
        credit_info = credits_repository.get_current_credit(request.employee)
        final_job_id = request.job_id if request.job_id else f"job_{uuid.uuid4()}"

        return {
            "status": "success",
            "response": chat_result["response"],
            "sources": chat_result["sources"],
            "currentUsage": credit_info["currentUsage"],
            "totalCredit": credit_info["totalCredit"],
            "job_id": final_job_id
        }
    except Exception as e:
        logger.error(f"❌ Erreur POST /ingest/userchat: {e}", exc_info=True)
        return {
            "status": "error",
            "response": f"Error: {str(e)}",
            "sources": []
        }