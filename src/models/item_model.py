from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SqlEnum, Table  
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session, backref  
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime  
from typing import Optional
from enums import ItemSpace, ItemType  
from base import Base
from enum import Enum
from models.user_model import User
from models.file_model import File

item_association = Table(  
    'item_association', Base.metadata,  
    Column('item_id', String, ForeignKey('items.id')),  
    Column('related_item_id', String, ForeignKey('items.id'))  
)  

class Item(Base):  
    __tablename__ = "items"  

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, nullable=False)  
    space: Mapped[Enum] = mapped_column(SqlEnum(ItemSpace), nullable=False)  
    type: Mapped[Enum] = mapped_column(SqlEnum(ItemType), nullable=False)  
    fields: Mapped[dict]= mapped_column(JSONB)  
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  
    workspace_id: Mapped[str] = mapped_column(String, ForeignKey('workspaces.id', ondelete="CASCADE", onupdate="CASCADE"))  
    owner_id: Mapped[str] = mapped_column(String, ForeignKey('users.id', ondelete="CASCADE", onupdate="CASCADE"))  

    # Relationships  
    workspaces = relationship("Workspace", back_populates="items")  
    owner = relationship("User", back_populates="items")
    transports = relationship("Transport", back_populates="items")  
    accommodations = relationship("Accommodation", back_populates="items")  
    excursions = relationship("Excursion", back_populates="items")  
    related_items = relationship(  
        'Item',  
        secondary=item_association,  
        primaryjoin=id==item_association.c.item_id,  
        secondaryjoin=id==item_association.c.related_item_id,  
        backref=backref('related_to', lazy='dynamic')  
    )  

    def is_active(self) -> bool:  
        now = datetime.now()  
        return self.start_at <= now <= self.end_at  

    def has_expired(self) -> bool:  
        now = datetime.now()  
        return self.end_at <= now  

    def is_renewal(self) -> bool:  
        now = datetime.now()  
        return self.start_at > now  

    def add_file(self, session: Session, path: str, owner: Optional[User], category: str):  
        mime_type = 'application/octet-stream'  # Assume a method for MIME type detection  
        existing_file = session.query(File).filter_by(category=category, item_id=self.id).first()  

        if not existing_file:  
            existing_file = File(item_id=self.id, category=category)  

        existing_file.type = mime_type  
        existing_file.path = path  
        existing_file.workspace_id = self.workspace_id  
        existing_file.owner_id = owner.id if owner else None  

        session.add(existing_file)  
        session.commit()  
        return existing_file  

    def field(self, key: str, default=None):  
        return self.fields.get(key, default)  

    def date(self, key: str) -> Optional[datetime]:  
        date_str = self.fields.get(key)  
        return datetime.strptime(date_str, '%Y-%m-%d') if date_str else None  

    def has_start_date(self) -> bool:  
        return self.start_at is not None  

    def has_end_date(self) -> bool:  
        return self.end_at is not None  

    def is_time_bounded(self) -> bool:  
        return self.has_start_date() or self.has_end_date()