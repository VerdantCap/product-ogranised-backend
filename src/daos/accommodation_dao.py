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

    def get_by_item( self, item_id: str) -> List[Accommodation]:
        return self.db.query(Accommodation).filter(Accommodation.item_id == item_id).all()