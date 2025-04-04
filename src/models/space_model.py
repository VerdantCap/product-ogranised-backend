from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from base import Base

class Space(Base):
    __tablename__ = "spaces"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, nullable=False)
    spacetype: Mapped[str] = mapped_column(String, nullable=False)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="spaces")
    user = relationship("User", back_populates="spaces")
