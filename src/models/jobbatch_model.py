from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func  
from base import Base
from datetime import datetime

class JobBatch(Base):  
    __tablename__ = 'job_batches'  
    
    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)  
    name: Mapped[str]= mapped_column(String, nullable=False)  
    total_jobs: Mapped[int]= mapped_column(Integer, nullable=False)  
    pending_jobs: Mapped[int]= mapped_column(Integer, nullable=False)  
    failed_jobs: Mapped[int]= mapped_column(Integer, nullable=False)  
    failed_job_ids: Mapped[list]= mapped_column(Text, nullable=False)  
    options: Mapped[str]= mapped_column(JSONB, nullable=True)  
    cancelled_at: Mapped[datetime]= mapped_column(DateTime, nullable=True)  
    created_at: Mapped[datetime]= mapped_column(DateTime, nullable=False, default = func.now())  
    finished_at: Mapped[datetime]= mapped_column(DateTime, nullable=True)  