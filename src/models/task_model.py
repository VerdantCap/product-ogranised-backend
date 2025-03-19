from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime  
from base import Base
from enum import Enum as PyEnum

class TaskPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"

class TaskType(str, PyEnum):
    GENERAL = "general"
    MEETING = "meeting"
    PROJECT = "project"
    HOLIDAY = "holiday"
    REMINDER = "reminder"

class Task(Base):  
    __tablename__ = "tasks"  

    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)
    workspace_id: Mapped[str]= mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE", onupdate="CASCADE"))
    title: Mapped[str]= mapped_column(String, nullable=False)  
    due_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)  
    description: Mapped[str] = mapped_column(Text, nullable=False)
    completed_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))
    assignee_id: Mapped[str]= mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))
    
    # New fields
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.ACTIVE)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType), default=TaskType.GENERAL)
    parent_id: Mapped[str] = mapped_column(String, ForeignKey('tasks.id', ondelete="SET NULL"), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)  # For ordering tasks
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    notifications: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_pattern: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="tasks_assigned")
    parent = relationship("Task", remote_side=[id], backref="subtasks")

    def is_completed(self) -> bool:  
        return self.completed_at is not None or self.status == TaskStatus.COMPLETED

    def reset(self, session: Session) -> 'Task':  
        """  
        Resets the task to incomplete state.  
        """  
        self.completed_at = None
        self.status = TaskStatus.ACTIVE
        session.add(self)  
        session.commit()  
        return self  

    def complete(self, session: Session) -> 'Task':  
        """  
        Marks the task as completed.  
        """  
        self.completed_at = datetime.now()
        self.status = TaskStatus.COMPLETED
        session.add(self)  
        session.commit()  
        return self
    
    def set_priority(self, priority: TaskPriority, session: Session) -> 'Task':
        """
        Sets the priority of the task.
        """
        self.priority = priority
        session.add(self)
        session.commit()
        return self
    
    def set_status(self, status: TaskStatus, session: Session) -> 'Task':
        """
        Sets the status of the task.
        """
        self.status = status
        if status == TaskStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()
        elif status != TaskStatus.COMPLETED and self.completed_at:
            self.completed_at = None
        session.add(self)
        session.commit()
        return self
    
    def add_tag(self, tag: str, session: Session) -> 'Task':
        """
        Adds a tag to the task.
        """
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
        session.add(self)
        session.commit()
        return self
    
    def remove_tag(self, tag: str, session: Session) -> 'Task':
        """
        Removes a tag from the task.
        """
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
        session.add(self)
        session.commit()
        return self

    @classmethod  
    def get_todo_tasks(cls, session: Session) -> list:  
        """  
        Returns tasks that are not completed.  
        """  
        return session.query(cls).filter(cls.completed_at.is_(None), cls.status != TaskStatus.COMPLETED).all()  

    @classmethod  
    def assigned_to(cls, session: Session, user_id: str) -> list:  
        """  
        Returns tasks assigned to a specific user or where the assignee is null.  
        """  
        return session.query(cls).filter(  
            (cls.assignee_id == user_id) | (cls.assignee_id == None)  
        ).all()
    
    @classmethod
    def get_by_priority(cls, session: Session, priority: TaskPriority) -> list:
        """
        Returns tasks with the specified priority.
        """
        return session.query(cls).filter(cls.priority == priority).all()
    
    @classmethod
    def get_by_status(cls, session: Session, status: TaskStatus) -> list:
        """
        Returns tasks with the specified status.
        """
        return session.query(cls).filter(cls.status == status).all()
    
    @classmethod
    def get_by_type(cls, session: Session, task_type: TaskType) -> list:
        """
        Returns tasks with the specified type.
        """
        return session.query(cls).filter(cls.type == task_type).all()
    
    @classmethod
    def get_subtasks(cls, session: Session, parent_id: str) -> list:
        """
        Returns subtasks for a given parent task.
        """
        return session.query(cls).filter(cls.parent_id == parent_id).all()
