# Configuration settings for the FastAPI application

import os
from functools import cache
from pydantic_settings import BaseSettings

SECRETS_PATH = "/app/secrets"

class BaseConfig(BaseSettings):
    # load environment variables
    FASTAPI_CONFIG: str = ""
    DOMAIN_NAME: str = ""
    ROOT_PATH: str = ""

    # postgres
    SQLALCHEMY_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432"
    )
    SQLALCHEMY_ECHO_SQL: bool = False

    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CELERY_DB: int = 1

    STORAGE_ACCOUNT: str = ""
    STORAGE_ACCOUNT_KEY: str = ""

    # oidc google
    GOOGLE_TOKEN_URL: str = ""
    GOOGLE_AUTH_URL: str = ""
    GOOGLE_TOKENINFO_URL: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    REDIRECT_URL: str = ""

    SMTP_SERVER: str = ""
    SMTP_PORT: int = 0
    

    # contact us stmp
    CONTACTUS_SMTP_FROM_EMAIL: str = ""
    CONTACTUS_SMTP_USERNAME: str = ""
    CONTACTUS_SMTP_PASSWORD: str = ""

    # verification stmp
    VERIFICATION_SMTP_FROM_EMAIL: str = ""
    VERIFICATION_SMTP_USERNAME: str = ""
    VERIFICATION_SMTP_PASSWORD: str = ""

    # jwt
    JWT_SECRET: str = "your-secret-key"
    JWT_EXPIRY_DAYS: int = 30

    # otp
    OTP_EXPIRY_MINUTES: int = 30

    class Config:
        case_sensitive = True


class DevelopConfig(BaseConfig):
    FASTAPI_CONFIG: str = "production"

    DOMAIN_NAME: str = os.environ.get("DOMAIN_NAME", "")
    ROOT_PATH: str = ""

    SQLALCHEMY_DATABASE_URL: str = os.environ.get("SQLALCHEMY_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432")
    SQLALCHEMY_ECHO_SQL: bool = os.environ.get("SQLALCHEMY_ECHO_SQL", False)

    REDIS_HOST: str = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT: int = os.environ.get("REDIS_PORT", 6380)
    REDIS_DB: int = 0
    REDIS_TLS: bool = True
    REDIS_PASSWORD: str = os.environ.get("REDIS_PASSWORD", "")

    STORAGE_ACCOUNT: str = os.environ.get("STORAGE_ACCOUNT", "")
    STORAGE_ACCOUNT_KEY: str = os.environ.get("STORAGE_ACCOUNT_KEY", "")

    # oidc google
    GOOGLE_TOKEN_URL: str = os.environ.get("GOOGLE_TOKEN_URL", "")
    GOOGLE_AUTH_URL: str = os.environ.get("GOOGLE_AUTH_URL", "")
    GOOGLE_TOKENINFO_URL: str = os.environ.get("GOOGLE_TOKENINFO_URL", "")
    GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    REDIRECT_URL: str = os.environ.get("REDIRECT_URL", "")

    SMTP_SERVER: str = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = os.environ.get("SMTP_PORT", 587)

    # contact us stmp
    # CONTACTUS_SMTP_FROM_EMAIL: str = os.environ.get("CONTACTUS_SMTP_FROM_EMAIL", "")
    # CONTACTUS_SMTP_USERNAME: str = os.environ.get("CONTACTUS_SMTP_USERNAME", "alex@getorganised.ai")
    # CONTACTUS_SMTP_PASSWORD: str = os.environ.get("CONTACTUS_SMTP_PASSWORD", "M@ther114")

    # verification stmp
    VERIFICATION_SMTP_FROM_EMAIL: str = os.environ.get(
        "VERIFICATION_SMTP_FROM_EMAIL", "support@getorganised.ai"
    )
    VERIFICATION_SMTP_USERNAME: str = os.environ.get("VERIFICATION_SMTP_USERNAME", "bluxking06@gmail.com")
    VERIFICATION_SMTP_PASSWORD: str = os.environ.get("VERIFICATION_SMTP_PASSWORD", "dhng khot tkst lzuc")

    # jwt
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "your-secret-key")
    JWT_EXPIRY_DAYS: int = os.environ.get("JWT_EXPIRY_DAYS", 30)

    # otp
    OTP_EXPIRY_MINUTES: int = os.environ.get("OTP_EXPIRY_MINUTES", 30)

@cache
def get_settings() -> BaseConfig:
    config_cls_dict = {
        "development": DevelopConfig
    }

    config_name = "development"
    config_cls = config_cls_dict[config_name]
    config_obj = config_cls()
    if (
        config_name == "testing"
        or config_name == "staging"
        or config_name == "production"
    ):
        config_obj.ROOT_PATH = "/mktp"
    return config_obj


settings: BaseConfig = get_settings()
