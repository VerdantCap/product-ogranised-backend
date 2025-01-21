from sqlalchemy import String, DateTime  
from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy.sql import func  
from base import Base
from datetime import datetime

class User(Base):  
    __tablename__ = 'users'  
    id: Mapped[str] = mapped_column (String, primary_key=True, index=True, nullable=False)  
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)  
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)  
    password: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default= func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String, index=False, nullable=True)
    oauth_id: Mapped[str] = mapped_column(String, nullable=True)  
    oauth_driver: Mapped[str] = mapped_column(String, nullable=True)
    workspaces = relationship("Workspace", back_populates="owner")
    tasks = relationship("Task", back_populates="assignee")    
    files = relationship("File", back_populates="owner")    
    items = relationship("Item", back_populates="owner")    