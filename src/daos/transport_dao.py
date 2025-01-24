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

    def create_transport(self, transport: Transport) -> Transport:
        self.db.add(transport)
        self.db.commit()
        return transport

    def update_transport(self, transport: Transport) -> Transport:
        self.db.add(transport)
        self.db.commit()
        return transport

    def delete_transport(self, transport: Transport) -> Transport:
        self.db.delete(transport)
        self.db.commit()
        return transport

    def get_by_id(self, transport_id: str) -> Transport:
        return self.db.query(Transport).filter(Transport.id == transport_id).first()

    def get_by_item( self, item_id: str) -> List[Transport]:
        return self.db.query(Transport).filter(
            Transport.item_id == item_id
        ).all()
    
    def get_by_workspace( self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Transport]:
        return self.db.query(Transport).filter(
            Transport.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()
    
    def get_by_user( self, user_id: str, skip: int = 0, limit: int = 100) -> List[Transport]:
        return self.db.query(Transport).filter(
            Transport.user_id == user_id
        ).offset(skip).limit(limit).all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Transport]:
        return self.db.query(Transport).offset(skip).limit(limit).all()