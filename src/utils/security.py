from typing import Any

from passlib.context import CryptContext


class PasswordHashing:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def create_hashed_password(password: str) -> Any:
        return PasswordHashing.pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> Any:
        return PasswordHashing.pwd_context.verify(plain_password, hashed_password)
