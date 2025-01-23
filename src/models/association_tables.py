from sqlalchemy import Column, String, DateTime, Table, ForeignKey
from sqlalchemy.sql import func  
from base import Base

item_association = Table(  
    'item_association', Base.metadata,  
    Column('item_id', String, ForeignKey('items.id')),  
    Column('related_item_id', String, ForeignKey('items.id'))  
)  