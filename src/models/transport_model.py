from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship  
from sqlalchemy.dialects.postgresql import JSONB
import uuid  
from base import Base

class Transport(Base):  
    __tablename__ = "transports"  

    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)  
    item_id: Mapped[str]= mapped_column(String, ForeignKey('items.id', ondelete="CASCADE", onupdate="CASCADE"))  
    transport_mode: Mapped[str]= mapped_column(String, nullable=False)  
    trip_type: Mapped[str]= mapped_column(String, nullable=False)  
    details: Mapped[dict]= Column(JSONB, default=dict)  # Assuming 'details' to be a JSON array  

    # Relationships  
    items = relationship("Item", back_populates="transports")  
