from pydantic import BaseModel 
from typing import Optional, List
from models.file_model import File
from models.transpot_model import Transport
from models.accommodation_model import Accommodation
from models.excursion_model import Excursion
from models.item_model import Item
from enums import ItemSpace, ItemType

class Item(BaseModel):
    workspace_id: str
    owner_id: str
    space: ItemSpace
    type: ItemType
    title: str
    description: Optional[str]
    fields: Optional[dict]
    files: List[File]
    related_items: List[Item] = []
    transports: List[Transport] = []
    accommodations: List[Accommodation] = []
    excursions: List[Excursion] = []

class ItemCreate(BaseModel):
    workspace_id: str
    space: ItemSpace
    type: ItemType
    title: str
    description: Optional[str]
    fields: Optional[dict]

class ItemUpdate(BaseModel):
    space: Optional[ItemSpace]
    type: Optional[ItemType]
    title: Optional[str]
    description: Optional[str]
    fields: Optional[dict]