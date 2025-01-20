from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Workspace(Base):  # Assuming Model is the base class from the ORM
    __tablename__ = 'workspaces'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Other fields related to workspace

    def casts(self) -> dict:
        # Logic for casts method
        pass

    events = relationship("Event", back_populates="workspace")
    files = relationship("File", back_populates="workspace")
    items = relationship("Item", back_populates="workspace")
    tasks = relationship("Task", back_populates="workspace")
    users = relationship("User", secondary='user_workspaces', back_populates="workspaces")

    # Methods for subscription management and space configuration
