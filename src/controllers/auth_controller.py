import logging
import smtplib
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from schemas.auth_schema import (
    CreateUserIn,
    AccessToken,
    ForgotPassword,
    VerifyOtpRequest,
    ForgotPasswordReset,
    ReplacePassword
)

from services.auth_service import AuthService, get_current_user
from config import settings
from utils.route import APIRouter
from utils.helpers import (
    generate_verification_code,
    send_otp_email,
    verify_otp,
)
from utils.redis_util import redis_context
from utils.schema import ID

auth_router = APIRouter()

logger = logging.getLogger(__name__)

CUSTOM_GOOGLE_AUTH_URL = (
    f"{settings.GOOGLE_AUTH_URL}"
    "?response_type=code"
    "&scope=openid profile email"
    f"&client_id={settings.GOOGLE_CLIENT_ID}"
    f"&redirect_uri={settings.REDIRECT_URL}"
)

@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_controller(
    user: CreateUserIn,
    auth_service: AuthService = Depends(AuthService),
) -> ID:
    try:
        user_id = await auth_service.create_user(user)
        return ID(id=user_id)
    except HTTPException as he:
        logger.error(f"{he.detail}: {he}")
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(
            f"An error occurred while processing user registration: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.post("/login")
async def login_controller(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(AuthService),
) -> AccessToken:
    try:
        access_token = await auth_service.handle_login(
            form_data.username, form_data.password
        )
        return AccessToken(access_token=access_token, token_type="bearer")
    except HTTPException as he:
        logger.error(f"{he.detail}: {he}")
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while login")

@auth_router.get("/google-login")
async def google_login() -> RedirectResponse:
    return RedirectResponse(url=CUSTOM_GOOGLE_AUTH_URL, status_code=303)

@auth_router.get("/login/callback")
async def login_callback_controller(
    code: str | None = None,
    error: str | None = None,
    auth_service: AuthService = Depends(AuthService),
) -> RedirectResponse:
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"Authorization error: {error}")

        if code is None:
            raise HTTPException(status_code=400, detail="Authorization code is missing")

        new_token = await auth_service.handle_oidc_login(code)

        return RedirectResponse(
            url=f"{settings.DOMAIN_NAME}/recon-web/auth/redirect?access_token={new_token}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except HTTPException as he:
        logger.error(f"{he.detail}: {he}")
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )

    except Exception as e:
        logger.error(f"Email sending failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.post("/logout", dependencies=[Depends(get_current_user)])
async def logout_controller() -> JSONResponse:
    try:
        response_data = {"message": "Logout successful"}
        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        logger.error(f"An error occurred during logout: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@auth_router.post("/{user_id}/generate_code")
async def verify_user_email_controller(
    user_id: str,
    email: str,
    redis_client: redis.Redis = Depends(redis_context),
) -> None:
    try:
        key = user_id
        verification_code = await generate_verification_code(
            key, redis_client, settings.OTP_EXPIRY_MINUTES
        )
        await send_otp_email(email, verification_code)
        logger.info(f"One-time password has been sent to {email}")

    except smtplib.SMTPException as se:
        logger.error(f"Email sending failed: {se}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email sending failed",
        )
    except HTTPException as he:
        logger.error(f"Email sending failed: {he}", exc_info=True)
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"Internal Server Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )


@auth_router.post("/{user_id}/verify_code")
async def verify_otp_controller(
    user_id: str,
    otp: str,
    redis_client: redis.StrictRedis = Depends(redis_context),
    auth_service: AuthService = Depends(AuthService),
) -> None:
    """
    Verify one-time password.

    This function is responsible for verifying the one-time password according to the specified company ID.

    The function returns nothing.
    """
    try:
        key = user_id
        await verify_otp(key, otp, redis_client)
        logger.info("OTP verification successful")
    except HTTPException as he:
        logger.error(f"{he.detail}: {he}")
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"Internal Server Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.post("/forgot-password/code")
async def forgot_password_controller(
    forgot_password: ForgotPassword,
    auth_service: AuthService = Depends(AuthService),
    redis_client: redis.StrictRedis = Depends(redis_context),
) -> JSONResponse:
    """
    Send one-time password to the email address.

    This function is responsible for sending a one-time password to the email address specified in the request.

    The function returns a JSON response with a message indicating that the one-time password has been sent to the email address.
    """
    email = forgot_password.email

    try:
        # check if the email is in db
        is_email_exists = await auth_service.auth_dao.check_email_exists(email)

        if not is_email_exists:
            raise HTTPException(
                detail="Email doesn't exist", status_code=status.HTTP_404_NOT_FOUND
            )
        key = email
        verification_code = await generate_verification_code(
            key, redis_client, settings.OTP_EXPIRY_MINUTES
        )
        await send_otp_email(email, verification_code)
        response_data = {"message": f"OTP has been sent to {email}"}
        return JSONResponse(content=response_data, status_code=200)
    except HTTPException as he:
        logger.error(f"{he.detail}: {he}", exc_info=True)
        raise HTTPException(status_code=he.status_code, detail=f"{he.detail}")
    except smtplib.SMTPException as se:
        logger.error(f"Email sending failed: {se}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email sending failed",
        )
    except Exception as e:
        logger.error(f"Email sending failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.post("/forgot-password/verify")
async def verify_otp_forgot_password_controller(
    request: VerifyOtpRequest,
    redis_client: redis.StrictRedis = Depends(redis_context),
    auth_service: AuthService = Depends(AuthService),
) -> AccessToken:
    """
    Verify one-time password for forgot password.

    This function is responsible for verifying the one-time password according to the specified email address.

    The function returns otp verification token if the otp is verified successfully.
    """
    try:
        key = request.email
        await verify_otp(key, request.otp, redis_client)
        otp_token = await auth_service.generate_otp_verification_token(request.email)
        return AccessToken(access_token=otp_token, token_type="bearer")
    except HTTPException as he:
        logger.error(he.detail, exc_info=True)
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while verifying OTP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.put("/forgot-password/reset")
async def update_password_controller(
    update_password: ForgotPasswordReset,
    auth_service: AuthService = Depends(AuthService),
) -> None:
    """
    Update user password.

    This function is responsible for updating the user password according to the specified email address and one-time password.

    The function returns nothing if the password is updated successfully.
    """
    try:
        logger.info("update user password")
        await auth_service.update_password(
            update_password.token, update_password.new_password
        )
    except HTTPException as he:
        logger.error(he.detail, exc_info=True)
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while updating password: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.put("/replace-password")
async def replace_password_controller(
    replace_password: ReplacePassword,
    user_info: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(AuthService),
) -> None:
    """
    Replace user password with a new password. Token is required to access this endpoint.
    """
    try:
        logger.info("replace user password")
        user_email = user_info["email"]
        await auth_service.replace_password(
            user_email, replace_password.old_password, replace_password.new_password
        )
    except HTTPException as he:
        logger.error(he.detail, exc_info=True)
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while updating password: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.delete("/delete")
async def delete_user_controller(
    user_info: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(AuthService),
) -> None:
    try:
        logger.info("delete user for service test")
        user_email = user_info["email"]
        await auth_service.delete_user(user_email)
    except HTTPException as he:
        logger.error(he.detail, exc_info=True)
        raise HTTPException(status_code=he.status_code, detail=he.detail)
    except Exception as e:
        logger.error(f"An error occurred while updating password: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.get("/refresh-token")
async def refresh_token_controller(
    user_info: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(AuthService),
) -> AccessToken:
    try:
        user_id = user_info.get("user_id", "")
        access_token = await auth_service.refresh_token(user_id)
        return AccessToken(access_token=access_token, token_type="bearer")
    except HTTPException as he:
        logger.error(he.detail, exc_info=True)
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while refreshing token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )