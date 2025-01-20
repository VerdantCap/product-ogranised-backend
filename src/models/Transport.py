from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Transport(Base):  # Assuming Model is the base class from the ORM
    __tablename__ = 'transports'

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    # Other fields related to transport

    def item(self):
        return relationship("Item", back_populates="transports")
