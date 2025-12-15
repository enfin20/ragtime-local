from sqlalchemy import Column, Integer, String, Text
from .base import Base

class PromptModel(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    prompt = Column(Text, nullable=False)
    user = Column(String, default="system")
    description = Column(String, nullable=True) # J'ajoute ça car présent dans votre JSON