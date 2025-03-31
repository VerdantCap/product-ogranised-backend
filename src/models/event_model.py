from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from base import Base
from datetime import datetime

class Event(Base):  
    __tablename__ = "events"  

    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE", onupdate="CASCADE"))
    name: Mapped[str]= mapped_column(String, nullable=False)
    description: Mapped[str]= mapped_column(String, nullable=True)
    location: Mapped[str]= mapped_column(String, nullable=True)  # Location of the event
    start_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)  
    end_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)
    lead: Mapped[str]= mapped_column(String, nullable=True)  # Person responsible for the event

    # Relationships  
    workspace = relationship("Workspace", back_populates="event")
