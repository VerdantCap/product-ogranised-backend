import logging
import smtplib
import os
from typing import Annotated, Optional
# from datetime import datetime, timedelta

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_sso.sso.google import GoogleSSO
# from fastapi_sso.sso.apple import AppleSSO

from schemas import (
    CreateUserIn,
    UserLogin,
    AccessToken,
    ForgotPassword,
    VerifyOtpRequest,
    ForgotPasswordReset,
    ReplacePassword,
    UserProfileUpdate,
    UserPreferencesUpdate,
    UserProfileResponse
)

from services.auth_service import AuthService, get_current_user
from daos.workspace_dao import WorkspaceDAO
from config import settings
from utils.route import APIRouter
from utils.helpers import (
    generate_verification_code,
    send_otp_email,
    verify_otp,
)
from utils.redis_util import redis_context
from utils.schema import ID

# Create a new API router for authentication-related endpoints
auth_router = APIRouter()

# Set up a logger for the authentication controller
logger = logging.getLogger(__name__)

# Initialize SSO providers
google_sso = GoogleSSO(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    redirect_uri=settings.GOOGLE_REDIRECT_URL,
    allow_insecure_http=True  # Only for development
)

# apple_sso = AppleSSO(
#     client_id=settings.APPLE_CLIENT_ID,
#     client_secret=settings.APPLE_CLIENT_SECRET,
#     redirect_uri=settings.APPLE_REDIRECT_URL,
#     allow_insecure_http=True  # Only for development
# )

@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_controller(
    user: CreateUserIn,
    auth_service: AuthService = Depends(AuthService),
) -> JSONResponse:
    """
    Register a new user.

    This function handles user registration by creating a new user in the system.
    Returns user ID and next step URL for generating verification code.
    """
    try:
        user_id = await auth_service.create_user(user)
        return JSONResponse(
            content={
                "id": user_id,
                "next_step": f"/auth/{user_id}/generate_code?email={user.email}",
                "message": "User created successfully. Please generate verification code."
            },
            status_code=status.HTTP_201_CREATED
        )
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
    form_data: UserLogin,
    auth_service: AuthService = Depends(AuthService),
) -> AccessToken:
    """
    User login.

    This function handles user login by verifying the provided credentials.

    Returns an access token if the login is successful.
    """
    try:
        access_token = await auth_service.handle_login(
            form_data.email, form_data.password
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


@auth_router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    """Redirect to Google login page"""
    return await google_sso.get_login_redirect(request, state="login")


# @auth_router.get("/apple/login")
# async def apple_login(request: Request) -> RedirectResponse:
#     """Redirect to Apple login page"""
#     return await apple_sso.get_login_redirect(request, state="login")

# OAuth callback endpoints
@auth_router.get("/google/callback")
async def google_callback(
    request: Request,
    auth_service: AuthService = Depends(AuthService)
) -> RedirectResponse:
    """Handle Google OAuth callback"""
    try:
        user = await google_sso.verify_and_process(request)
        if not user:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        # Check if the user exists in the database
        user_exists = await auth_service.auth_dao.check_email_exists(user.email)

        if user_exists:

        # Create or update user
            access_token = await auth_service.handle_sso_user(
                email=user.email,
                name=user.display_name or "",
                provider="google",
                provider_id=user.id,
                picture=user.picture,
                is_signup=False
            )

        else:
            # Signup flow
            access_token = await auth_service.handle_sso_user(
                email=user.email,
                name=user.display_name or "",
                provider="google",
                provider_id=user.id,
                picture=user.picture,
                is_signup=True
            )

        # Redirect to appropriate page based on signup/login
        redirect_path = "login" if user_exists else "signup"
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/{redirect_path}/callback?access_token={access_token}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/error?message={str(e)}",
            status_code=status.HTTP_303_SEE_OTHER
        )

# @auth_router.post("/apple/callback")
# async def apple_callback(
#     request: Request,
#     auth_service: AuthService = Depends(AuthService)
# ) -> RedirectResponse:
#     """Handle Apple OAuth callback"""
#     try:
#         user = await apple_sso.verify_and_process(request)
#         if not user:
#             raise HTTPException(status_code=400, detail="Failed to get user info from Apple")

#         # Check if the user exists in the database
#         user_exists = await auth_service.auth_dao.check_email_exists(user.email)

#         if user_exists:
#             access_token = await auth_service.handle_sso_user(
#                 email=user.email,
#                 name=user.display_name or "",
#                 provider="apple",
#                 provider_id=user.id,
#                 picture=None,  # Apple doesn't provide profile picture
#                 is_signup=False
#             )
#         else:
#             access_token = await auth_service.handle_sso_user(
#                 email=user.email,
#                 name=user.display_name or "",
#                 provider="apple",
#                 provider_id=user.id,
#                 picture=None,  # Apple doesn't provide profile picture
#                 is_signup=True
#             )

#         # Redirect to appropriate page based on signup/login
#         redirect_path = "login" if user_exi else "signup"
#         return RedirectResponse(
#             url=f"{settings.FRONTEND_URL}/auth/{redirect_path}/callback?access_token={access_token}",
#             status_code=status.HTTP_303_SEE_OTHER
#         )
#     except Exception as e:
#         logger.error(f"Apple callback error: {str(e)}")
#         return RedirectResponse(
#             url=f"{settings.FRONTEND_URL}/auth/error?message={str(e)}",
#             status_code=status.HTTP_303_SEE_OTHER
#         )

@auth_router.post("/{user_id}/generate_code")
async def verify_user_email_controller(
    user_id: str,
    email: str,
    redis_client: redis.Redis = Depends(redis_context),
) -> None:
    """
    Generate verification code for user email.

    This function generates a verification code and sends it to the user's email address.

    The function returns nothing.
    """
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
) -> AccessToken:
    """
    Verify one-time password.

    This function is responsible for verifying the one-time password according to the specified company ID.

    The function returns nothing.
    """
    try:
        key = user_id
        await verify_otp(key, otp, redis_client)
        logger.info("OTP verification successful")
        user = await auth_service.auth_dao.get_user_by_id(user_id)
        await auth_service.auth_dao.verify_user_email(user)
        await auth_service.auth_dao.refresh_database()
        access_token = await auth_service.generate_access_token(user)
        return AccessToken(access_token=access_token, token_type="bear")

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


@auth_router.get("/me", response_model=UserProfileResponse)
async def get_current_user_controller(
    user_info: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(AuthService),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
) -> UserProfileResponse:
    """
    Get current user information.
    
    This endpoint returns the information of the currently authenticated user.
    
    Returns a JSON response containing the user's information.
    """
    
    try:
        logger.info("Getting current user information")
        user_id = user_info.get("user_id")
        user = await auth_service.auth_dao.get_user_by_id(user_id)
        workspaces = await workspace_dao.get_workspaces_by_user_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(workspaces[0].id)
        return UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            address=user.address,
            phone=user.phone,
            country=user.country,
            city=user.city,
            timezone=user.timezone,
            bio=user.bio,
            languages=user.languages,
            avatar_url=user.avatar_url,
            cover_image_url=user.cover_image_url,
            email_notification=user.email_notification,
            sms_notification=user.sms_notification,
            push_notification=user.push_notification,
            marketing_email=user.marketing_email,
            marketing_phone=user.marketing_phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
            workspace_id = workspaces[0].id
        )
    except HTTPException as he:
        logger.error(f"{he.detail}: {he}")
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while getting user information: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@auth_router.put("/profile")
async def update_profile_controller(
    profile_data: UserProfileUpdate = None,
    avatar: UploadFile = File(None),
    user_info: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(AuthService),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
) -> JSONResponse:
    """
    Update user profile.
    
    This endpoint allows the user to update their profile information.
    
    Returns a JSON response indicating success or failure.
    """
    try:
        logger.info("Updating user profile")
        user_id = user_info.get("user_id")
        
        # Update profile data if provided
        if profile_data:
            profile_dict = profile_data.dict(exclude_unset=True)
            if profile_dict:
                await auth_service.auth_dao.update_user_profile(user_id, profile_dict)
        
        # Handle avatar upload if provided
        if avatar:
            from utils.storage import store_file, get_file_url
            
            # Get the user's workspaces
            workspaces = await workspace_dao.get_workspaces_by_user_id(user_id)
            if not workspaces:
                # If user has no workspaces, create a default storage path
                storage_path = f"users/{user_id}/avatars"
            else:
                # Use the first workspace ID
                workspace_id = workspaces[0].id
                storage_path = f"workspaces/{workspace_id}/users/{user_id}/avatars"
            
            # Store the avatar using the storage utility
            file_path = await store_file(avatar, storage_path)
            
            # Get the URL for the stored file
            if hasattr(settings, 'USE_S3_STORAGE') and settings.USE_S3_STORAGE:
                avatar_url = get_file_url(file_path)
            else:
                avatar_url = f"/files/{file_path}"
            
            # Update the avatar URL in the database
            await auth_service.auth_dao.update_user_avatar(user_id, avatar_url)
        
        return JSONResponse(
            content={"message": "Profile updated successfully"},
            status_code=status.HTTP_200_OK
        )
    except HTTPException as he:
        logger.error(f"{he.detail}: {he}")
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while updating user profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@auth_router.put("/preferences")
async def update_preferences_controller(
    preferences: UserPreferencesUpdate,
    user_info: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(AuthService)
) -> JSONResponse:
    """
    Update user preferences.
    
    This endpoint allows the user to update their notification and marketing preferences.
    
    Returns a JSON response indicating success or failure.
    """
    try:
        logger.info("Updating user preferences")
        user_id = user_info.get("user_id")
        
        preferences_dict = preferences.dict(exclude_unset=True)
        if preferences_dict:
            await auth_service.auth_dao.update_user_preferences(user_id, preferences_dict)
        
        return JSONResponse(
            content={"message": "Preferences updated successfully"},
            status_code=status.HTTP_200_OK
        )
    except HTTPException as he:
        logger.error(f"{he.detail}: {he}")
        raise HTTPException(
            status_code=he.status_code, detail=he.detail, headers=he.headers
        )
    except Exception as e:
        logger.error(f"An error occurred while updating user preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@auth_router.delete("/delete")
async def delete_user_controller(
    user_info: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(AuthService),
) -> None:
    """
    Delete user account.

    This function is responsible for deleting the user account associated with the provided token.

    The function returns nothing if the account is deleted successfully.
    """
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
    """
    Refresh access token.

    This function is responsible for refreshing the access token for the user associated with the provided token.

    Returns a new access token.
    """
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
