from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ID(BaseModel):
    id: Optional[str] = None


class Page(BaseModel, Generic[T]):
    items: List[T]
    page: int
    size: int
    total: int
    pages: int
