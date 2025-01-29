from sqlalchemy import String, Text, DateTime, ForeignKey  
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from datetime import datetime  
from base import Base



class Task(Base):  
    __tablename__ = "tasks"  

    id: Mapped[str]= mapped_column(String,  primary_key=True, index=True, nullable=False)
    workspace_id: Mapped[str]= mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE", onupdate="CASCADE"))
    title: Mapped[str]= mapped_column(String, nullable=False)  
    due_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)  
    description: Mapped[str] = mapped_column(Text, nullable=False)
    completed_at: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))
    assignee_id: Mapped[str]= mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))  

    assignee = relationship("User", back_populates="tasks")  

    def is_completed(self) -> bool:  
        return self.completed_at is not None  

    def reset(self, session: Session) -> 'Task':  
        """  
        Resets the task to incomplete state.  
        """  
        self.completed_at = None  
        session.add(self)  
        session.commit()  
        return self  

    def complete(self, session: Session) -> 'Task':  
        """  
        Marks the task as completed.  
        """  
        self.completed_at = datetime.now()  
        session.add(self)  
        session.commit()  
        return self  

    @classmethod  
    def get_todo_tasks(cls, session: Session) -> list:  
        """  
        Returns tasks that are not completed.  
        """  
        return session.query(cls).filter(cls.completed_at.is_(None)).all()  

    @classmethod  
    def assigned_to(cls, session: Session, user_id: str) -> list:  
        """  
        Returns tasks assigned to a specific user or where the assignee is null.  
        """  
        return session.query(cls).filter(  
            (cls.assignee_id == user_id) | (cls.assignee_id == None)  
        ).all()  
