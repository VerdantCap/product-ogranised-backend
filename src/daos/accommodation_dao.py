import logging
from fastapi import Depends
from typing import List
from models.accommodation_model import Accommodation
from db.postgres import AsyncSession, get_postgres_session

# Set up a logger for the AccommodationDAO
logger = logging.getLogger(__name__)

class AccommodationDAO:
    """
    Data Access Object for Accommodation.

    This class provides methods to perform CRUD operations on Accommodation objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    def create_accommodation(self, accommodation: Accommodation):
        """
        Create a new accommodation record in the database.

        Returns the created Accommodation object.
        """
        self.db.add(accommodation)
        self.db.commit()
        return accommodation
    
    def update_accommodation(self, accommodation: Accommodation):
        """
        Update an existing accommodation record in the database.

        Returns the updated Accommodation object.
        """
        self.db.add(accommodation)
        self.db.commit()
        return accommodation

    def delete_accommodation(self, accommodation: Accommodation):
        """
        Delete an accommodation record from the database.

        Returns the deleted Accommodation object.
        """
        self.db.delete(accommodation)
        self.db.commit()
        return accommodation
    
    def get_by_id(self, accommodation_id: str) -> Accommodation:
        """
        Retrieve an accommodation record by its ID.

        Returns the Accommodation object if found, otherwise None.
        """
        return self.db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

    def get_by_item(self, item_id: str) -> List[Accommodation]:
        """
        Retrieve accommodation records by item ID.

        Returns a list of Accommodation objects.
        """
        return self.db.query(Accommodation).filter(Accommodation.item_id == item_id).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100):
        """
        Retrieve multiple accommodation records with pagination.

        Returns a list of Accommodation objects.
        """
        return self.db.query(Accommodation).offset(skip).limit(limit).all()
