from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from base import Base
from datetime import datetime
from models.association_tables import user_workspace
from typing import Optional, List

class User(Base):  
    __tablename__ = 'users'  
    
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, nullable=False)  
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)  
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)  
    password: Mapped[str] = mapped_column(String, nullable=True)
    # Profile fields
    address: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    timezone: Mapped[str] = mapped_column(String, nullable=True, default="UTC")
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    languages: Mapped[str] = mapped_column(String, nullable=True)  # Comma-separated list of languages
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    # Media
    avatar_url: Mapped[str] = mapped_column(String, index=False, nullable=True)
    cover_image_url: Mapped[str] = mapped_column(String, index=False, nullable=True)
    # OAuth fields
    google_sub: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    apple_sub: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    oauth_provider: Mapped[str] = mapped_column(String, nullable=True)  # 'google' or 'apple'
    # Verification and notification settings
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_notification: Mapped[bool] = mapped_column(Boolean, default=False)  
    sms_notification: Mapped[bool] = mapped_column(Boolean, default=False)  
    push_notification: Mapped[bool] = mapped_column(Boolean, default=False)
    # Marketing preferences
    marketing_email: Mapped[bool] = mapped_column(Boolean, default=False)
    marketing_phone: Mapped[bool] = mapped_column(Boolean, default=False)

    workspaces = relationship(
        'Workspace',
        secondary=user_workspace,
        back_populates='users'
    )
    tasks_owned = relationship("Task", foreign_keys="Task.owner_id")
    tasks_assigned = relationship("Task", foreign_keys="Task.assignee_id")
    files = relationship("File", back_populates="owner")
    folders = relationship("Folder", back_populates="owner")
    items = relationship("Item", back_populates="owner")
    activities = relationship("Activity", back_populates="user")
    spaces = relationship("Space", back_populates="user")

    @hybrid_property
    def is_oauthed(self) -> bool:
        return bool(self.google_sub or self.apple_sub)
