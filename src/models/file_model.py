from sqlalchemy import String, ForeignKey, Enum as SqlEnum, Integer, DateTime, Text, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from sqlalchemy.ext.declarative import declared_attr
import os
from enum import Enum
from datetime import datetime
from enums import FileType, ItemSpace
from base import Base


class File(Base):  
    __tablename__ = "files"  

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, nullable=False)  
    name: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)  
    type: Mapped[Enum] = mapped_column(SqlEnum(FileType), nullable=False)  # Enum FileType  
    mime_type: Mapped[str] = mapped_column(String, nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=True)  # File size in bytes
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Organization fields
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE"), nullable=False)
    folder_id: Mapped[str] = mapped_column(String, nullable=True)  # Using string reference instead of ForeignKey to avoid circular dependency
    category: Mapped[str] = mapped_column(String, nullable=True)
    space: Mapped[Enum] = mapped_column(SqlEnum(ItemSpace), nullable=True)
    
    # Version tracking
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    owner_id: Mapped[str] = mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False) 
    owner = relationship("User", back_populates="files")
    workspace = relationship("Workspace", back_populates="files")
    folder = relationship(
        "Folder", 
        primaryjoin="foreign(File.folder_id) == Folder.id",
        back_populates="files"
    )

    # Note: File deletion should be handled by the storage utility functions
    # rather than directly in the model to support both local and S3/MinIO storage
    
    def to_dict(self):
        """Convert file object to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "type": self.type.value if self.type else None,
            "mime_type": self.mime_type,
            "size": self.size,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "workspace_id": self.workspace_id,
            "folder_id": self.folder_id,
            "category": self.category,
            "space": self.space.value if self.space else None,
            "version": self.version,
            "owner_id": self.owner_id
        }
