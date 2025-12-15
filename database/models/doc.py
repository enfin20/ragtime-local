from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from datetime import datetime
from .base import Base

class DocModel(Base):
    __tablename__ = "docs"

    id = Column(Integer, primary_key=True, index=True)
    doc = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)
    date_init = Column(DateTime, default=datetime.utcnow)
    source = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    tags = Column(JSON, default=[])
    synthesis = Column(Text, default="")
    suggested_tags = Column(JSON, default=[])
    quality = Column(Float, default=0.0)
    status = Column(String, default="Processing")
    employee = Column(String, index=True, nullable=False)
    job_id = Column(String, nullable=False)
    page_content = Column(JSON, nullable=False)
    previous_page_content = Column(JSON, nullable=True)
    date_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_fields = Column(String, nullable=True)
    name = Column(String, nullable=True)
    manual_comment = Column(Text, nullable=True)