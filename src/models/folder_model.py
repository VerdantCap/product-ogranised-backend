from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign
from datetime import datetime
from typing import List, Optional
from base import Base


class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Hierarchical structure
    parent_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey('folders.id', ondelete="CASCADE"), nullable=True)
    
    # Organization fields
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE"), nullable=False)
    
    # Relationships
    owner_id: Mapped[str] = mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="folders")
    workspace = relationship("Workspace", back_populates="folders")
    parent = relationship("Folder", remote_side=[id], back_populates="children")
    children = relationship("Folder", back_populates="parent", cascade="all, delete-orphan")
    files = relationship(
        "File", 
        primaryjoin="Folder.id == foreign(File.folder_id)",
        back_populates="folder", 
        cascade="all, delete-orphan"
    )
    
    def to_dict(self, include_files=False):
        """Convert folder object to dictionary for API responses"""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "parent_id": self.parent_id,
            "workspace_id": self.workspace_id,
            "owner_id": self.owner_id,
            "files_count": len(self.files) if self.files else 0
        }
        
        if include_files and self.files:
            result["files"] = [file.to_dict() for file in self.files]
            
        return result
