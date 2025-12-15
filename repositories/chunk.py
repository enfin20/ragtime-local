import uuid
import logging
from typing import List, Optional
from schemas.doc import Chunk as ChunkSchema
from database.connection import get_chroma_client

logger = logging.getLogger(__name__)

class ChunkRepository:
    def __init__(self):
        self.client = get_chroma_client()

    @property
    def collection(self):
        return self.client.get_or_create_collection(name="rag_chunks")

    def add_chunks(self, doc_id: str, employee: str, chunks: List[ChunkSchema]):
        if not chunks:
            return

        self.delete_chunks_by_doc(doc_id, employee)

        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}_{str(uuid.uuid4())[:8]}"
            ids.append(chunk_id)
            documents.append(chunk.content)
            
            meta = chunk.metadata.copy()
            meta["doc"] = doc_id
            meta["employee"] = employee
            
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, list):
                    clean_meta[k] = ",".join(map(str, v))
                elif v is None:
                    clean_meta[k] = ""
                else:
                    clean_meta[k] = v
            metadatas.append(clean_meta)

        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"✅ [Chroma] {len(ids)} chunks ajoutés pour {doc_id}")
        except Exception as e:
            logger.error(f"❌ Erreur ajout Chroma : {e}")
            raise e

    def search(self, query: str, employee: str, limit: int = 5, doc_ids_filter: Optional[List[str]] = None):
        try:
            # Construction de la clause WHERE avec $and explicite pour éviter l'erreur Chroma
            conditions = [{"employee": employee}]
            
            if doc_ids_filter is not None:
                if len(doc_ids_filter) == 0:
                    return {"ids": [], "documents": [], "metadatas": [], "distances": []}
                
                conditions.append({"doc": {"$in": doc_ids_filter}})

            if len(conditions) > 1:
                where_clause = {"$and": conditions}
            else:
                where_clause = conditions[0]

            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause
            )
            return results
        except Exception as e:
            logger.error(f"❌ Erreur recherche Chroma : {e}")
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

    def delete_chunks_by_doc(self, doc_id: str, employee: str):
        try:
            self.collection.delete(
                where={"$and": [{"doc": doc_id}, {"employee": employee}]}
            )
        except Exception as e:
            logger.warning(f"⚠️ Erreur suppression chunks (peut-être vides) : {e}")

chunk_repository = ChunkRepository()