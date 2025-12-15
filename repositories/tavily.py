import os
import requests
import logging
import json
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TavilyRepository:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.extract_url = "https://api.tavily.com/extract"
        if not self.api_key:
            logger.warning("⚠️ TAVILY_API_KEY non définie. Le scraping va échouer.")

        
    def extract_content(self, url: str) -> str:
        """
        Utilise l'API Tavily Extract pour récupérer le contenu brut d'une URL.
        """


        logger.info(f"🌐 [Tavily] Extracting content from: {url}")

        try:
            response = requests.post(
                self.extract_url,
                json={
                    "api_key": self.api_key,
                    "urls": [url],
                    "include_images": False
                },
                timeout=30 # Bonnes pratiques : timeout
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Tavily API Error: {response.status_code} - {response.text}")
                return ""

            data = response.json()
            results = data.get("results", [])
            
            if results and len(results) > 0:
                raw_content = results[0].get("raw_content", "")
                logger.info(f"✅ [Tavily] Content retrieved ({len(raw_content)} chars)")
                return raw_content
            
            return ""

        except Exception as e:
            logger.error(f"❌ Error communicating with Tavily: {e}")
            return ""

tavily_repository = TavilyRepository()