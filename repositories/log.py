from schemas.log import ApiLogCreate
from database.models.log import ApiLogModel
from .base import BaseRepository

class LogRepository(BaseRepository):
    def create_log(self, log_data: ApiLogCreate):
        with self.get_session() as db:
            log = ApiLogModel(**log_data.model_dump())
            db.add(log)
            # Pas de return nécessaire pour du logging fire-and-forget
            
log_repository = LogRepository()