import os
import logging
from pydantic import FilePath
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class TextExtractor:
    @staticmethod
    def extract_from_file(file_path: str) -> str:
        """
        Détecte l'extension et extrait le texte.
        Supporte: .txt, .pdf, .md
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier n'existe pas : {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        try:
            if ext == ".pdf":
                return TextExtractor._read_pdf(file_path)
            elif ext in [".txt", ".md", ".json", ".csv"]:
                return TextExtractor._read_text(file_path)
            else:
                logger.warning(f"⚠️ Extension non supportée pour l'extraction texte : {ext}")
                return ""
        except Exception as e:
            logger.error(f"❌ Erreur lecture fichier {file_path}: {e}")
            raise e

    @staticmethod
    def _read_text(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _read_pdf(path: str) -> str:
        text = ""
        reader = PdfReader(path)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text

text_extractor = TextExtractor()