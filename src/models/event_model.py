from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from base import Base
from datetime import datetime

class Event(Base):  
    __tablename__ = "events"  

    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE", onupdate="CASCADE"))
    name: Mapped[str]= mapped_column(String, nullable=False)  # Assuming there is a name field
    description: Mapped[str]= mapped_column(String, nullable=True)  # Assuming there is a description field  
    start_at: Mapped[str]= mapped_column(DateTime(timezone=True), nullable=True)  
    end_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)  

    # Relationships  
    workspaces = relationship("Workspace", back_populates="events")
