import logging
from fastapi import Depends
from typing import Optional, List
from models.item_model import Item
from models.file_model import File
from schemas.file_schema import FileCreate
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime
from enums import ItemSpace, ItemType, ItemStatus  

class ItemDAO:
    """
    Data Access Object for Item.

    This class provides methods to perform CRUD operations on Item objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    def create_item(self, item: Item) -> Item:
        """
        Create a new item record in the database.

        Returns the created Item object.
        """
        self.db.add(item)
        self.db.commit()
        return item
    
    def get_item_by_id(self, item_id: int) -> Item:
        """
        Retrieve an item record by its ID.

        Returns the Item object if found, otherwise None.
        """
        return self.db.query(Item).filter(Item.id == item_id).first()
    
    def update_item(self, item: Item) -> Item:
        """
        Update an existing item record in the database.

        Returns the updated Item object.
        """
        self.db.add(item)
        self.db.commit()
        return item
    
    def delete_item(self, item: Item) -> None:
        """
        Delete an item record from the database.
        """
        self.db.delete(item)
        self.db.commit()

    def get_by_id(self, item_id: int) -> Optional[Item]:
        """
        Retrieve an item record by its ID.

        Returns the Item object if found, otherwise None.
        """
        return self.db.query(Item).filter(Item.id == item_id).first()
    
    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Item]: 
        """
        Retrieve item records by user ID with pagination.

        Returns a list of Item objects.
        """
        return self.db.query(Item).filter(Item.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve item records by workspace ID with pagination.

        Returns a list of Item objects.
        """
        return self.db.query(Item).filter(
            Item.workspace_id == workspace_id,
            Item.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()

    def get_by_space(self, space: ItemSpace, workspace_id: str) -> List[Item]:
        """
        Retrieve item records by space and workspace ID.

        Returns a list of Item objects.
        """
        return self.db.query(Item).filter(
            Item.space == space,
            Item.workspace_id == workspace_id,
            Item.deleted_at.is_(None)
        ).all()

    def get_by_type(self, type: ItemType, workspace_id: str) -> List[Item]:
        """
        Retrieve item records by type and workspace ID.

        Returns a list of Item objects.
        """
        return self.db.query(Item).filter(
            Item.type == type,
            Item.workspace_id == workspace_id,
            Item.deleted_at.is_(None)
        ).all()

    def get_by_status(self, status: ItemStatus, workspace_id: str) -> List[Item]:
        """
        Retrieve item records by status and workspace ID.

        Returns a list of Item objects.
        """
        query = self.db.query(Item).filter(
            Item.workspace_id == workspace_id,
            Item.deleted_at.is_(None)
        )
        
        if status == ItemStatus.ACTIVE:
            query = query.filter(
                Item.start_at <= datetime.now(),
                Item.end_at >= datetime.now()
            )
        elif status == ItemStatus.EXPIRED:
            query = query.filter(Item.end_at < datetime.now())
        elif status == ItemStatus.RENEWAL:
            query = query.filter(Item.start_at > datetime.now())
            
        return query.all()

    def get_by_workspace_and_user(self, workspace_id: str, user_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve item records by workspace ID and user ID with pagination.

        Returns a list of Item objects.
        """
        return self.db.query(Item).filter(
            Item.workspace_id == workspace_id,
            Item.user_id == user_id
        ).offset(skip).limit(limit).all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve multiple item records with pagination.

        Returns a list of Item objects.
        """
        return self.db.query(Item).offset(skip).limit(limit).all()

    def soft_delete(self, item: Item) -> Item:
        """
        Soft delete an item record by setting its deleted_at timestamp.

        Returns the updated Item object.
        """
        item.deleted_at = datetime.now()
        self.db.commit()
        self.db.refresh(item)
        return item

    def add_related_item(self, item: Item, related_item: Item):
        """
        Add a related item to an item.

        Returns the updated Item object.
        """
        item.related_items.append(related_item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_related_item(self, item: Item, related_item: Item):
        """
        Remove a related item from an item.

        Returns the updated Item object.
        """
        item.related_items.remove(related_item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def add_file(self, item: Item, file_create: FileCreate, owner_id: str) -> File:
        """
        Add a file to an item.

        Returns the created File object.
        """
        file_create['owner_id'] = owner_id
        file_obj = File(**file_create)
        item.files.append(file_obj)
        self.db.commit()
        self.db.refresh(file_obj)
        return file_obj
