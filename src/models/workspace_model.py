from sqlalchemy import String, ForeignKey, DateTime 
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime  
from base import Base
from enums import ItemSpace
from typing import List
from models.association_tables import user_workspace

class Workspace(Base):  
    __tablename__ = "workspaces"  
    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False) 
    name: Mapped[str] = mapped_column(String,nullable=False) 
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))  
    cancelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stripe_id: Mapped[str] = mapped_column(String, nullable=False) 
    billing_plan: Mapped[str] = mapped_column(String, nullable=False)

    users = relationship(
        'User',
        secondary=user_workspace,
        back_populates='workspaces'
    )
    event = relationship("Event", back_populates="workspace")
    items = relationship("Item", back_populates="workspace")
    activities = relationship("Activity", back_populates="workspace")
    folders = relationship("Folder", back_populates="workspace")
    files = relationship("File", back_populates="workspace")
    spaces = relationship("Space", back_populates="workspace")
    
    def has_active_subscription(self) -> bool:
        """
        Check if the workspace has an active subscription.
        
        Returns True if the subscription is active, False otherwise.
        """
        if self.expires_at is None:
            return True
        return self.expires_at > datetime.now()
    
    def enabled_spaces(self) -> List[str]:
        """
        Get the list of enabled spaces in the workspace.
        
        Returns a list of enabled space names.
        """
        from sqlalchemy import select
        from sqlalchemy.orm import Session
        from models.space_model import Space
        
        # This is a placeholder. In actual implementation, this would query the spaces table
        # to get all enabled spaces for this workspace
        return [space.spacetype for space in self.spaces if space.status]
