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
from schemas.chat import ChatRequestLegacy 
from services.chat import chat_service     

# Logger configuré pour afficher les infos dans la console
logger = logging.getLogger(__name__)

router = APIRouter()

# ... [Routes existantes /tags non modifiées] ...

@router.get("/tags")
async def get_tags_legacy(
    employee: str = Query(..., description="User identifier"),
    job_id: Optional[str] = Query(None)
):
    try:
        tags_data = doc_repository.get_tags_with_count(employee)
        credit_info = credits_repository.get_current_credit(employee)
        final_job_id = job_id if job_id else f"job_{uuid.uuid4()}"

        return {
            "status": "success",
            "tags": tags_data,
            "currentUsage": credit_info["currentUsage"],
            "totalCredit": credit_info["totalCredit"],
            "job_id": final_job_id
        }
    except Exception as e:
        logger.error(f"Error GET /tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def get_prompts_legacy(
    employee: str = Query(..., description="User identifier")
):
    """
    Retourne UNIQUEMENT les prompts de l'utilisateur (user == employee).
    """
    logger.info(f"📥 [API] GET /prompts appelé par : '{employee}'")
    
    try:
        # Appel au repo qui contient maintenant des logs
        prompts_list = prompt_repository.get_prompts_for_user(employee)
        
        logger.info(f"📤 [API] Renvoi de {len(prompts_list)} prompts au client.")
        
        return {
            "status": "success",
            "prompts": prompts_list
        }
    except Exception as e:
        logger.error(f"❌ [API] Erreur critique GET /prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/docscategories")
async def get_docs_categories_legacy(
    employee: str = Query("system", description="User identifier"),
    job_id: Optional[str] = Query(None)
):
    try:
        categories_data = doc_repository.get_all_active_categories()
        
        if not categories_data:
            categories_data = [
                {
                    "category": "profile",
                    "description": "Profil LinkedIn ou CV",
                    "is_active": True,
                    "extraction_instructions": "Extrais l'expérience...",
                    "data_schema": {}
                },
                {
                    "category": "company",
                    "description": "Page entreprise",
                    "is_active": True,
                    "extraction_instructions": "Extrais les infos société...",
                    "data_schema": {}
                },
                {
                    "category": "post",
                    "description": "Publication ou Article",
                    "is_active": True,
                    "extraction_instructions": "Extrais le contenu...",
                    "data_schema": {}
                }
            ]

        credit_info = credits_repository.get_current_credit(employee)
        final_job_id = job_id if job_id else f"job_{uuid.uuid4()}"
        
        return {
            "status": "success",
            "docscategories": categories_data,
            "currentUsage": credit_info["currentUsage"],
            "totalCredit": credit_info["totalCredit"],
            "job_id": final_job_id
        }
    except Exception as e:
        logger.error(f"Error GET /docscategories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/urls")
async def ingest_url_get_legacy(
    url: str = Query(..., description="Target URL"),
    employee: str = Query(..., description="User identifier"),
    job_id: Optional[str] = Query(None),
    fields: Optional[str] = Query(None)
):
    try:
        cleaned_url = url
        if "linkedin.com" in url:
            cleaned_url = clean_linkedin_url(url)
            
        doc = doc_repository.get_doc(doc_id=cleaned_url, employee=employee)

        return {
            "status": "success",
            "message": "doc retrieved",
            "data": [doc] if doc else []
        }
    except Exception as e:
        logger.error(f"Error GET /urls: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.delete("/urls")
async def ingest_url_delete_legacy(
    url: str = Query(..., description="Target URL"),
    employee: str = Query(..., description="User identifier")
):
    try:
        cleaned_url = url
        if "linkedin.com" in url:
            cleaned_url = clean_linkedin_url(url)
            
        result = doc_repository.delete_doc(doc_id=cleaned_url, employee=employee)
        return result
    except Exception as e:
        logger.error(f"Error DELETE /urls: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        

@router.post("/urls", response_model=IngestResponse)
async def ingest_url_post_legacy(
    request: IngestUrlRequest, 
    fields: Optional[str] = Query(None)
):
    try:
        result = ingestion_service.process_input(
            input_data=request.url,
            employee=request.employee,
            tags=request.tags,
            origin=f"legacy_post_{fields}" if fields else "legacy_post"
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"FATAL ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# STANDARD API ROUTES
# =====================================================================

@router.post("/text", response_model=IngestResponse)
async def ingest_text(request: IngestTextRequest):
    try:
        result = ingestion_service.process_input(
            input_data=request.text,
            employee=request.employee,
            tags=request.tags,
            origin="api_text"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/url", response_model=IngestResponse)
async def ingest_url(request: IngestUrlRequest):
    try:
        result = ingestion_service.process_input(
            input_data=request.url,
            employee=request.employee,
            tags=request.tags,
            origin="api_url"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    employee: str = Form("api_user"),
    tags: str = Form("")
):
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        result = ingestion_service.process_input(
            input_data=temp_file_path,
            employee=employee,
            tags=tag_list,
            origin="api_file"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/version")
async def get_version():
    return {"version": "locale"}


@router.get("/tags/{tag}/docs")
async def get_tags_docs_legacy(
    tag: str,
    employee: str = Query(..., description="User identifier"),
    job_id: Optional[str] = Query(None)
):
    try:
        docs_list = doc_repository.get_docs_by_tag(employee, tag)
        credit_info = credits_repository.get_current_credit(employee)
        final_job_id = job_id if job_id else f"job_{uuid.uuid4()}"

        return {
            "status": "success",
            "docs": docs_list,
            "currentUsage": credit_info["currentUsage"],
            "totalCredit": credit_info["totalCredit"],
            "job_id": final_job_id
        }
    except Exception as e:
        logger.error(f"❌ Erreur GET /tags/{tag}/docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/chat")
async def chat_legacy(request: ChatRequestLegacy):
    try:
        chat_result = chat_service.handle_legacy_chat(request)
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
        logger.error(f"❌ Erreur POST /ingest/chat: {e}")
        return {
            "status": "error",
            "response": f"Error: {str(e)}",
            "sources": []
        }