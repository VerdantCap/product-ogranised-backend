import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from models.item_model import Item
from schemas.item_schema import ItemCreate, ItemUpdate
from schemas.transport_schema import TransportCreate, TransportUpdate
from schemas.accommodation_schema import AccommodationCreate, AccommodationUpdate
from daos.item_dao import ItemDAO
from daos.transport_dao import TransportDAO
from daos.excursion_dao import ExcursionDAO
from services.auth_service import get_current_user
from utils.route import APIRouter
from enums import ItemSpace, ItemType, ItemStatus
from schemas.auth_schema import User
from schemas.file_schema import FileCreate
from schemas.excursion_schema import ExcursionCreate
from utils.storage import store_file

# Create a new API router for item-related endpoints
item_router = APIRouter()

# Set up a logger for the item controller
logger = logging.getLogger(__name__)

# List all items by owned user
@item_router.get("/list-user")
async def list_items_by_user(
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(100, description="Limit items"),
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    return item_dao.get_by_user(user.id, skip, limit)

# List all items by space
@item_router.get("/list-space")
async def list_items_by_space(
    space: Optional[ItemSpace],
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(100, description="Limit items"),
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    return item_dao.get_by_space(user.active_workspace_id, space, skip, limit)

# List all items by type
@item_router.get("/list-type")
async def list_items_by_type(
    type: Optional[ItemType],
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(100, description="Limit items"),
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    return item_dao.get_by_type(user.active_workspace_id, type, skip, limit)

@item_router.get("/list-status")
async def list_items_by_status(
    status: Optional[ItemStatus],
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(100, description="Limit items"),
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    return item_dao.get_by_status(user.active_workspace_id, status, skip, limit)

@item_router.get("/list-workspace")
async def list_items_by_workspace(
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(100, description="Limit items"),
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    return item_dao.get_by_workspace(user.workspace_id, skip, limit)

@item_router.get("/list-workspace-and-user")
async def list_items_by_workspace_and_user(
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(100, description="Limit items"),
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    return item_dao.get_by_workspace_and_user(user.workspace_id, user.id, skip, limit)

@item_router.get("/list-all")
async def list_items(
    skip: int = Query(0, description="Skip items"),
    limit: int = Query(100, description="Limit items"),
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    return item_dao.get_multi(skip, limit)

# Create a new item
@item_router.post("/create", response_model=Item)
async def create_item(
    item_data: ItemCreate, 
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO)
    ):
    item = Item(
        **item_data.dict(), 
        workspace_id=user.workspace_id,
        owner_id=user.id)
    return item_dao.create_item(item)

# Update an existing item
@item_router.put("/{item_id}/update")
async def update_item(
    item_data: ItemUpdate, 
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO)
    ):
    # item = Item(**item_data.dict())
    item = item_dao.get_by_id(item_data.id)
    if item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this item")
    for key, value in item_data.dict():
        if value is not None:
            setattr(item, key, value)
    return item_dao.update_item(item)

# Delete an item
@item_router.delete("/{item_id}/delete")
async def delete_item(
    item_id: str, 
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO)
    ):
    item = item_dao.get_by_id(item_id)
    if item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this item")
    return item_dao.delete_item(item)

@item_router.post("/soft-delete")
async def soft_delete_item(
    item_id: str, 
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO)
    ):
    item = item_dao.get_by_id(item_id)
    if item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to delete this item")
    return item_dao.soft_delete(item)

@item_router.post("/{item_id}/upload")
async def add_file(
    item_id: str,
    file_data: FileCreate,
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    item = item_dao.get_by_id(item_id)
    if item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to add files to this item")
    
    file_path = await store_file(file_data.file)
    file_create = FileCreate(
        workspace_id=user.active_workspace_id,
        path=file_path,
        type=file_data.file.content_type,
        folder = str(item.space),
        category = str(item.category)
    )
    return item_dao.add_file(item, file_data, user.id)


@item_router.post("/{item_id}/transport")
async def create_transport( 
    item_id: str,
    transport_data: TransportCreate,
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    transport_dao: TransportDAO = Depends(TransportDAO),
    ):
    item = item_dao.get_by_id(item_id)
    if item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to create a transport for this item")
    if item.type != ItemType.TRANSPORT:
        raise HTTPException(status_code=400, detail="Item is not a transport")
    # if item.status != ItemStatus.DONE:
    #     raise HTTPException(status_code=400, detail="Item is not done")


    return transport_dao.create_transport(Item(item_id, user.active_workspace_id, **transport_data.dict()))

@item_router.get("/{item_id}/transport/{transport_id}")
async def update_transport( 
    item_id: str,
    transport_id: str,
    transport_data: TransportUpdate,
    user: User = Depends(get_current_user),
    transport_dao: TransportDAO = Depends(TransportDAO),
    ):
    transport = transport_dao.get_by_id(transport_id)
    if not transport or transport.item_id != item_id:
        raise HTTPException(status_code=404, detail="Transport not found")
    if transport.workspace_id != user.active_workspace_id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this transport")
    return transport_dao.update_transport(Item(item_id, user.active_workspace_id, **transport_data.dict()))

@item_router.post("/{item_id}/accommdation/create")
async def create_accommodation(
    item_id: str,
    accommodation_data: AccommodationCreate,
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    item = item_dao.get_by_id(item_id)
    if item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to create an accommodation for this item")
    if item.type != ItemType.ACCOMMODATION:
        raise HTTPException(status_code=400, detail="Item is not an accommodation")
    return item_dao.create_accommodation(Item(item_id, user.active_workspace_id, **accommodation_data.dict()))

@item_router.put("/{item_id}/accommdation/{accommodation_id}/update")
async def update_accommodation(
    item_id: str,
    accommodation_id: str,
    accommodation_data: AccommodationUpdate,
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO),
    ):
    accommodation = item_dao.get_accommodation(accommodation_id)
    if not accommodation or accommodation.item_id != item_id:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    if accommodation.workspace_id != user.active_workspace_id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this accommodation")
    return item_dao.update_accommodation(Item(item_id, user.active_workspace_id, **accommodation_data.dict()))

@item_router.post("/{item_id}/excursion/create")
async def create_excursion(
    item_id: str,
    excursion_data: ExcursionCreate,
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO),
    item_dao: ItemDAO = Depends(ItemDAO)
    ):
    item = item_dao.get_by_id(item_id)
    if item.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to create an excursion for this item")
    if item.type != ItemType.EXCURSION:
        raise HTTPException(status_code=400, detail="Item is not an excursion")
    return excursion_dao.create_excursion(Item(item_id, user.active_workspace_id, **excursion_data.dict()))


@item_router.put("/{item_id}/excursions/{excursion_id}/update")
async def update_excursion(
    item_id: str,
    excursion_id: str,
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO)
    ):
    excursion = excursion_dao.get_by_id(excursion_id)
    if not excursion or excursion.item_id != item_id:
        raise HTTPException(status_code=404, detail="Excursion not found")
    if excursion.workspace_id != user.active_workspace_id:
        raise HTTPException(status_code=403, detail="Not authorized")


# Related Items Routes
@item_router.post("/{item_id}/related/{related_id}")
async def add_related_item(
    item_id: str,
    related_id: str,
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO)
    ):
    item  = item_dao.get_by_id(item_id)
    if not item or item.workspace_id != user.active_workspace_id:
        raise HTTPException(status_code=404, detail="Item not found")

    related_item = item_dao.get_by_id(related_id)
    if not related_item or related_item.workspace_id != user.active_workspace_id:
        raise HTTPException(status_code=404, detail="Related item not found")
    item.related_items.append(related_item)
    item_dao.update_item(item)

@item_router.delete("/{item_id}/related/{related_id}")
async def remove_related_item(
    item_id: str,
    related_id: str,
    user: User = Depends(get_current_user),
    item_dao: ItemDAO = Depends(ItemDAO)
    ):
    item  = item_dao.get_by_id(item_id)
    if not item or item.workspace_id != user.active_workspace_id:
        raise HTTPException(status_code=404, detail="Item not found")

    related_item = item_dao.get_by_id(related_id)
    if not related_item or related_item.workspace_id != user.active_workspace_id:
        raise HTTPException(status_code=404, detail="Related item not found")
    item.related_items.remove(related_item)
    item_dao.update_item(item)  