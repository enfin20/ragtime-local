from sqlalchemy import Column, Integer, String, Boolean, JSON, Text
from .base import Base

class DocCategoryModel(Base):
    __tablename__ = "doc_categories"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    extraction_instructions = Column(Text, nullable=True)
    data_schema = Column(JSON, nullable=True)