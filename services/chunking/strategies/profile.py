from typing import List, Any
from schemas.doc import Chunk as ChunkSchema
from ..factory import chunk_factory
from .base import ChunkingStrategy
from .general import GeneralStrategy

# IMPORT NOUVEAU
from services.chunking.enrichment import enrichment_service 

class ProfileStrategy(ChunkingStrategy):
    def __init__(self):
        self.text_strategy = GeneralStrategy()

    def execute(self, doc_id: str, data: Any, tags: List[str]) -> List[ChunkSchema]:
        if not isinstance(data, dict):
            return self.text_strategy.execute(doc_id, data, tags)

        chunks = []
        person_name = data.get("name", "Inconnu")

        # 1. Chunk "About" + ENRICHISSEMENT
        if data.get("about"):
            about_text = f"À propos de {person_name} : {data['about']}"
            
            # --- NOUVEAU : Appel LLM pour extraire les skills ---
            # On utilise le prompt 'chunk_about' que vous avez migré en base
            enriched_meta = enrichment_service.extract_metadata(data['about'], "chunk_about")
            # ----------------------------------------------------

            about_chunks = self.text_strategy.execute(doc_id, about_text, tags)
            
            for c in about_chunks:
                c.metadata["type"] = "profile_about"
                c.metadata["person_name"] = person_name
                
                # Injection des métadonnées LLM (Skills, etc.)
                if enriched_meta:
                    # On convertit les listes en strings pour Chroma
                    if "hard_skills" in enriched_meta:
                        c.metadata["hard_skills"] = ", ".join(enriched_meta["hard_skills"])
                    if "soft_skills" in enriched_meta:
                        c.metadata["soft_skills"] = ", ".join(enriched_meta["soft_skills"])
                    if "languages" in enriched_meta:
                        c.metadata["languages"] = ", ".join(enriched_meta["languages"])

            chunks.extend(about_chunks)

        # 2. Chunks "Experience"
        experiences = data.get("experience", [])
        if isinstance(experiences, list):
            for exp in experiences:
                chunk = chunk_factory.create_experience_chunk(doc_id, exp, person_name)
                chunk.metadata["tags"] = ",".join(tags)
                chunks.append(chunk)

        # 3. Chunks "Education"
        education = data.get("education", [])
        if isinstance(education, list):
            for edu in education:
                chunk = chunk_factory.create_education_chunk(doc_id, edu, person_name)
                chunk.metadata["tags"] = ",".join(tags)
                chunks.append(chunk)

        return chunks