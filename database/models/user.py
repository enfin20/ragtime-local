from sqlalchemy import Column, Integer, String, Float, JSON
from .base import Base

class LoginModel(Base):
    __tablename__ = "logins"

    id = Column(Integer, primary_key=True, index=True)
    employee = Column(String, unique=True, index=True, nullable=False)
    company = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    firstname = Column(String, nullable=False)
    credit = Column(Float, default=0.0)
    password = Column(String, nullable=False)
    services = Column(JSON, default={}) 
    api_key = Column(String, unique=True, nullable=True)