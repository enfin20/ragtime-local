from abc import ABC, abstractmethod
from typing import List, Any
from schemas.doc import Chunk as ChunkSchema # <-- Import essentiel ici

class ChunkingStrategy(ABC):
    @abstractmethod
    def execute(self, doc_id: str, data: Any, tags: List[str]) -> List[ChunkSchema]:
        pass