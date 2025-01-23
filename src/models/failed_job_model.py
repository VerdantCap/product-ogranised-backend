from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy.sql import func  
from base import Base
from datetime import datetime

class FailedJob(Base):  
    __tablename__ = 'failed_jobs'  
    
    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable= False)  
    connection: Mapped[str]= mapped_column(Text, nullable=False)  
    queue: Mapped[str]= mapped_column(Text, nullable=False)  
    payload: Mapped[str]= mapped_column(Text, nullable=False)  
    exception: Mapped[str]= mapped_column(Text, nullable=False)  
    failed_at: Mapped[datetime]= mapped_column(DateTime, default=func.now())  