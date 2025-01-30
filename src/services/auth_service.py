import logging
import re
import uuid
import httpx
import jwt
from typing import Annotated, Any, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models.user_model import User
from utils.auth_bearer import JWTBearer

from utils.exceptions import (
    DiffPwdException,
    DuplicateException,
    GoogleAuthException,
    IncorrectPwdException,
    LoginExpiredException,
    NotFoundException,
    TokenException
)
from utils.auth_bearer import JWTBearer
from daos.auth_dao import AuthDAO
from schemas import CreateUserIn
from utils.security import PasswordHashing
from config import settings
from db.postgres import AsyncSession, get_postgres_session
from utils.helpers import normalize_email
from datetime import datetime

# OAuth2 scheme for password-based authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.ROOT_PATH}/auth/login", auto_error=False
)

# Set up a logger for the AuthService
logger = logging.getLogger(__name__)

class AuthService:
    """
    Service class for handling user authentication and authorization.

    This class provides methods for user registration, login, token generation, and password management.
    """

    def __init__(
        self,
        auth_dao: AuthDAO = Depends(AuthDAO),
    ):
        # Initialize the AuthService with an AuthDAO instance
        self.auth_dao = auth_dao

    async def create_user(
        self,
        create_user_in: CreateUserIn,
    ) -> str:
        """
        Create a new user in the system.

        Returns the user ID of the newly created user.
        """
        create_user_in.email = normalize_email(create_user_in.email)

        if await self.auth_dao.check_email_exists(create_user_in.email):
            logger.warning("Email already registered")
            raise DuplicateException("Email already registered")

        password_check(create_user_in.password)

        hashed_password = PasswordHashing.create_hashed_password(
            create_user_in.password
        )

        create_user_in.password = hashed_password

        user_id = f"user_{str(uuid.uuid4())}"
        user = User(
            email=create_user_in.email,
            password=create_user_in.password,
            name=create_user_in.name,
            id=user_id
        )
        self.auth_dao.create_user(user)
        await self.auth_dao.db.commit()

        return user_id

    async def handle_login(
        self,
        email: str,
        password: str,
    ) -> Any:
        """
        Handle user login by verifying credentials.

        Returns an access token if login is successful.
        """
        email = normalize_email(email)

        user = await self.auth_dao.get_user_by_email(email)

        if user is None:
            logger.warning("User not found")
            raise NotFoundException("User not found")

        if PasswordHashing.verify_password(
            password, user.password if user.password else ""
        ):
            return await self.generate_access_token(user)
        else:
            logger.warning("Incorrect password")
            raise IncorrectPwdException("Incorrect password")

    async def generate_access_token(self, user: User) -> str:
        """
        Generate a JWT access token for the user.

        Returns the generated JWT token.
        """
        profile = dict(
            avatar_url=user.avatar_url,
            name=user.name,
            country=user.country,
            city=user.city,
        )
        payload: Dict[str, Any] = {
            "user_id": user.id,
            "email": user.email
        }
        jwt_expiry_minutes = settings.JWT_EXPIRY_DAYS * 24 * 60
        jwt_token: str = JWTBearer.generate_jwt(
            payload=payload, expiry_minutes=jwt_expiry_minutes
        )

        return jwt_token

    async def generate_otp_verification_token(self, email: str) -> str:
        """
        Generate a JWT token for OTP verification.

        Returns the generated JWT token.
        """
        email = normalize_email(email)

        payload = {"email": email, "type": "otp"}
        expiry_minutes = 30
        jwt_token: str = JWTBearer.generate_jwt(
            payload=payload, expiry_minutes=expiry_minutes
        )

        return jwt_token

    async def delete_user(self, user_email: str) -> None:
        """
        Delete a user from the system by email.
        """
        user_email = normalize_email(user_email)

        await self.auth_dao.delete_user_by_email(user_email)
        await self.auth_dao.db.commit()

    # def refresh_google_token(self, user: User):
    #     if not user.refresh_token:
    #         return None
        
    #     credentials = Credentials(
    #         token = user.access_token,
    #         refresh_token = user.refresh_token,
    #         token_uri = settings.GOOGLE_TOKEN_URL,
    #         client_id = settings.GOOGLE_CLIENT_ID,
    #         client_secret = settings.GOOGLE_CLIENT_SECRET,
    #     )

    #     if credentials.expired:
    #         credentials = credentials.refresh()
    #         self.auth_dao.update(
    #             user,credentials.token,
    #             datetime.utcnow() + timedelta(seconds=credentials.expiry.second)
    #         )
            
    #     return credentials
    
    # def get_google_calendar_events(
    #     self,
    #     user: User,
    #     start_date: datetime,
    #     end_date: datetime,
    # ):
    #     credentials = self.refresh_google_token(user)
    #     if not credentials:
    #         return []

    #     try:
    #         service = build(
    #             "calendar",
    #             "v3",
    #             credentials=credentials
    #         )

    #         event_result = service.events().list(
    #             calendarId="primary",
    #             timeMin=start_date.isoformat() + 'Z',
    #             timeMax=end_date.isoformat() + 'Z',
    #             maxResults=100,
    #             singleEvents=True,
    #             orderBy="startTime",
    #         ).execute()

    #         events = event_result.get("items", [])

    #         formatted_events = []
    #         for event in events:
    #             start = event["start"].get("dateTime", event["start"].get("date"))
    #             end = event["end"].get("dateTime", event["end"].get("date"))
    #             formatted_event = {
    #                 "summary": event["summary"],
    #                 "start": start,
    #                 "end": end,
    #                 "description": event.get("description", ""),
    #                 "location": event.get("location", ""),
    #             }
    #             formatted_events.append(formatted_event)

    #         return formatted_events

    #     except HttpError as e:
    #         logger.error(f"An error occurred: {e}")
    #         return []

    async def refresh_token(self, user_id: str) -> Any:
        """
        Refresh the access token for a user.

        Returns the refreshed access token.
        """
        user = await self.auth_dao.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            raise NotFoundException("User not found")
        return await self.generate_access_token(user)

    async def update_password(self, token: str, new_password: str) -> None:
        """
        Update a user's password using a token for verification.
        """
        decoded_token = decode_token(token)
        email = decoded_token["email"]

        if decoded_token["type"] != "otp":
            logger.warning("Invalid token type")
            raise TokenException("Invalid token type")

        user = await self.auth_dao.get_user_by_email(email)

        if user is not None:
            if PasswordHashing.verify_password(new_password, user.password):
                logger.warning("New password cannot be the same as the old password.")
                raise DiffPwdException(
                    "New password cannot be the same as the old password."
                )
            password_check(new_password)

            hashed_password = PasswordHashing.create_hashed_password(new_password)
            await self.auth_dao.update_user_password(user, hashed_password)
            await self.auth_dao.db.commit()
        else:
            logger.warning(f"No user found with email '{email}'. Password not updated.")
            raise NotFoundException(f"No user found with email '{email}'.")

    async def handle_sso_user(
        self,
        email: str,
        name: str,
        provider: str,
        provider_id: str,
        picture: Optional[str] = None,
        is_signup: bool = False
    ) -> str:
        """
        Handle SSO user from any provider (Google or Apple).
        Creates or updates user and returns access token.
        """
        try:
            # Try to find existing user
            user = await self.auth_dao.get_user_by_oauth_provider(provider, provider_id)
            if not user:
                user = await self.auth_dao.get_user_by_email(email)

            # Handle signup vs login
            if is_signup:
                if user:
                    # If user exists during signup, they should login instead
                    raise HTTPException(
                        status_code=400,
                        detail="Email already registered. Please login instead."
                    )
                # Create new user for signup
                user = User(
                    id=f"user_{str(uuid.uuid4())}",
                    email=email,
                    name=name,
                    is_email_verified=True,
                    avatar_url=picture
                )
            else:  # Login flow
                if not user:
                    # If user doesn't exist during login, they should signup
                    raise HTTPException(
                        status_code=404,
                        detail="Account not found. Please signup first."
                    )

            # Update OAuth fields
            if provider == "google":
                user.google_sub = provider_id
            else:
                user.apple_sub = provider_id

            user.oauth_provider = provider
            user.name = name or user.name  # Update name if provided
            if picture:
                user.avatar_url = picture

            # Save user
            self.auth_dao.create_user(user)
            await self.auth_dao.db.commit()

            # Generate access token
            return await self.generate_access_token(user)

        except Exception as e:
            logger.error(f"Error handling SSO user: {str(e)}")
            raise HTTPException(status_code=500, detail=f"SSO handling failed: {str(e)}")

    async def replace_password(
        self, email: str, old_password: str, new_password: str
    ) -> None:
        """
        Replace a user's password with a new one after verifying the old password.
        """
        email = normalize_email(email)

        user = await self.auth_dao.get_user_by_email(email)

        if user is None:
            logger.warning(f"No user found with email '{email}'. Password not updated.")
            raise NotFoundException(f"No user found with email '{email}'.")

        if not PasswordHashing.verify_password(old_password, user.password):
            logger.warning("Your password is incorrect.")
            raise IncorrectPwdException("Your password is incorrect.")

        if PasswordHashing.verify_password(new_password, user.password):
            logger.warning("New password cannot be the same as the old password.")
            raise DiffPwdException(
                "New password cannot be the same as the old password."
            )

        password_check(new_password)

        hashed_password = PasswordHashing.create_hashed_password(new_password)
        await self.auth_dao.update_user_password(user, hashed_password)
        await self.auth_dao.db.commit()

async def compose_forgot_pwd_message(
    email: str, payload: dict, expiry_minutes: int
) -> str:
    """
    Compose a message for password reset with a tokenized URL.

    Returns the message containing the reset URL.
    """
    reset_pwd_url = f"{settings.DOMAIN_NAME}/mktp/update-password"

    jwt_token = JWTBearer.generate_jwt(payload=payload, expiry_minutes=expiry_minutes)

    return f"{reset_pwd_url}?token={jwt_token}&email={email}"


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_postgres_session)
) -> Dict[str, Any]:
    """
    Retrieve the current user based on the provided token.
    Works with both traditional and SSO authentication.

    Returns a dictionary containing user information and authentication details.
    """
    if not token:
        raise NotFoundException("User not found.")

    decoded_token = decode_token(token)

    if (
        not decoded_token
        or "user_id" not in decoded_token
        or "email" not in decoded_token
    ):
        logger.warning("Invalid token.")
        raise TokenException(detail="Invalid token.")
    
    user_id = decoded_token["user_id"]
    email = decoded_token["email"]
    user_dao = AuthDAO(db)
    user = await user_dao.get_user(email, user_id)
    await user_dao.db.commit()
    logger.info(user)

    if user is None:
        logger.warning("No valid users found in the database.")
        raise NotFoundException(
            "No valid users found in the database.",
        )

    try:
        # Refresh the user object to ensure all attributes are loaded
        await db.refresh(user)
        
        # Determine authentication method
        auth_method = "password"
        if user.google_sub:
            auth_method = "google"
        elif user.apple_sub:
            auth_method = "apple"

        # Return enhanced user information
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "auth_method": auth_method,
            "is_email_verified": user.is_email_verified,
            "avatar_url": user.avatar_url,
            "oauth_provider": user.oauth_provider,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    except Exception as e:
        logger.error(f"Error accessing user attributes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error accessing user information"
        )

def decode_token(token: str) -> Any:
    """
    Decode a JWT token and return its payload.

    Raises exceptions for expired or invalid tokens.
    """
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.error("Your session has expired due to inactivity. Please log in again.")
        raise LoginExpiredException(
            "Your session has expired due to inactivity. Please log in again."
        )
    except jwt.InvalidTokenError:
        logger.error(f"Invalid token: {token}.")
        raise TokenException("Invalid token.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e


def password_check(password: str) -> None:
    """
    Validate a password against security criteria.

    Raises an HTTPException if the password does not meet the criteria.
    """
    # calculating the length
    length_error = len(password) < 8

    # searching for digits
    digit_error = re.search(r"\d", password) is None

    # searching for uppercase
    uppercase_error = re.search(r"[A-Z]", password) is None

    # searching for lowercase
    lowercase_error = re.search(r"[a-z]", password) is None

    # searching for symbols
    symbol_error = re.search(r"[ !@#$%&'()*+,-./[\\\]^_`{|}~" + r'"]', password) is None

    # overall result
    if (
        length_error
        or digit_error
        or uppercase_error
        or lowercase_error
        or symbol_error
    ):
        error_messages = []
        if length_error:
            error_messages.append("Password length must be at least 8 characters")
        if digit_error:
            error_messages.append("Password must contain at least one digit")
        if uppercase_error:
            error_messages.append("Password must contain at least one uppercase letter")
        if lowercase_error:
            error_messages.append("Password must contain at least one lowercase letter")
        if symbol_error:
            error_messages.append("Password must contain at least one special symbol")
        error_detail = ". ".join(error_messages)

        logger.warning(f"Password validation failed: {error_detail}")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail
        )
