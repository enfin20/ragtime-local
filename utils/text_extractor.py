import io
import logging
import pdfplumber  # Remplacement de pypdf pour une meilleure gestion spatiale

logger = logging.getLogger(__name__)

class TextExtractor:
    
    # Configuration des marges à ignorer (en pixels/points PDF)
    # Ajustez ces valeurs selon vos documents (50-60 est souvent un bon standard pour en-tête/pied)
    TOP_MARGIN_CROP = 50
    BOTTOM_MARGIN_CROP = 50

    def extract_from_file(self, file_path: str, content_type: str = "text/plain") -> str:
        """
        Extrait le texte depuis un chemin de fichier local.
        """
        try:
            if content_type == "application/pdf" or file_path.lower().endswith(".pdf"):
                return self._extract_pdf(file_path)
            else:
                # Fallback pour fichiers texte/markdown/json
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"❌ Erreur extraction texte fichier : {e}")
            return ""

    def extract_from_bytes(self, file_bytes: bytes, filename: str) -> str:
        """
        Extrait le texte depuis un flux d'octets (utilisé par l'upload API).
        """
        try:
            if filename.lower().endswith(".pdf"):
                # pdfplumber peut ouvrir un objet BytesIO comme un fichier
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    return self._process_pdf_object(pdf)
            else:
                return file_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Erreur extraction bytes : {e}")
            raise e

    def _extract_pdf(self, file_path: str) -> str:
        """
        Méthode interne pour ouvrir un PDF depuis un chemin.
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                return self._process_pdf_object(pdf)
        except Exception as e:
            logger.error(f"❌ Erreur lecture PDF (path) : {e}")
            raise e

    def _process_pdf_object(self, pdf_obj) -> str:
        """
        Logique centrale d'extraction avec recadrage (Cropping) des en-têtes et pieds de page.
        """
        full_text = []
        
        for i, page in enumerate(pdf_obj.pages):
            try:
                width = page.width
                height = page.height

                # Calcul de la zone à conserver (Bounding Box)
                # Format: (x0, top, x1, bottom)
                # x0 = 0 (bord gauche)
                # top = TOP_MARGIN_CROP (on coupe le haut)
                # x1 = width (bord droit)
                # bottom = height - BOTTOM_MARGIN_CROP (on coupe le bas)
                
                # Vérification de sécurité : si la page est plus petite que les marges, on prend tout
                if height <= (self.TOP_MARGIN_CROP + self.BOTTOM_MARGIN_CROP):
                    logger.warning(f"⚠️ Page {i+1} trop petite pour le cropping. Extraction complète.")
                    text = page.extract_text()
                else:
                    crop_box = (
                        0, 
                        self.TOP_MARGIN_CROP, 
                        width, 
                        height - self.BOTTOM_MARGIN_CROP
                    )
                    
                    # On crée une version recadrée de la page
                    cropped_page = page.within_bbox(crop_box)
                    text = cropped_page.extract_text()

                if text:
                    full_text.append(text)

            except Exception as e:
                logger.warning(f"⚠️ Erreur extraction page {i+1} : {e}")
                continue

        # On joint les pages avec un double saut de ligne pour marquer la séparation
        return "\n\n".join(full_text)

text_extractor = TextExtractor()