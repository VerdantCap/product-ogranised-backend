from sqlalchemy import Column, String, Table, ForeignKey
from base import Base

item_association = Table(  
    'item_association', Base.metadata,  
    Column('item_id', String, ForeignKey('items.id')),  
    Column('related_item_id', String, ForeignKey('items.id'))  
)  