from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped,mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from base import Base
from datetime import datetime
from models.association_tables import user_workspace

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
    access_token: Mapped[str] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email_notification: Mapped[bool]= mapped_column(Boolean, default=False)  
    sms_notification: Mapped[bool]= mapped_column(Boolean, default=False)  
    push_notification: Mapped[bool]= mapped_column(Boolean, default=False)
    active_workspace_id: Mapped[str] = mapped_column(String, ForeignKey('workspaces.id'), nullable=True)

    workspaces = relationship(
        'Workspace',
        secondary=user_workspace,
        back_populates='users'
    )
    tasks_owned = relationship("Task", foreign_keys="Task.owner_id")
    tasks_assigned = relationship("Task", foreign_keys="Task.assignee_id")    
    files = relationship("File", back_populates="owner")    
    items = relationship("Item", back_populates="owner")

    @hybrid_property
    def is_oauthed(self) -> bool:
        return self.oauth_id is not None  