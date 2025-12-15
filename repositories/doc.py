from datetime import datetime
from collections import Counter
import logging

from database.models.doc import DocModel
from database.models.doc_category import DocCategoryModel 
from schemas.doc import DocCreate, DocResponse 
from .base import BaseRepository

logger = logging.getLogger(__name__)

class DocRepository(BaseRepository):
    
    def get_doc(self, doc_id: str, employee: str) -> DocResponse | None:
        with self.get_session() as db:
            doc = db.query(DocModel).filter(
                DocModel.doc == doc_id,
                DocModel.employee == employee
            ).first()

            if not doc:
                alt_id = doc_id[:-1] if doc_id.endswith("/") else doc_id + "/"
                doc = db.query(DocModel).filter(
                    DocModel.doc == alt_id,
                    DocModel.employee == employee
                ).first()

            if doc:
                return DocResponse.model_validate(doc)
            return None

    def get_filtered_doc_ids(self, employee: str, tags: list[str] = None, exclude_ids: list[str] = None) -> list[str]:
        """
        Récupère les IDs des documents qui correspondent aux tags ET qui ne sont pas exclus.
        Sert de pré-filtre pour la recherche vectorielle.
        """
        with self.get_session() as db:
            query = db.query(DocModel).filter(
                DocModel.employee == employee,
                DocModel.status == "Done"
            )
            docs = query.all()
            
            valid_ids = []
            target_tags = set(t.lower().strip() for t in tags) if tags else set()
            excluded_set = set(exclude_ids) if exclude_ids else set()

            for doc in docs:
                if doc.doc in excluded_set:
                    continue

                if not target_tags:
                    valid_ids.append(doc.doc)
                    continue

                if doc.tags:
                    doc_tags = set(str(t).lower().strip() for t in doc.tags)
                    if not target_tags.isdisjoint(doc_tags):
                        valid_ids.append(doc.doc)
            
            return valid_ids

    def upsert_doc(self, data: DocCreate) -> DocResponse:
        with self.get_session() as db:
            existing = db.query(DocModel).filter(
                DocModel.doc == data.doc,
                DocModel.employee == data.employee
            ).first()

            doc_to_return = None

            if existing:
                existing.category = data.category
                existing.tags = data.tags
                existing.synthesis = data.synthesis
                existing.suggested_tags = data.suggested_tags
                existing.quality = data.quality
                existing.page_content = data.page_content
                existing.status = data.status
                existing.date_update = datetime.now()
                
                db.add(existing)
                db.commit()
                db.refresh(existing)
                doc_to_return = existing
            else:
                new_doc = DocModel(**data.model_dump())
                db.add(new_doc)
                db.commit()
                db.refresh(new_doc)
                doc_to_return = new_doc
             
            return DocResponse.model_validate(doc_to_return)

    def update_status(self, doc_id: str, employee: str, status: str):
        with self.get_session() as db:
            doc = db.query(DocModel).filter(
                DocModel.doc == doc_id, 
                DocModel.employee == employee
            ).first()
            if doc:
                doc.status = status
                doc.date_update = datetime.now()
                db.commit()

    def delete_doc(self, doc_id: str, employee: str) -> dict:
        from repositories.chunk import chunk_repository 

        with self.get_session() as db:
            doc = db.query(DocModel).filter(
                DocModel.doc == doc_id,
                DocModel.employee == employee
            ).first()

            if not doc:
                alt_id = doc_id[:-1] if doc_id.endswith("/") else doc_id + "/"
                doc = db.query(DocModel).filter(
                    DocModel.doc == alt_id,
                    DocModel.employee == employee
                ).first()

            if not doc:
                return {"status": "success", "message": "No document found to delete."}

            chunk_repository.delete_chunks_by_doc(doc.doc, employee)
            
            db.delete(doc)
            db.commit()
            
            return {"status": "success", "message": f"{doc_id} SUCCESS_DELETE"}

    def get_unique_tags(self, employee: str) -> list[str]:
        with self.get_session() as db:
            results = db.query(DocModel.tags).filter(DocModel.employee == employee).all()
            unique_tags = set()
            for (tag_list,) in results:
                if tag_list and isinstance(tag_list, list):
                    unique_tags.update(tag_list)
            return sorted(list(unique_tags))

    def get_tags_with_count(self, employee: str) -> list[dict]:
        with self.get_session() as db:
            results = db.query(DocModel.tags).filter(DocModel.employee == employee).all()
            all_tags = []
            for (tag_list,) in results:
                if tag_list and isinstance(tag_list, list):
                    all_tags.extend(tag_list)
            
            counter = Counter(all_tags)
            response = [{"tag": tag, "count": count} for tag, count in counter.items()]
            response.sort(key=lambda x: (-x["count"], x["tag"]))
            
            return response

    def get_unique_categories(self, employee: str) -> list[dict]:
        with self.get_session() as db:
            results = db.query(DocModel.category).filter(DocModel.employee == employee).distinct().all()
            categories = []
            for (cat,) in results:
                if cat:
                    categories.append({"label": cat.capitalize(), "value": cat})
            return categories

    def get_all_active_categories(self) -> list[dict]:
        with self.get_session() as db:
            cats = db.query(DocCategoryModel).filter(DocCategoryModel.is_active == True).all()
            return [
                {
                    "category": c.category,
                    "description": c.description,
                    "is_active": c.is_active,
                    "extraction_instructions": c.extraction_instructions,
                    "data_schema": c.data_schema
                }
                for c in cats
            ]
        
    def get_docs_by_tag(self, employee: str, tag: str) -> list[dict]:
        with self.get_session() as db:
            docs = db.query(DocModel).filter(
                DocModel.employee == employee,
                DocModel.status != "Failed"
            ).all()

            results = []
            target_tag = tag.strip().lower()

            for doc in docs:
                doc_tags = [t.lower() for t in (doc.tags or [])]
                
                if target_tag in doc_tags:
                    pc = doc.page_content or {}
                    current_company = pc.get("current_company", {})
                    if not isinstance(current_company, dict): 
                        current_company = {}

                    summary = {
                        "doc": doc.doc,
                        "source": doc.source,
                        "category": doc.category,
                        "name": doc.name or "",
                        "tags": doc.tags,
                        "status": doc.status,
                        "quality": doc.quality,
                        "synthesis": doc.synthesis,
                        "suggested_tags": doc.suggested_tags,
                        "origin": doc.origin,
                        "date_init": doc.date_init,
                        "date_update": doc.date_update,
                        "about": pc.get("about", ""),
                        "current_company_name": current_company.get("name", ""),
                        "current_title": current_company.get("title", ""),
                        "modified_fields": doc.modified_fields or "",
                        "manual_comment": doc.manual_comment or ""
                    }
                    results.append(summary)
            return results
        
doc_repository = DocRepository()