import logging
from fastapi import Depends
from typing import List
from models.transpot_model import Transport
from db.postgres import AsyncSession, get_postgres_session

# Set up a logger for the TransportDAO
logger = logging.getLogger(__name__)

class TransportDAO:
    """
    Data Access Object for Transport.

    This class provides methods to perform CRUD operations on Transport objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    def create_transport(self, transport: Transport) -> Transport:
        """
        Create a new transport record in the database.

        Returns the created Transport object.
        """
        self.db.add(transport)
        self.db.commit()
        return transport

    def update_transport(self, transport: Transport) -> Transport:
        """
        Update an existing transport record in the database.

        Returns the updated Transport object.
        """
        self.db.add(transport)
        self.db.commit()
        return transport

    def delete_transport(self, transport: Transport) -> Transport:
        """
        Delete a transport record from the database.

        Returns the deleted Transport object.
        """
        self.db.delete(transport)
        self.db.commit()
        return transport

    def get_by_id(self, transport_id: str) -> Transport:
        """
        Retrieve a transport record by its ID.

        Returns the Transport object if found, otherwise None.
        """
        return self.db.query(Transport).filter(Transport.id == transport_id).first()

    def get_by_item(self, item_id: str) -> List[Transport]:
        """
        Retrieve transport records by item ID.

        Returns a list of Transport objects.
        """
        return self.db.query(Transport).filter(
            Transport.item_id == item_id
        ).all()
    
    def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Transport]:
        """
        Retrieve transport records by workspace ID with pagination.

        Returns a list of Transport objects.
        """
        return self.db.query(Transport).filter(
            Transport.workspace_id == workspace_id
        ).offset(skip).limit(limit).all()
    
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Transport]:
        """
        Retrieve transport records by user ID with pagination.

        Returns a list of Transport objects.
        """
        return self.db.query(Transport).filter(
            Transport.user_id == user_id
        ).offset(skip).limit(limit).all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Transport]:
        """
        Retrieve multiple transport records with pagination.

        Returns a list of Transport objects.
        """
        return self.db.query(Transport).offset(skip).limit(limit).all()
