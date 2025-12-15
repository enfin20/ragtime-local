from contextlib import contextmanager
from database.connection import SessionLocal

class BaseRepository:
    """
    Classe parente pour gérer proprement les sessions DB.
    Permet d'utiliser 'with self.get_session() as db:'
    """
    @contextmanager
    def get_session(self):
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()