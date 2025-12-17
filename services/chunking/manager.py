import logging
import uuid
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter # pip install langchain-text-splitters
from schemas.doc import Chunk as ChunkSchema
from services.llm import llm_service

logger = logging.getLogger(__name__)

class ChunkingManager:
    
    def __init__(self):
        # Configuration standard RAG
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def chunk_data(self, doc_id: str, text_content: str, category: str, tags: List[str]) -> List[ChunkSchema]:
        """
        Découpe le texte, génère les embeddings et formate pour ChromaDB.
        """
        logger.info(f"✂️ Chunking started for {doc_id} ({len(text_content)} chars)")
        
        # 1. Découpage
        raw_chunks = self.splitter.create_documents([text_content])
        chunk_schemas = []

        # 2. Traitement & Embeddings
        for i, doc in enumerate(raw_chunks):
            content = doc.page_content
            
            # Génération embedding (appel LLM ou modèle local)
            # Note: Dans le code Node, c'était fait via `llmRepository.callLlmEmbeddings`
            # Ici on simule ou on appelle votre service existant s'il supporte l'embedding
            # embeddings = llm_service.generate_embeddings(content) 
            embeddings = [] # Placeholder si pas de modèle d'embedding configuré dans llm.py

            metadata = {
                "doc": doc_id,
                "chunk_index": i,
                "category": category,
                "tags": ",".join(tags),
                "source_type": "file_upload",
                "length": len(content)
            }

            chunk_schemas.append(ChunkSchema(
                content=content,
                metadata=metadata,
                embeddings=embeddings
            ))

        logger.info(f"✅ {len(chunk_schemas)} chunks générés pour {doc_id}")
        return chunk_schemas

chunking_manager = ChunkingManager()