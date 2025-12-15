from repositories.user import user_repository
from repositories.base import BaseRepository
from database.models.log import ApiLogModel
from sqlalchemy import func
from datetime import datetime

class CreditsRepository(BaseRepository):
    
    def get_current_credit(self, employee: str) -> dict:
        """
        Replique de creditsRepository.getCurrentCredit()
        Retourne { currentUsage, totalCredit }
        """
        with self.get_session() as db:
            # 1. Récupérer Total Credit (User)
            user = user_repository.get_by_employee(employee)
            total_credit = user.credit if user else 0
            
            # 2. Calculer Current Usage (Somme des coûts du mois)
            # Simplifié pour l'instant : on compte juste les logs ou on met 0
            # Pour faire EXACTEMENT comme Node, il faudrait sommer api_logs.total_cost
            
            # Exemple simple : Somme des coûts > 0 ce mois-ci
            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)
            
            usage_query = db.query(func.sum(ApiLogModel.total_cost)).filter(
                ApiLogModel.employee == employee,
                ApiLogModel.total_cost > 0,
                ApiLogModel.start_time >= start_of_month
            ).scalar()
            
            current_usage = usage_query if usage_query else 0

            return {
                "currentUsage": current_usage,
                "totalCredit": total_credit
            }

credits_repository = CreditsRepository()