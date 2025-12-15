import os
import logging
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from schemas.doc import DocCreate
from repositories.doc import doc_repository
from repositories.chunk import chunk_repository
from repositories.tavily import tavily_repository
from utils.text_extractor import text_extractor
from services.chunking.manager import chunking_manager
from services.chunking.enrichment import enrichment_service

logger = logging.getLogger(__name__)

class IngestionService:
    
    def _fallback_scrape(self, url: str) -> str:
        """
        Plan B : Scraping classique si l'API Tavily échoue.
        """
        logger.info(f"🛡️ [Fallback] Tentative de scraping standard pour : {url}")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # On essaie de récupérer le texte principal
            # On vire les scripts et styles
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
                
            text = soup.get_text(separator="\n")
            
            # Nettoyage basique des lignes vides
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            if len(clean_text) < 50:
                return ""
                
            return clean_text
            
        except Exception as e:
            logger.error(f"❌ [Fallback] Echec aussi : {e}")
            return ""

    def process_input(self, input_data: str | dict, employee: str, tags: list[str], origin: str = "manual"):
        doc_name = "Document sans titre"
        content_data = "" 
        source_type = "manual"
        category = "document"

        if isinstance(input_data, str) and (input_data.startswith("http://") or input_data.startswith("https://")):
            logger.info(f"🔗 URL détectée : {input_data}")
            source_type = "web"
            category = "website"
            doc_name = input_data
            
            # [cite_start]1. Tentative Tavily [cite: 117]
            content_data = tavily_repository.extract_content(input_data)
            
            # 2. Tentative Fallback si vide
            if not content_data:
                logger.warning(f"⚠️ Tavily n'a rien renvoyé pour {input_data}. Passage au Fallback.")
                content_data = self._fallback_scrape(input_data)

            if not content_data:
                raise Exception(f"Contenu vide pour l'URL (Protection anti-bot ou erreur) : {input_data}")

        elif isinstance(input_data, str) and os.path.exists(input_data) and os.path.isfile(input_data):
            logger.info(f"📁 Fichier local détecté : {input_data}")
            source_type = "file"
            doc_name = os.path.basename(input_data)
            
            if input_data.endswith(".json"):
                with open(input_data, 'r', encoding='utf-8') as f:
                    content_data = json.load(f)
                category = "profile"
            else:
                content_data = text_extractor.extract_from_file(input_data)
                category = "document"

        else:
            logger.info("📦 Donnée brute détectée")
            source_type = "raw"
            
            if isinstance(input_data, dict):
                content_data = input_data
                if "post_text" in input_data or "text" in input_data:
                    category = "post"
                    doc_name = f"post_{int(datetime.now().timestamp())}"
                else:
                    category = "profile"
                    doc_name = f"profile_{input_data.get('name', 'unknown')}"
            else:
                doc_name = f"text_{int(datetime.now().timestamp())}.txt"
                content_data = input_data

        return self._process_content(doc_name, content_data, category, employee, tags, origin, source_type)

    def _process_content(self, doc_id: str, content_data: any, category: str, employee: str, tags: list[str], origin: str, source: str):
        job_id = f"job_{int(datetime.now().timestamp())}"
        
        preview_text = str(content_data)[:3000]
        synthesis_data = {}
        
        try:
            logger.info(f"🧠 [Ingestion] Generating synthesis for {doc_id}...")
            synthesis_input = f"Doc: {doc_id}\nContent: {preview_text}"
            synthesis_data = enrichment_service.extract_metadata(synthesis_input, "synthesis_tags")
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate synthesis: {e}")

        doc_synthesis = synthesis_data.get("synthesis", "")
        doc_suggested_tags = synthesis_data.get("suggested_tags", [])

        page_content_storage = content_data if isinstance(content_data, dict) else {"text": content_data}

        doc_data = DocCreate(
            doc=doc_id,
            category=category,
            source=source,
            origin=origin,
            tags=tags,
            status="Processing",
            employee=employee,
            job_id=job_id,
            page_content=page_content_storage,
            synthesis=doc_synthesis,
            suggested_tags=doc_suggested_tags
        )
        doc_repository.upsert_doc(doc_data)

        try:
            chunks_to_save = chunking_manager.chunk_data(doc_id, content_data, category, tags)

            if not chunks_to_save:
                logger.warning(f"⚠️ Aucun chunk généré pour {doc_id}")

            chunk_repository.add_chunks(doc_id, employee, chunks_to_save)

            doc_repository.update_status(doc_id, employee, "Done")
            logger.info(f"✅ [Ingestion] Success. {len(chunks_to_save)} chunks created via strategy.")
            
            return {
                "status": "success", 
                "doc_id": doc_id,
                "chunks_count": len(chunks_to_save),
                "strategy": category
            }

        except Exception as e:
            logger.error(f"❌ [Ingestion] Error: {e}")
            doc_repository.update_status(doc_id, employee, "Failed")
            raise e

ingestion_service = IngestionService()