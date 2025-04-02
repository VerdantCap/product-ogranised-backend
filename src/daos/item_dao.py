import logging
from fastapi import Depends
from typing import Optional, List
from sqlalchemy import select
from models.item_model import Item
from models.file_model import File
from schemas import FileCreate
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime
from enums import ItemSpace, ItemType, ItemStatus  

# Set up a logger for the FileDAO
logger = logging.getLogger(__name__)

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

    async def create_item(self, item: Item) -> Item:
        """
        Create a new item record in the database.

        Returns the created Item object.
        """
        self.db.add(item)
        await self.db.commit()
        return item
    
    async def get_item_by_id(self, item_id: int) -> Item:
        """
        Retrieve an item record by its ID.

        Returns the Item object if found, otherwise None.
        """
        result = await self.db.execute(
            select(Item).filter(Item.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def update_item(self, item: Item) -> Item:
        """
        Update an existing item record in the database.

        Returns the updated Item object.
        """
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item
    
    async def delete_item(self, item: Item) -> None:
        """
        Delete an item record from the database.
        """
        await self.db.delete(item)
        await self.db.commit()

    async def get_by_id(self, item_id: int) -> Optional[Item]:
        """
        Retrieve an item record by its ID.

        Returns the Item object if found, otherwise None.
        """
        result = await self.db.execute(
            select(Item).filter(Item.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Item]: 
        """
        Retrieve item records by user ID with pagination.

        Returns a list of Item objects.
        """
        result = await self.db.execute(
            select(Item)
            .filter(Item.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve item records by workspace ID with pagination.

        Returns a list of Item objects.
        """
        result = await self.db.execute(
            select(Item)
            .filter(
                Item.workspace_id == workspace_id
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_space(self, space: ItemSpace, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve item records by space and workspace ID.

        Returns a list of Item objects.
        """
        result = await self.db.execute(
            select(Item)
            .filter(
                Item.space == space,
                Item.workspace_id == workspace_id
            )
        )
        return result.scalars().all()

    async def get_by_type(self, type: ItemType, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve item records by type and workspace ID.

        Returns a list of Item objects.
        """
        result = await self.db.execute(
            select(Item)
            .filter(
                Item.type == type,
                Item.workspace_id == workspace_id
            )
        )
        return result.scalars().all()

    async def get_by_status(self, status: ItemStatus, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve item records by status and workspace ID.

        Returns a list of Item objects.
        """
        query = select(Item).filter(
            Item.workspace_id == workspace_id
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
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_workspace_and_user(self, workspace_id: str, user_id: str, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve item records by workspace ID and user ID with pagination.

        Returns a list of Item objects.
        """
        result = await self.db.execute(
            select(Item)
            .filter(
                Item.workspace_id == workspace_id,
                Item.user_id == user_id
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Item]:
        """
        Retrieve multiple item records with pagination.

        Returns a list of Item objects.
        """
        result = await self.db.execute(
            select(Item)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def soft_delete(self, item: Item) -> Item:
        """
        Soft delete an item record.  
        Returns the updated Item object.
        """

        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def add_related_item(self, item: Item, related_item: Item):
        """
        Add a related item to an item.

        Returns the updated Item object.
        """
        item.related_items.append(related_item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def remove_related_item(self, item: Item, related_item: Item):
        """
        Remove a related item from an item.

        Returns the updated Item object.
        """
        item.related_items.remove(related_item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def add_file(self, item: Item, file_create: FileCreate, owner_id: str) -> File:
        """
        Add a file to an item.

        Returns the created File object.
        """
        file_create['owner_id'] = owner_id
        file_obj = File(**file_create)
        item.files.append(file_obj)
        await self.db.commit()
        await self.db.refresh(file_obj)
        return file_obj
