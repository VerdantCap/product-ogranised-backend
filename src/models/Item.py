from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Item(Base):  # Assuming Model is the base class from the ORM
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(8), nullable=True, unique=True)
    space = Column(String, index=True)
    type = Column(String, index=True)
    fields = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    workspace_id = Column(Integer, ForeignKey('workspaces.id'))
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def casts(self) -> dict:
        return {
            "start_at": "datetime",
            "end_at": "datetime",
            "created_at": "datetime",
            "updated_at": "datetime"
        }

    @staticmethod
    def scopeSpace(query, space):
        return query.filter_by(space=space)

    @staticmethod
    def scopeType(query, type):
        return query.filter_by(type=type)

    @staticmethod
    def scopeStatus(query, status):
        return query.filter_by(status=status)

    @staticmethod
    def scopeActive(query):
        return query.filter(Item.end_at > datetime.utcnow())

    @staticmethod
    def scopeExpired(query):
        return query.filter(Item.end_at <= datetime.utcnow())

    @staticmethod
    def scopeRenewal(query):
        # Logic for renewal scope
        pass

    files = relationship("File", back_populates="item")
    transports = relationship("Transport", back_populates="item")
    accommodations = relationship("Accommodation", back_populates="item")
    excursions = relationship("Excursion", back_populates="item")
    relatedItems = relationship("Item", secondary='related_items', back_populates="relatedItems")

    # Other methods for handling dates, status, and file associations
