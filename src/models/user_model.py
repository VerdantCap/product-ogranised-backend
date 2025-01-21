from sqlalchemy import String  
from sqlalchemy.orm import Mapped,mapped_column, relationship  
from base import Base

class User(Base):  
    __tablename__ = 'users'  
    id: Mapped[str] = mapped_column (String, primary_key=True, index=True, nullable=False)  
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)  
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)  
    password: Mapped[str] = mapped_column(String, nullable=True)
    country: Mapped[str] = mapped_column(String, index=True, nullable=True)
    city: Mapped[str] = mapped_column(String, index=True, nullable=True)
    avatar_url: Mapped[str] = mapped_column(String, index=False, nullable=True)
    oauth_id: Mapped[str] = mapped_column(String, nullable=True)  
    oauth_driver: Mapped[str] = mapped_column(String, nullable=True)
    workspaces = relationship("workspaces", back_populates="users")  