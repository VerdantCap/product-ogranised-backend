import logging
from typing import Any, Optional, Tuple, List
from fastapi import Depends
from models.user_model import User
from models.workspace_model import Workspace
from models.association_tables import user_workspace
from sqlalchemy import and_, delete, exists, select, or_, update
from datetime import datetime

from db.postgres import AsyncSession, get_postgres_session

# Set up a logger for the AuthDAO
logger = logging.getLogger(__name__)

class AuthDAO:
    """
    Data Access Object for User Authentication.

    This class provides methods to perform CRUD operations on User objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    def create_user(self, user: User) -> None:
        """
        Create a new user record in the database.
        """
        self.db.add(user)

    async def update_user(self, user: User) -> User:
        """
        Update an existing user record in the database.

        Returns the updated User object.
        """
        self.db.add(user)
        await self.db.commit()
        return user
    
    async def update_user_name(self, user: User, new_name: str) -> None:
        """
        Update the user's name in the database.
        """
        query = (
            update(User)
            .where(User.id == user.id)
            .values(user_name=new_name)
        )
        await self.db.execute(query)

    async def update_user_email(self, user: User, new_email: str) -> None:
        """
        Update the user's email in the database.
        """
        query = (
            update(User)
            .where(User.id == user.id)
            .values(email=new_email)
        )
        await self.db.execute(query)

    async def verify_user_email(self, user: User) -> None:
        """
        Set the user's email as verified in the database.
        """
        query = (
            update(User)
            .where(User.id == user.id)
            .values(is_email_verified=True)
        )
        await self.db.execute(query)
        await self.db.commit()

    async def update_user_password(self, user: User, new_password: str) -> None:
        """
        Update the user's password in the database.
        """
        query = (
            update(User)
            .where(User.id == user.id)
            .values(password=new_password)
        )
        await self.db.execute(query)

    async def update_oauth_tokens(
        self, 
        user: User, 
        access_token: str, 
        refresh_token: Optional[str],
        token_expires_at: Optional[datetime]
    ) -> None:
        """
        Update the user's OAuth tokens in the database.
        """
        values = {
            "access_token": access_token,
            "token_expires_at": token_expires_at
        }
        if refresh_token:
            values["refresh_token"] = refresh_token

        query = (
            update(User)
            .where(User.id == user.id)
            .values(**values)
        )
        await self.db.execute(query)

    async def delete_user_by_id(self, user_id: str) -> None:
        """
        Delete a user record from the database by user ID.
        """
        query = delete(User).where(User.id == user_id)
        await self.db.execute(query)

    async def delete_user_by_email(self, email: str) -> None:
        """
        Delete a user record from the database by email.
        """
        query = delete(User).where(User.email == email)
        await self.db.execute(query)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user record by user ID.

        Returns the User object if found, otherwise None.
        """
        query = select(User).where(
            User.id == user_id
        )
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user record by email.

        Returns the User object if found, otherwise None.
        """
        query = (
            select(User)
            .where(
                and_(User.email == email)
            )
            .order_by(User.created_at.desc())
        )
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result

    async def get_user(self, email: str, user_id: str) -> Optional[User]:
        """
        Retrieve a user record by both email and user ID.
        This is used for token validation to ensure both email and ID match.
        
        Returns the User object if found, otherwise None.
        """
        query = select(User).where(
            and_(
                User.email == email,
                User.id == user_id
            )
        )
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result
    
    async def get_user_by_google_sub(self, google_sub: str) -> Optional[User]:
        """
        Retrieve a user record by Google subscription ID.
        Returns the User object if found, otherwise None.
        """
        query = select(User).where(User.google_sub == google_sub)
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result

    async def get_user_by_apple_sub(self, apple_sub: str) -> Optional[User]:
        """
        Retrieve a user record by Apple subscription ID.
        Returns the User object if found, otherwise None.
        """
        query = select(User).where(User.apple_sub == apple_sub)
        result: Optional[User] = (await self.db.execute(query)).scalars().first()
        return result

    async def get_user_by_oauth_provider(self, provider: str, sub: str) -> Optional[User]:
        """
        Retrieve a user record by OAuth provider and subscription ID.
        Returns the User object if found, otherwise None.
        """
        if provider == "google":
            return await self.get_user_by_google_sub(sub)
        elif provider == "apple":
            return await self.get_user_by_apple_sub(sub)
        return None

    async def get_email_by_user_id(self, user_id: str) -> Optional[str]:
        """
        Retrieve the email address of a user by user ID.

        Returns the email address if found, otherwise None.
        """
        query = select(User.email).where(User.id == user_id)
        result = await self.db.execute(query)
        email = result.scalar()
        return email if isinstance(email, str) else None

    async def get_user_email_and_name_by_id(
        self, user_id: str
    ) -> Optional[Tuple[Optional[str], Optional[str]]]:
        """
        Retrieve the email address and name of a user by user ID.

        Returns a tuple containing the email address and name if found, otherwise None.
        """
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
        """
        Retrieve the email address and email subscription settings of a user by user ID.

        Returns a tuple containing the email address and subscription settings.
        """
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
        """
        Check if an email address exists in the database.

        Returns True if the email exists, otherwise False.
        """
        query = select(
            exists().where(
                and_(
                    User.email == user_email
                )
            )
        )
        return (await self.db.execute(query)).scalar()
    
    async def get_oauth_users(self, provider: Optional[str] = None) -> List[User]:
        """
        Retrieve users with OAuth credentials.
        Returns a list of User objects.
        """
        conditions = []
        if provider == "google":
            conditions.append(User.google_sub.isnot(None))
        elif provider == "apple":
            conditions.append(User.apple_sub.isnot(None))
        else:
            conditions.append(or_(
                User.google_sub.isnot(None),
                User.apple_sub.isnot(None)
            ))
        
        query = select(User).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalars().all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Retrieve multiple user records with pagination.

        Returns a list of User objects.
        """
        return self.db.query(User).offset(skip).limit(limit).all()

    async def join_workspace(self, user: User, workspace: Workspace):  
        """
        Add a user to a workspace.

        Commits the change to the database.
        """
        # Check if the relationship already exists
        query = select(exists().where(
            and_(
                user_workspace.c.user_id == user.id,
                user_workspace.c.workspace_id == workspace.id
            )
        ))
        result = await self.db.execute(query)
        already_joined = result.scalar()

        if not already_joined:
            # Insert the relationship directly using the association table
            query = user_workspace.insert().values(
                user_id=user.id,
                workspace_id=workspace.id
            )
            await self.db.execute(query)
            await self.db.commit()

    async def leave_workspace(self, user: User, workspace: Workspace):  
        """
        Remove a user from a workspace.

        Commits the change to the database.
        """
        # Delete the relationship directly from the association table
        query = delete(user_workspace).where(
            and_(
                user_workspace.c.user_id == user.id,
                user_workspace.c.workspace_id == workspace.id
            )
        )
        await self.db.execute(query)
        await self.db.commit()

    async def set_active_workspace(self,user: User, workspace: Optional[Workspace] = None) -> User:  
        """
        Set the active workspace for a user.

        Commits the change to the database.
        """
        query = (
            update(User)
            .where(User.id == user.id)
            .values(active_workspace_id=workspace.id)
        )
        await self.db.execute(query)
        await self.db.commit()

        return user
        
    async def refresh_database(self, user: Optional[User] = None) -> None:
        """
        Refresh the database session to ensure it has the latest data.
        
        If a user object is provided, refreshes that specific user object.
        Otherwise, just refreshes the database session.
        
        This is useful when data might have been modified by another session
        or when you need to ensure you have the latest state from the database.
        """
        try:
            if user:
                await self.db.refresh(user)
                logger.info(f"Refreshed user data for user ID: {user.id}")
            else:
                # Just refresh the session
                await self.db.flush()
                logger.info("Database session refreshed")
        except Exception as e:
            logger.error(f"Error refreshing database: {e}")
            raise
