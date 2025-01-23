import logging
from fastapi import Depends
from typing import List
from models.transpot_model import Transport
from db.postgres import AsyncSession, get_postgres_session

logger = logging.getLogger(__name__)

class TransportDAO:
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db

    def get_by_item( self, item_id: str) -> List[Transport]:
        return self.db.query(Transport).filter(
            Transport.item_id == item_id
        ).all()