from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class File(Base):  # Assuming Model is the base class from the ORM
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(8), nullable=True, unique=True)
    folder = Column(String, nullable=True, index=True)
    type = Column(String, index=True)
    path = Column(String)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def casts(self) -> dict:
        return {
            "created_at": "datetime",
            "updated_at": "datetime"
        }

    @staticmethod
    def booted():
        # Logic for booted method
        pass

    item = relationship("Item", back_populates="files")
    owner = relationship("User", back_populates="files")
    workspace = relationship("Workspace", back_populates="files")
