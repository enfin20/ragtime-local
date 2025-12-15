import logging
from typing import List, Any
from schemas.doc import Chunk as ChunkSchema
from .strategies.general import GeneralStrategy
from .strategies.profile import ProfileStrategy
from .strategies.post import PostStrategy

logger = logging.getLogger(__name__)

class ChunkingManager:
    def __init__(self):
        self.strategies = {
            "document": GeneralStrategy(),
            "article": GeneralStrategy(),
            "website": GeneralStrategy(),
            "profile": ProfileStrategy(),
            "post": PostStrategy(),
        }
        self.default_strategy = GeneralStrategy()

    def chunk_data(self, doc_id: str, data: Any, category: str, tags: List[str]) -> List[ChunkSchema]:
        strategy = self.strategies.get(category, self.default_strategy)
        logger.info(f"🔪 [Chunking] Using strategy '{strategy.__class__.__name__}' for category '{category}'")
        return strategy.execute(doc_id, data, tags)

chunking_manager = ChunkingManager()