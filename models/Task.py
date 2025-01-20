from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Task(Base):  # Assuming Model is the base class from the ORM
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(8), nullable=True, unique=True)
    name = Column(String)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'))
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def casts(self) -> dict:
        return {
            "due_at": "datetime",
            "completed_at": "datetime",
            "created_at": "datetime",
            "updated_at": "datetime"
        }

    @staticmethod
    def scopeTodo(query):
        return query.filter(Task.completed_at == None)

    @staticmethod
    def scopeAssignedTo(query, user_id):
        return query.filter_by(assignee_id=user_id)

    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="tasks")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_tasks")
    workspace = relationship("Workspace", back_populates="tasks")

    # Methods for task status and management
