from sqlalchemy import Column, String, ForeignKey, Enum as SqlEnum  
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session  
from sqlalchemy.ext.declarative import declared_attr  
import os
from enum import Enum
from enums import FileType 
from base import Base


class File(Base):  
    __tablename__ = "files"  

    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)  
    path: Mapped[str]= mapped_column(String, nullable=False)  
    type: Mapped[Enum] = mapped_column(SqlEnum(FileType), nullable=False)  # Enum FileType  
    folder: Mapped[str] = mapped_column(String)  
    category: Mapped[str] = mapped_column(String)  
    
    # Relationships and other fields
    owner_id: Mapped[str]= mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE")) 
    owner = relationship("User", back_populates="files")  

    def delete_file(self, session: Session):  
        """  
        Delete the file from storage and remove the database record.  
        """  
        # Delete the physical file if it exists  
        if os.path.exists(self.path):  
            os.remove(self.path)          
        session.delete(self)  
        session.commit()  