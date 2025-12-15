from typing import List, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from schemas.doc import Chunk as ChunkSchema
from ..factory import chunk_factory
from .base import ChunkingStrategy
from services.chunking.enrichment import enrichment_service 

class GeneralStrategy(ChunkingStrategy):
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def execute(self, doc_id: str, data: Any, tags: List[str]) -> List[ChunkSchema]:
        text_content = ""
        if isinstance(data, str):
            text_content = data
        elif isinstance(data, dict):
            text_content = data.get("text_content") or data.get("body") or data.get("content") or str(data)
        
        if not text_content:
            return []

        # 1. Découpage
        raw_chunks = self.splitter.create_documents([text_content])
        
        final_chunks = []
        for i, rc in enumerate(raw_chunks):
            content_for_chunk = rc.page_content
            
            # 2. ENRICHISSEMENT 1 : Questions Hypothétiques
            if len(rc.page_content) > 500:
              questions = enrichment_service.generate_hypothetical_questions(rc.page_content)
            if questions:
                content_for_chunk += f"\n\n--- Questions Potentielles ---\n{questions}"

            # 3. ENRICHISSEMENT 2 : Entités Nommées (chunk_entities)
            entities = enrichment_service.extract_entities(rc.page_content)
            
            # Préparation des métadonnées aplaties pour Chroma
            extra_meta = {
                "index": i,
                "tags": ",".join(tags), # Toujours aplatir les listes
                "has_questions": bool(questions)
            }

            # On injecte les entités si trouvées
            # Le prompt renvoie : { "people": [{"name": "..."}], "companies": ... }
            if entities:
                if "people" in entities and entities["people"]:
                    names = [p["name"] for p in entities["people"] if "name" in p]
                    extra_meta["entities_people"] = ", ".join(names)
                
                if "companies" in entities and entities["companies"]:
                    names = [c["name"] for c in entities["companies"] if "name" in c]
                    extra_meta["entities_companies"] = ", ".join(names)
                
                if "tools" in entities and entities["tools"]:
                    names = [t["name"] for t in entities["tools"] if "name" in t]
                    extra_meta["entities_tools"] = ", ".join(names)

                if "locations" in entities and entities["locations"]:
                    names = [l["name"] for l in entities["locations"] if "name" in l]
                    extra_meta["entities_locations"] = ", ".join(names)

            chunk = chunk_factory.create_chunk(
                content=content_for_chunk,
                doc_id=doc_id,
                type_chunk="general",
                extra_meta=extra_meta
            )
            final_chunks.append(chunk)
            
        return final_chunks