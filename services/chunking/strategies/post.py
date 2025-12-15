from typing import List, Any
from schemas.doc import Chunk as ChunkSchema
from ..factory import chunk_factory
from .base import ChunkingStrategy
from services.chunking.enrichment import enrichment_service

class PostStrategy(ChunkingStrategy):
    def execute(self, doc_id: str, data: Any, tags: List[str]) -> List[ChunkSchema]:
        """
        Traite un Post LinkedIn/Social.
        Utilise le prompt 'chunk_post' pour extraire les métadonnées avant de chunker.
        """
        # 1. Récupération du texte brut
        text_content = ""
        if isinstance(data, str):
            text_content = data
        elif isinstance(data, dict):
            text_content = data.get("post_text") or data.get("text") or str(data)

        if not text_content:
            return []

        # 2. Enrichissement via LLM (Prompt: chunk_post)
        # Ce prompt extrait : name, company, industry, dates, likes_count, type...
        meta_extracted = enrichment_service.extract_metadata(text_content, "chunk_post")
        
        # 3. Création du Chunk unique (un post est rarement assez long pour être découpé)
        # On injecte les métadonnées extraites pour le filtrage futur
        
        chunk = chunk_factory.create_chunk(
            content=text_content,
            doc_id=doc_id,
            type_chunk="post",
            extra_meta={
                "tags": ",".join(tags),
                **meta_extracted  # Fusionne les infos extraites (ex: author, date...)
            }
        )

        return [chunk]