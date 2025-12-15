import logging
from sqlalchemy.orm import Session
from database.models.prompt import PromptModel
from schemas.prompt import PromptCreate, PromptResponse
from .base import BaseRepository

# Configuration du logger pour ce fichier
logger = logging.getLogger(__name__)

class PromptRepository(BaseRepository):
    
    def get_by_name(self, name: str) -> PromptResponse | None:
        """Utilisé en interne par le backend"""
        with self.get_session() as db:
            prompt = db.query(PromptModel).filter(PromptModel.name == name).first()
            if prompt:
                return PromptResponse.model_validate(prompt)
            return None

    def get_prompts_for_user(self, employee: str) -> list[PromptResponse]:
        """
        Récupère UNIQUEMENT les prompts créés par l'utilisateur courant.
        FILTRE STRICT : prompt.user == employee
        """
        logger.info(f"🔍 [PromptRepo] Recherche des prompts STRICTEMENT pour l'user: '{employee}'")
        
        with self.get_session() as db:
            # Requête stricte
            query = db.query(PromptModel).filter(PromptModel.user == employee)
            
            # Log de la requête SQL (pour debug avancé si besoin, sinon on log juste le count)
            # logger.debug(f"📝 [PromptRepo] Query: {str(query)}")
            
            prompts = query.all()
            count = len(prompts)
            
            logger.info(f"✅ [PromptRepo] Résultat : {count} prompt(s) trouvé(s) pour '{employee}'.")
            
            if count == 0:
                logger.warning(f"⚠️ [PromptRepo] Attention: L'utilisateur '{employee}' n'a AUCUN prompt personnalisé en base.")
            
            return [PromptResponse.model_validate(p) for p in prompts]

    def upsert_prompt(self, data: PromptCreate) -> PromptResponse:
        logger.info(f"💾 [PromptRepo] Sauvegarde/Mise à jour du prompt : '{data.name}' pour user '{data.user}'")
        with self.get_session() as db:
            existing = db.query(PromptModel).filter(PromptModel.name == data.name).first()
            
            if existing:
                logger.info(f"   -> Mise à jour du prompt existant (ID: {existing.id})")
                existing.prompt = data.prompt
                existing.user = data.user
                existing.description = data.description
                db.add(existing)
                db.commit()
                db.refresh(existing)
                return PromptResponse.model_validate(existing)
            else:
                logger.info(f"   -> Création d'un nouveau prompt")
                new_prompt = PromptModel(**data.model_dump())
                db.add(new_prompt)
                db.commit()
                db.refresh(new_prompt)
                return PromptResponse.model_validate(new_prompt)

prompt_repository = PromptRepository()