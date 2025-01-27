from sqlalchemy import Column, String, Table, ForeignKey
from base import Base

item_association = Table(  
    'item_association', Base.metadata,  
    Column('item_id', String, ForeignKey('items.id')),  
    Column('related_item_id', String, ForeignKey('items.id'))  
)

user_workspace = Table(
    'user_workspace',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('workspace_id', Integer, ForeignKey('workspaces.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)