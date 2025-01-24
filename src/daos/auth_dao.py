import logging
from typing import Any, Optional, Tuple, List
from fastapi import Depends
from models.user_model import User
from models.workspace_model import Workspace
from sqlalchemy import and_, delete, exists, select, true, update

from db.postgres import AsyncSession, get_postgres_session

logger = logging.getLogger(__name__)


class AuthDAO:
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db

    def create_user(self, user: User) -> None:
        self.db.add(user)

    async def update_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        return user
    
    async def update_user_name(self, user: User, new_name: str) -> None:
        query = (
            update(User)
            .where(User.id == user.id)
            .values(user_name=new_name)
        )
        await self.db.execute(query)

    async def update_user_email(self, user: User, new_email: str) -> None:
        query = (
            update(User)
            .where(User.id == user.id)
            .values(email=new_email)
        )
        await self.db.execute(query)

    async def update_user_password(self, user: User, new_password: str) -> None:
        query = (
            update(User)
            .where(User.id == user.id)
            .values(password=new_password)
        )
        await self.db.execute(query)

    async def delete_user_by_id(self, user_id: str) -> None:
        query = delete(User).where(User.id == user_id)
        await self.db.execute(query)

    async def delete_user_by_email(self, email: str) -> None:
        query = delete(User).where(User.email == email)
        await self.db.execute(query)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        query = select(User).where(
            User.id == user_id
        )
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = (
            select(User)
            .where(
                and_(User.email == email)
            )
            .order_by(User.created_at.desc())
        )
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result
    
    async def get_user_by_google_sub(self, google_sub: str) -> Optional[User]:
        query = select(User).where(User.google_sub == google_sub)
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result

    async def get_email_by_user_id(self, user_id: str) -> Optional[str]:
        query = select(User.email).where(User.id == user_id)
        result = await self.db.execute(query)
        email = result.scalar()
        return email if isinstance(email, str) else None

    async def get_user_email_and_name_by_id(
        self, user_id: str
    ) -> Optional[Tuple[Optional[str], Optional[str]]]:
        query = select(User.email, User.user_name).where(
            User.id == user_id
        )
        result = await self.db.execute(query)
        email, name = result.first()
        return (
            email if isinstance(email, str) else None,
            name if isinstance(name, str) else None,
        )

    async def get_email_and_im_email_settings_by_user_id(
        self, user_id: str
    ) -> Tuple[Optional[str], bool]:
        query = select(User.email, User.is_im_email_subscribed).where(
            User.id == user_id
        )
        result = await self.db.execute(query)
        email, is_im_email_subscribed = result.first()
        return (
            email if isinstance(email, str) else None,
            is_im_email_subscribed
            if isinstance(is_im_email_subscribed, bool)
            else True,
        )

    async def check_email_exists(self, user_email: str) -> Any:
        query = select(
            exists().where(
                and_(
                    User.email == user_email
                )
            )
        )
        return (await self.db.execute(query)).scalar()
    
    def get_oauthed(self, driver: Optional[str] = None) -> List[User]:
        query = self.db.query(User).filter(User.oauth_id.isnot(None))
        if driver:
            query = query.filter(User.oauth_driver == driver)
        return query.all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def join_workspace(self, user: User, workspace: Workspace):  
        if workspace not in user.workspaces:  
            user.workspaces.append(workspace)  
        self.db.commit()  

    def leave_workspace(self, user: User, workspace: Workspace):  
        if workspace in user.workspaces:  
            user.workspaces.remove(workspace)  
        self.db.commit() 