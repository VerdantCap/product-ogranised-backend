from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):  # Assuming Authenticatable is the base class from the ORM
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Other fields related to user

    def casts(self) -> dict:
        # Logic for casts method
        pass

    @staticmethod
    def scopeOAuthed(query):
        # Logic for OAuth scope
        pass

    workspaces = relationship("Workspace", secondary='user_workspaces', back_populates="users")

    # Methods for workspace management and OAuth status
