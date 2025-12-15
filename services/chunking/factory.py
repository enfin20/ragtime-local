from typing import Dict, Any, List
from schemas.doc import Chunk as ChunkSchema

class ChunkFactory:
    """
    Centralise la création des objets Chunk pour garantir un format de métadonnées cohérent.
    """

    @staticmethod
    def create_chunk(content: str, doc_id: str, type_chunk: str, extra_meta: Dict[str, Any] = {}) -> ChunkSchema:
        """Helper générique"""
        # On fusionne les métadonnées de base avec les spécifiques
        metadata = {
            "doc": doc_id,
            "type": type_chunk,
            **extra_meta
        }
        
        # Nettoyage des valeurs None pour Chroma
        clean_meta = {k: v for k, v in metadata.items() if v is not None}

        return ChunkSchema(
            content=content,
            metadata=clean_meta
        )

    @staticmethod
    def create_experience_chunk(doc_id: str, exp: Dict[str, Any]) -> ChunkSchema:
        """Crée un chunk spécifique pour une expérience professionnelle"""
        title = exp.get("title", "Poste inconnu")
        company = exp.get("company", "Entreprise inconnue")
        description = exp.get("description", "")
        dates = exp.get("date_range", "")

        content = f"Poste : {title}\nEntreprise : {company}\nPériode : {dates}\nDescription : {description}"
        
        # Texte optimisé pour la recherche vectorielle (Embedding)
        # Ici on garde le même contenu, mais on pourrait le résumer
        
        return ChunkFactory.create_chunk(
            content=content,
            doc_id=doc_id,
            type_chunk="experience",
            extra_meta={
                "company": company,
                "title": title,
                "source_type": "profile_structure"
            }
        )

    @staticmethod
    def create_education_chunk(doc_id: str, edu: Dict[str, Any]) -> ChunkSchema:
        school = edu.get("school", "École inconnue")
        degree = edu.get("degree", "")
        
        content = f"École : {school}\nDiplôme : {degree}"
        
        return ChunkFactory.create_chunk(
            content=content,
            doc_id=doc_id,
            type_chunk="education",
            extra_meta={
                "school": school,
                "degree": degree,
                "source_type": "profile_structure"
            }
        )

chunk_factory = ChunkFactory()