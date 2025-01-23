from sqlalchemy import String, ForeignKey, DateTime 
from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime  
from base import Base
from enums import ItemSpace
from typing import List

class Workspace(Base):  
    __tablename__ = "workspaces"  
    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)  
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))  
    cancelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stripe_id: Mapped[str] = mapped_column(String, nullable=False) 
    spaces_order: Mapped[list]= mapped_column(JSONB)  # Using JSON to store arrays  

    userworkspace = relationship("UserWorkspace", back_populates="workspace")
    events = relationship("Event", back_populates="workspaces")
    items = relationship("Item", back_populates="workspaces")  

    def has_active_subscription(self) -> bool:  
        return self.expires_at is None or self.on_grace_period()  

    def on_grace_period(self) -> bool:  
        return self.expires_at is not None and self.expires_at > datetime.now()  
    
    def enabled_spaces_ordered(self) -> List[str]:  
        enabled_spaces = []  
        for space_value in self.spaces_order:  
            try:
                space = ItemSpace(space_value)  
                enabled_spaces.append(space)  
            except ValueError:  
                # Ignore invalid values  
                pass  
        return enabled_spaces  