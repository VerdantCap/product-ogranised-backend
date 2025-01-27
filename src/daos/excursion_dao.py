import logging
from fastapi import Depends
from typing import List
from models.excursion_model import Excursion
from db.postgres import AsyncSession, get_postgres_session

# Set up a logger for the ExcursionDAO
logger = logging.getLogger(__name__)

class ExcursionDAO:
    """
    Data Access Object for Excursion.

    This class provides methods to perform CRUD operations on Excursion objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    def create_excursion(self, excursion: Excursion):
        """
        Create a new excursion record in the database.

        Returns the created Excursion object.
        """
        self.db.add(excursion)
        self.db.commit()
        self.db.refresh(excursion)
        return excursion
    
    def update_excursion(self, excursion: Excursion):
        """
        Update an existing excursion record in the database.

        Returns the updated Excursion object.
        """
        self.db.add(excursion)
        self.db.commit()
        self.db.refresh(excursion)
        return 
    
    def delete_excursion(self, excursion: Excursion):
        """
        Delete an excursion record from the database.

        Returns the deleted Excursion object.
        """
        self.db.delete(excursion)
        self.db.commit()
        return
    
    def get_by_id(self, excursion_id: str) -> Excursion:
        """
        Retrieve an excursion record by its ID.

        Returns the Excursion object if found, otherwise None.
        """
        return self.db.query(Excursion).filter(Excursion.id == excursion_id).first()

    def get_by_item(self, item_id: str) -> List[Excursion]:
        """
        Retrieve excursion records by item ID.

        Returns a list of Excursion objects.
        """
        return self.db.query(Excursion).filter(Excursion.item_id == item_id).all()
    
    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Excursion]:
        """
        Retrieve multiple excursion records with pagination.

        Returns a list of Excursion objects.
        """
        return self.db.query(Excursion).offset(skip).limit(limit).all()
