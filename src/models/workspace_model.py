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
    spaces_order: Mapped[list]= mapped_column(JSONB)  # Using JSON to store arrays  

    owner = relationship("User", back_populates="workspaces")
    events = relationship("Event", back_populates="workspaces")
    items = relationship("Item", back_populates="workspaces")  

    def has_active_subscription(self) -> bool:  
        return self.expires_at is None or self.on_grace_period()  

    def on_grace_period(self) -> bool:  
        return self.expires_at is not None and self.expires_at > datetime.now()  

    def maintain_subscription(self):  
        was_cancelled = not self.has_active_subscription() or self.on_grace_period()  

        self.cancelled_at = None  
        self.expires_at = None  
        # Assuming session is a SQLAlchemy session  
        # session.merge(self) or use an update pattern  
        # session.commit()  

        if was_cancelled:  
            self.subscription_renewed()  

        return self  

    def cancel_subscription(self, expires_at: datetime):  
        was_active = self.has_active_subscription()  

        self.cancelled_at = datetime.now()  
        self.expires_at = expires_at  
        # Update and commit via session  
        # session.merge(self)  
        # session.commit()  

        if was_active:  
            self.subscription_cancelled()  

        return self  

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

    def toggle_space(self, space_value: str):  
        if space_value in self.spaces_order:  
            self.spaces_order.remove(space_value)  
        else:  
            self.spaces_order.append(space_value)  
        # Persist changes to the database  
        # session.merge(self)  
        # session.commit()  
        return self  

    def set_spaces(self, selected_spaces: List[str]):  
        valid_spaces = [space_value for space_value in selected_spaces if self.is_valid_space(space_value)]  
        self.spaces_order = valid_spaces  
        # Persist changes to the database  
        # session.merge(self)  
        # session.commit()  
        return self  

    def is_space_enabled(self, space_value: str) -> bool:  
        return space_value in self.spaces_order  

    def is_valid_space(self, space_value: str) -> bool:  
        try:  
            ItemSpace(space_value)
            return True  
        except ValueError:  
            return False  

    def subscription_renewed(self):  
        # Implement your event handling logic  
        print(f"Subscription renewed for workspace {self.id}")  

    def subscription_cancelled(self):  
        # Implement your event handling logic  
        print(f"Subscription cancelled for workspace {self.id}")  