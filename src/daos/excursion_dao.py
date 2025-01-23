import logging
from fastapi import Depends
from typing import List
from models.excursion_model import Excursion
from db.postgres import AsyncSession, get_postgres_session


logger = logging.getLogger(__name__)

class ExcursionDAO:
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db

    def get_by_item(self, item_id: str) -> List[Excursion]:
        return self.db.query(Excursion).filter(Excursion.item_id == item_id).all()