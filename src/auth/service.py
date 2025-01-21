import logging
import re
import uuid
import httpx
import jwt
from typing import Annotated, Any, Dict, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models.user_model import User
from auth.auth_bearer import JWTBearer

from utils.exceptions import (
    DiffPwdException,
    DuplicateException,
    GoogleAuthException,
    IncorrectPwdException,
    LoginExpiredException,
    NotFoundException,
    TokenException,
    UserNotActivatedException,
)
from auth.auth_bearer import JWTBearer
from auth.dao import AuthDAO
from auth.schema import CreateUserIn
from auth.security import PasswordHashing
from config import settings
from db.postgres import AsyncSession, get_postgres_session
from utils.helpers import normalize_email

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.ROOT_PATH}/auth/login", auto_error=False
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        auth_dao: AuthDAO = Depends(AuthDAO),
    ):
        self.auth_dao = auth_dao

    async def create_user(
        self,
        create_user_in: CreateUserIn,
    ) -> str:
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
            user_name=create_user_in.user_name,
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
        email = normalize_email(email)

        user = await self.auth_dao.get_user_by_email(email)

        if user is None:
            logger.warning("User not found")
            raise NotFoundException("User not found")

        if not user.is_email_verified:
            logger.warning("User not activated")
            raise UserNotActivatedException("User not activated")

        if PasswordHashing.verify_password(
            password, user.password if user.password else ""
        ):
            return await self.generate_access_token(user)
        else:
            logger.warning("Incorrect password")
            raise IncorrectPwdException("Incorrect password")

    async def generate_access_token(self, user: User) -> str:
        profile = dict(
            avatar_url=user.avatar_url,
            user_name=user.user_name,
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
        email = normalize_email(email)

        payload = {"email": email, "type": "otp"}
        expiry_minutes = 30
        jwt_token: str = JWTBearer.generate_jwt(
            payload=payload, expiry_minutes=expiry_minutes
        )

        return jwt_token

    async def delete_user(self, user_email: str) -> None:
        user_email = normalize_email(user_email)

        await self.auth_dao.delete_user_by_email(user_email)
        await self.auth_dao.db.commit()

    async def refresh_token(self, user_id: str) -> Any:
        user = await self.auth_dao.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            raise NotFoundException("User not found")
        return await self.generate_access_token(user)

    async def update_password(self, token: str, new_password: str) -> None:
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

    async def handle_oidc_login(self, code: str) -> Any:
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.REDIRECT_URL,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.GOOGLE_TOKEN_URL, data=data)

            if response.status_code != 200:
                logger.warning(f"Token exchange failed: {response.text}")
                raise GoogleAuthException(f"Token exchange failed: {response.text}")

            token_data = response.json()

            id_token = token_data["id_token"]

            custom_google_tokeninfo_url = (
                f"{settings.GOOGLE_TOKENINFO_URL}?id_token={id_token}"
            )

            token_info_response = await client.get(custom_google_tokeninfo_url)

            if token_info_response.status_code != 200:
                logger.warning(
                    f"Failed to fetch user profile: {token_info_response.text}",
                )
                raise GoogleAuthException(
                    f"Failed to fetch user profile: {token_info_response.text}"
                )

            profile_data = token_info_response.json()

            google_sub = profile_data["sub"]
            user = await self.auth_dao.get_user_by_google_sub(google_sub)
            if user is None:
                user = User(
                    email=profile_data["email"],
                    google_sub=profile_data["sub"],
                    user_name=profile_data["name"],
                    avatar_url=profile_data["picture"],
                    is_subscribed=True,
                    is_email_verified=True,
                )

            self.auth_dao.create_user(user)
            await self.auth_dao.db.commit()
            return await self.generate_access_token(user)

    async def replace_password(
        self, email: str, old_password: str, new_password: str
    ) -> None:
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
    reset_pwd_url = f"{settings.DOMAIN_NAME}/mktp/update-password"

    jwt_token = JWTBearer.generate_jwt(payload=payload, expiry_minutes=expiry_minutes)

    return f"{reset_pwd_url}?token={jwt_token}&email={email}"


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_postgres_session),
) -> Optional[Any]:
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

    if user is None:
        logger.warning("No valid users found in the database.")
        raise NotFoundException(
            "No valid users found in the database.",
        )
    return decoded_token

def decode_token(token: str) -> Any:
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
