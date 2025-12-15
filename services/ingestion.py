import os
import logging
import json
import requests
import re
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

    def _clean_text_content(self, html_content: str) -> str:
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # 1. Suppression balises techniques/navigation
        for tag in soup(["script", "style", "nav", "footer", "aside", "form", "iframe", "noscript", "header"]):
            tag.decompose()

        # 2. Suppression par patterns CSS (Sidebar, Related, Comments)
        noise_patterns = re.compile(r'(related|recommend|share|social|comment|sidebar|newsletter|author-bio|cookie|promo)', re.IGNORECASE)
        for tag in soup.find_all(attrs={"class": noise_patterns}):
            tag.decompose()
        for tag in soup.find_all(attrs={"id": noise_patterns}):
            tag.decompose()

        text = soup.get_text(separator="\n")

        # 3. La "Guillotine" : on coupe dès qu'on voit ces titres
        stop_phrases = [
            "Related Articles", "You might also like", "Recommended for you",
            "Share this article", "About the Author", "Written by",
            "Submit an Article", "Editors Pick", "Read Next"
        ]
        
        lines = []
        for line in text.splitlines():
            clean_line = line.strip()
            if not clean_line:
                continue
            
            # Si une ligne commence par une phrase d'arrêt, on stoppe tout
            stop_hit = False
            for phrase in stop_phrases:
                if clean_line.lower() == phrase.lower() or clean_line.lower().startswith(phrase.lower() + ":"):
                    stop_hit = True
                    break
            
            if stop_hit:
                logger.info(f"✂️  Texte coupé au marqueur : '{clean_line}'")
                break 
            
            lines.append(clean_line)

        return "\n".join(lines)

    def _fallback_scrape(self, url: str) -> str:
        logger.info(f"🛡️ [Fallback] Scraping : {url}")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return self._clean_text_content(response.text)
        except Exception as e:
            logger.error(f"❌ [Fallback] Erreur : {e}")
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
            
            # Nettoyage systématique même sur Tavily
            raw_tavily = tavily_repository.extract_content(input_data)
            if raw_tavily:
                content_data = self._clean_text_content(raw_tavily)
            else:
                content_data = self._fallback_scrape(input_data)

            if not content_data:
                raise Exception(f"Contenu vide pour l'URL : {input_data}")

        elif isinstance(input_data, str) and os.path.exists(input_data) and os.path.isfile(input_data):
            logger.info(f"📁 Fichier local : {input_data}")
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
            logger.info("📦 Donnée brute")
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
        
        # Synthèse IA
        synthesis_data = {}
        try:
            synthesis_input = f"Doc: {doc_id}\nContent: {preview_text}"
            synthesis_data = enrichment_service.extract_metadata(synthesis_input, "synthesis_tags")
        except Exception as e:
            logger.warning(f"⚠️ Erreur Synthèse: {e}")

        doc_data = DocCreate(
            doc=doc_id, category=category, source=source, origin=origin, tags=tags,
            status="Processing", employee=employee, job_id=job_id,
            page_content=content_data if isinstance(content_data, dict) else {"text": content_data},
            synthesis=synthesis_data.get("synthesis", ""),
            suggested_tags=synthesis_data.get("suggested_tags", [])
        )
        doc_repository.upsert_doc(doc_data)

        try:
            chunks_to_save = chunking_manager.chunk_data(doc_id, content_data, category, tags)
            if not chunks_to_save:
                logger.warning(f"⚠️ 0 chunk pour {doc_id}")
            
            chunk_repository.add_chunks(doc_id, employee, chunks_to_save)
            doc_repository.update_status(doc_id, employee, "Done")
            
            return {"status": "success", "doc_id": doc_id, "chunks_count": len(chunks_to_save), "strategy": category}

        except Exception as e:
            logger.error(f"❌ Erreur Ingestion: {e}")
            doc_repository.update_status(doc_id, employee, "Failed")
            raise e

ingestion_service = IngestionService()