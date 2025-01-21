from sqlalchemy import String, Float, Boolean, Date, ForeignKey, Text  
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from sqlalchemy.dialects.postgresql import JSONB
from base import Base 
from datetime import date
import uuid   

class Accommodation(Base):  
    __tablename__ = "accommodations"  

    id: Mapped[str]= mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))  
    item_id: Mapped[str]= mapped_column(String, ForeignKey('items.id', ondelete="CASCADE", onupdate="CASCADE"))  
    name: Mapped[str]= mapped_column(String, nullable=False)  
    booking_ref: Mapped[str]= mapped_column(String, nullable=True)  
    provider: Mapped[str]= mapped_column(String, nullable=True)  
    arrival_date: Mapped[date]= mapped_column(Date, nullable=True)  
    departure_date: Mapped[date]= mapped_column(Date, nullable=True)  
    contact_number: Mapped[str]= mapped_column(String, nullable=True)  
    contact_email: Mapped[str]= mapped_column(String, nullable=True)  
    food_drink_included: Mapped[bool]= mapped_column(Boolean, nullable=True, default=False)  
    total_cost: Mapped[float]= mapped_column(Float, nullable=True, default=0.0)  
    deposit_paid: Mapped[bool]= mapped_column(Boolean, nullable=False, default=False)  
    deposit_amount: Mapped[float]= mapped_column(Float, nullable=True, default=0.0)  
    deposit_date: Mapped[date]= mapped_column(Date, nullable=True)  
    remaining_balance: Mapped[float]= mapped_column(Float, nullable=True, default=0.0)  
    balance_due_date: Mapped[date]= mapped_column(Date, nullable=True)  
    notes: Mapped[str]= mapped_column(Text, nullable=True)  
    attachments: Mapped[list]= mapped_column(JSONB, nullable=True)  

    # Relationships  
    items = relationship("Item", back_populates="accommodations")