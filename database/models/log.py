from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from datetime import datetime
from .base import Base

class ApiLogModel(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    method = Column(String, nullable=True)
    original_url = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    employee = Column(String, index=True, nullable=False)
    job_id = Column(String, nullable=False)
    api = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True)
    response = Column(JSON, nullable=True)
    is_pushed_to_analytics = Column(Boolean, default=False)