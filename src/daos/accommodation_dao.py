import logging
from fastapi import Depends
from typing import List
from models.accommodation_model import Accommodation
from db.postgres import AsyncSession, get_postgres_session


logger = logging.getLogger(__name__)

class AccommodationDAO:
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db

    def create_accommodation(self, accommodation: Accommodation):
        self.db.add(accommodation)
        self.db.commit()
        return accommodation
    
    def update_accommodation(self, accommodation: Accommodation):
        self.db.add(accommodation)
        self.db.commit()
        return accommodation

    def delete_accommodation(self, accommodation: Accommodation):
        self.db.delete(accommodation)
        self.db.commit()
        return accommodation
    
    def get_by_id(self, accommodation_id: str) -> Accommodation:
        return self.db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

    def get_by_item( self, item_id: str) -> List[Accommodation]:
        return self.db.query(Accommodation).filter(Accommodation.item_id == item_id).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100):
        return self.db.query(Accommodation).offset(skip).limit(limit).all()