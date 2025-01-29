import logging
import string
import random
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
import aiosmtplib
import backoff
import pytz
import redis.asyncio as redis
from fastapi import HTTPException
from pydantic import ValidationError
from config import settings
from utils.exceptions import OTPException

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
@backoff.on_exception(backoff.constant, ConnectionError, max_tries=8, interval=1)
async def generate_verification_code(
    key: str,
    redis_client: redis.Redis,
    expiry_minutes: int,
    length: int = 6,
) -> str:
    otp = "".join(random.choices(string.digits, k=length))
    logger.info(redis_client)
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid or missing Redis connection.",
        )
    try:
        async with redis_client as conn:
            await conn.set(key, otp)
            await conn.expire(key, expiry_minutes * 60)
    except Exception:
        raise ConnectionError("Unable to connect to Redis server")
    return otp

@backoff.on_exception(backoff.constant, ConnectionError, max_tries=8, interval=1)
async def verify_otp(key: str, otp: str, redis_client: redis.StrictRedis) -> None:
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid or missing Redis connection.",
        )

    stored_otp = None
    try:
        async with redis_client as conn:
            stored_otp = await conn.get(key)
            logger.info(f"stored_otp: {stored_otp}")
    except Exception:
        raise ConnectionError("Unable to connect to Redis server")

    if stored_otp is None or stored_otp != otp:
        raise OTPException(detail="Verification code is invalid or expired")

    try:
        await conn.delete(key)
        logger.info(f"OTP deleted from Redis for key: {key}")
    except Exception as e:
        logger.error(f"Failed to delete OTP for key {key}: {e}")
        raise ConnectionError("Unable to delete OTP from Redis server")

async def send_otp_email(email: str, otp: str) -> None:
    subject = f"Getorganised: Verification Code {otp} - Action Required"
    if email is None:
        raise HTTPException(
            status_code=400,
            detail="Email cannot be None",
        )
    logger.info(f"verify email: {email}")
    logger.info(f"one-time password: {otp}")
    body = compose_verify_email_message(otp)

    logger.debug(f"email username: {settings.VERIFICATION_SMTP_USERNAME}")
    logger.debug(f"email password: {settings.VERIFICATION_SMTP_PASSWORD}")

    await send_email(
        from_email=settings.VERIFICATION_SMTP_FROM_EMAIL,
        to_email=email,
        smtp_username=settings.VERIFICATION_SMTP_USERNAME,
        smtp_password=settings.VERIFICATION_SMTP_PASSWORD,
        subject=subject,
        body=body,
    )


async def send_email(
    from_email: str,
    to_email: str,
    smtp_username: str,
    smtp_password: str,
    subject: str,
    body: str,
) -> None:
    email_message = MIMEMultipart()
    email_message["From"] = from_email
    email_message["To"] = to_email
    email_message["Subject"] = subject
    email_message.attach(MIMEText(body, "html"))

    async with aiosmtplib.SMTP(
        hostname=settings.SMTP_SERVER,
        port=settings.SMTP_PORT,
        start_tls=True,
        username=smtp_username,
        password=smtp_password,
    ) as server:
        await server.send_message(email_message)
        logger.info("Email sent successfully")

def compose_verify_email_message(otp: str) -> str:
    return """
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        color: #333333;
                        margin: 20px;
                    }}
                    p {{
                        margin-bottom: 15px;
                    }}
                </style>
            </head>
            <body>
                <p>Dear User,</p>

                <p>Your verification code is: <strong>{0}</strong></p>

                <p>Please use this code to verify your account within the next {1} minutes.</p>

                <p><em>Regards,<br>
                LeyLine</em></p>
            </body>
            </html>
            """.format(
        otp, settings.OTP_EXPIRY_MINUTES
    )


def paginate(items: List, page: int, size: int) -> List:
    total_items = len(items)
    start_index = (page - 1) * size
    end_index = start_index + size

    if start_index >= total_items:
        return []

    return items[start_index:end_index]


def reformat_validation_error(rve: ValidationError) -> str:
    reformatted_message = ""
    for pydantic_error in rve.errors():
        loc, msg = pydantic_error["loc"], pydantic_error["msg"]
        filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
        field_string = ".".join([str(item) for item in filtered_loc])
        reformatted_message = f"{field_string}: {msg}"
    return reformatted_message


def normalize_email(email: str) -> str:
    email = email.lower()
    if settings.FASTAPI_CONFIG == "production":
        parts = email.split("@")
        if len(parts) == 2:
            local_part, domain_part = parts
            local_part = local_part.split("+")[0]
            normalized_email = f"{local_part}@{domain_part}"
            return normalized_email
        else:
            return email
    return email


def convert_to_utc(naive_datetime: datetime, timezone_str: str) -> datetime:
    tz = pytz.timezone(timezone_str)
    aware_datetime = tz.localize(naive_datetime)
    utc_datetime = aware_datetime.astimezone(pytz.utc)
    return utc_datetime
