from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    passport_file = Column(String)   # путь к сохранённому PDF
    registered_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)  # будет проставляться при старте
