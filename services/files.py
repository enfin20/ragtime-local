import logging
import shutil
import os
from datetime import datetime
from fastapi import UploadFile, BackgroundTasks

from repositories.doc import doc_repository
from repositories.chunk import chunk_repository
from schemas.doc import DocCreate
from utils.text_extractor import text_extractor
from services.chunking.manager import chunking_manager
from services.ingestion import ingestion_service # Pour réutiliser logic synthèse si besoin

logger = logging.getLogger(__name__)

class FilesService:

    async def handle_add_file_workflow(self, file: UploadFile, tags: list[str], employee: str, job_id: str, background_tasks: BackgroundTasks):
        doc_name = file.filename
        
        # 1. Création du Placeholder (Statut: Processing)
        # Permet de rendre la main tout de suite au client
        placeholder = DocCreate(
            doc=doc_name,
            category="document", # Sera affiné
            source="manual",
            origin="upload",
            tags=tags,
            status="Processing",
            employee=employee,
            job_id=job_id,
            page_content={"name": doc_name, "loading": True}
        )
        doc_repository.upsert_doc(placeholder)
        logger.info(f"⏳ [Job {job_id}] Placeholder créé pour {doc_name}")

        # 2. Lecture du contenu (En mémoire pour passer à la tâche de fond)
        content_bytes = await file.read()
        
        # 3. Lancement Tâche de Fond (Fire and Forget)
        background_tasks.add_task(
            self._process_file_background,
            doc_name,
            content_bytes,
            tags,
            employee,
            job_id,
            file.content_type
        )

        return {"status": "success", "message": "PROCESSING_STARTED", "job_id": job_id}

    def _process_file_background(self, doc_name: str, content_bytes: bytes, tags: list[str], employee: str, job_id: str, content_type: str):
        try:
            logger.info(f"🚀 [Job {job_id}] Démarrage traitement background : {doc_name}")

            # A. Extraction Texte
            text_content = ""
            if "pdf" in content_type or doc_name.endswith(".pdf"):
                # Sauvegarde temporaire si pypdf le nécessite, ou flux bytes
                text_content = text_extractor.extract_from_bytes(content_bytes, doc_name)
            else:
                text_content = content_bytes.decode("utf-8")

            if not text_content:
                raise Exception("Contenu extrait vide")

            # B. Classification / Synthèse (Simplifié par rapport au Node qui utilise un Agent)
            # On peut imaginer ici un appel LLM pour déterminer la catégorie
            category = "document" 
            
            # C. Chunking & Vectorisation
            chunks = chunking_manager.chunk_data(doc_name, text_content, category, tags)

            # D. Persistance Vectorielle (Chroma)
            chunk_repository.add_chunks(doc_name, employee, chunks)

            # E. Mise à jour Document (Statut: Done)
            final_doc = DocCreate(
                doc=doc_name,
                category=category,
                source="manual",
                origin="upload",
                tags=tags,
                status="Done",
                employee=employee,
                job_id=job_id,
                page_content={
                    "text": text_content, 
                    "preview": text_content[:500]
                },
                quality=10.0 # Arbitraire pour fichier manuel
            )
            doc_repository.upsert_doc(final_doc)
            
            logger.info(f"✅ [Job {job_id}] Traitement terminé avec succès pour {doc_name}")

        except Exception as e:
            logger.error(f"❌ [Job {job_id}] Echec traitement {doc_name}: {str(e)}")
            doc_repository.update_status(doc_name, employee, "Failed")

files_service = FilesService()