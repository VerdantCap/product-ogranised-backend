from sqlalchemy import String, Float, Boolean, DateTime, Date, ForeignKey, Integer, Text, JSON  
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, date 
from base import Base

class Excursion(Base):  
    __tablename__ = "excursions"  

    id: Mapped[str]= mapped_column(String, primary_key=True, index=True, nullable=False)  
    item_id: Mapped[str]= mapped_column(String, ForeignKey('items.id', ondelete="CASCADE", onupdate="CASCADE"))  
    name: Mapped[str]= mapped_column(String, nullable=False)  
    booking_ref: Mapped[str]= mapped_column(String, nullable=True)  
    provider: Mapped[str]= mapped_column(String, nullable=True)  
    excursion_date: Mapped[date]= mapped_column(Date, nullable=True)  
    start_time: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)  
    end_time: Mapped[datetime]= mapped_column(DateTime(timezone=True), nullable=True)  
    contact_number: Mapped[str]= mapped_column(String, nullable=True)  
    contact_email: Mapped[str]= mapped_column(String, nullable=True)  
    total_cost: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)  
    deposit_paid: Mapped[bool]= mapped_column(Boolean, nullable=True, default=False)  
    deposit_amount: Mapped[float]= mapped_column(Float, nullable=True, default=0.0)  
    deposit_date: Mapped[date]= mapped_column(Date, nullable=True)  
    remaining_balance: Mapped[float]= mapped_column(Float, nullable=True, default=0.0)  
    balance_due_date: Mapped[date]= mapped_column(Date, nullable=True)  
    notes: Mapped[str]= mapped_column(Text, nullable=True)  
    attachments: Mapped[list]= mapped_column(JSONB, nullable=True, default=list)  

    # Relationships  
    items = relationship("Item", back_populates="excursions")  
