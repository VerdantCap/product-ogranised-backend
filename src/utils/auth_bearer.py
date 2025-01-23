import logging
from datetime import datetime,timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status
from config import settings

class JWTBearer:
    @staticmethod
    def generate_jwt(payload: dict, expiry_minutes: int) -> Any:
        expiration_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        payload["exp"] = expiration_time.timestamp()
        jwt_token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
        return jwt_token
    
    @staticmethod
    def decode_jwt(token: str)-> Any:
        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=["H256"])
        except jwt.ExpiredSignatureError:
            logging.error("JWT token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT token: Token has expired"
            )
        except jwt.InvalidTokenError:
            logging.err("Invalid JWT token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT token: Token is not valid"
            )
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while processing the JWT token",
            )