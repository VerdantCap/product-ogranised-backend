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

    def create_excursion(self, excursion: Excursion):
        self.db.add(excursion)
        self.db.commit()
        self.db.refresh(excursion)
        return excursion
    
    def update_excursion(self, excursion: Excursion):
        self.db.add(excursion)
        self.db.commit()
        self.db.refresh(excursion)
        return 
    
    def delete_excursion(self, excursion: Excursion):
        self.db.delete(excursion)
        self.db.commit()
        return
    
    def get_by_id(self, excursion_id: str) -> Excursion:
        return self.db.query(Excursion).filter(Excursion.id == excursion_id).first()

    def get_by_item(self, item_id: str) -> List[Excursion]:
        return self.db.query(Excursion).filter(Excursion.item_id == item_id).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Excursion]:
        return self.db.query(Excursion).offset(skip).limit(limit).all()