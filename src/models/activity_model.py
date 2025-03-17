from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from base import Base

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE", onupdate="CASCADE"))
    type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., task_created, task_completed, event_created
    entity_id: Mapped[str] = mapped_column(String, nullable=True)  # ID of the related entity (task, event, etc.)
    entity_type: Mapped[str] = mapped_column(String, nullable=True)  # Type of the related entity (task, event, etc.)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)  # Additional details as JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="activities")
    workspace = relationship("Workspace", back_populates="activities")

    @classmethod
    def get_recent_activities(cls, session, workspace_id: str, limit: int = 10):
        """
        Get recent activities for a workspace.
        """
        return session.query(cls).filter(
            cls.workspace_id == workspace_id
        ).order_by(cls.created_at.desc()).limit(limit).all()
