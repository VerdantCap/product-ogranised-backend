from sqlalchemy import Column, String, Table, ForeignKey, DateTime
from base import Base
from datetime import datetime

item_association = Table(  
    'item_association', Base.metadata,  
    Column('item_id', String, ForeignKey('items.id')),  
    Column('related_item_id', String, ForeignKey('items.id'))  
)

user_workspace = Table(
    'user_workspace',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('workspace_id', String, ForeignKey('workspaces.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)