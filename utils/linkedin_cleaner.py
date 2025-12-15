# utils/linkedin_cleaner.py
import re
from urllib.parse import urlparse, urlunparse

def clean_linkedin_url(url: str) -> str:
    """
    Nettoie une URL LinkedIn pour ne garder que la partie canonique.
    Ex: https://www.linkedin.com/in/jean-dupont?src=... -> https://www.linkedin.com/in/jean-dupont
    """
    if not url:
        return ""
        
    try:
        # 1. Parsing basique
        parsed = urlparse(url.strip())
        
        # 2. On reconstruit sans les query params (partie après ?) ni fragments (partie après #)
        # On garde scheme (https), netloc (www.linkedin.com) et path (/in/jean-dupont)
        cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        
        # 3. Retirer le slash final s'il existe (convention souvent utilisée pour les IDs)
        if cleaned.endswith("/"):
            cleaned = cleaned[:-1]
            
        return cleaned
        
    except Exception:
        # Fallback si l'URL est malformée, on renvoie telle quelle
        return url