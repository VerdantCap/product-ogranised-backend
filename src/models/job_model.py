from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped,mapped_column
from base import Base
from datetime import datetime

class Job(Base):  
    __tablename__ = 'jobs'  
    
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, nullable=False)  
    queue: Mapped[str]= mapped_column(String, index=True, nullable=False)  
    payload: Mapped[str]= mapped_column(Text, nullable=False)  
    attempts: Mapped[int]= mapped_column(Integer, nullable=False)  
    reserved_at: Mapped[datetime]= mapped_column(DateTime, nullable=True)  
    available_at: Mapped[datetime]= mapped_column(DateTime, nullable=False)  
    created_at: Mapped[int]= mapped_column(Integer, nullable=False)  