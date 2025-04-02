import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, Request, Response
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from db.postgres import AsyncSession, get_postgres_session

from models.user_model import User
from models.workspace_model import Workspace
from daos.workspace_dao import WorkspaceDAO
from daos.auth_dao import AuthDAO
from services.auth_service import get_current_user
from fastapi.security import OAuth2PasswordBearer
from utils.exceptions import NotFoundException
from utils.redis_util import redis_context
from utils.route import APIRouter
from utils.helpers import send_email, compose_workspace_invite_email
from schemas import WorkspaceInviteCreate, WorkspaceInviteResponse, WorkspaceInviteAccept
from enums import WorkspaceRole
from config import settings

invite_router = APIRouter()
logger = logging.getLogger(__name__)

# Create a custom dependency that returns None if no token is provided
async def get_optional_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl=f"{settings.ROOT_PATH}/auth/login", auto_error=False)),
    db: AsyncSession = Depends(get_postgres_session)
) -> Optional[Dict[str, Any]]:
    """
    Dependency that returns the current user if authenticated, or None if not.
    This is used for endpoints that can be accessed by both authenticated and unauthenticated users.
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token, db)
    except NotFoundException:
        return None
    except Exception as e:
        raise e

# Redis key prefix for invites
INVITE_KEY_PREFIX = "workspace_invite:"
# Invite expiration time in days
INVITE_EXPIRATION_DAYS = 7

@invite_router.post("/workspace/{workspace_id}", response_model=WorkspaceInviteResponse)
async def create_workspace_invite(
    workspace_id: str = Path(..., description="Workspace ID"),
    invite_data: WorkspaceInviteCreate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(),
    auth_dao: AuthDAO = Depends(),
    redis: Redis = Depends(redis_context)
):
    """
    Create a workspace invitation.
    
    This endpoint creates an invitation for a user to join a workspace.
    The invitation is stored in Redis with an expiration time.
    """
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if the current user has permission to invite users
    members = await workspace_dao.get_workspace_members(workspace_id)
    current_user_member = next((m for m in members if m["id"] == current_user["user_id"]), None)
    
    if not current_user_member:
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    
    if current_user_member["role"] not in [WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="You don't have permission to invite users")
    
    # Check if the user already exists
    existing_user = await auth_dao.get_user_by_email(invite_data.email)
    
    # Generate a unique token for the invitation
    token = str(uuid.uuid4())
    
    # Create the invitation data
    invite = {
        "workspace_id": workspace_id,
        "email": invite_data.email,
        "role": invite_data.role.value,
        "invited_by": current_user["user_id"],
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=INVITE_EXPIRATION_DAYS)).isoformat()
    }
    
    # Store the invitation in Redis with expiration
    redis_key = f"{INVITE_KEY_PREFIX}{token}"
    await redis.set(redis_key, json.dumps(invite), ex=INVITE_EXPIRATION_DAYS * 24 * 60 * 60)
    
    # Generate the invite link
    invite_link = f"{settings.FRONTEND_URL}/invite/accept?token={token}"
    
    # Get inviter's name
    inviter_name = current_user.get("name", "A workspace administrator")
    
    # Send invitation email
    try:
        # Create email subject
        subject = f"Invitation to join {workspace.name} workspace"
        
        # Create email body
        body = compose_workspace_invite_email(
            workspace_name=workspace.name,
            inviter_name=inviter_name,
            role=invite_data.role.value,
            invite_link=invite_link,
            expiry_days=INVITE_EXPIRATION_DAYS
        )
        
        # Send the email
        await send_email(
            from_email=settings.VERIFICATION_SMTP_FROM_EMAIL,
            to_email=invite_data.email,
            smtp_username=settings.VERIFICATION_SMTP_USERNAME,
            smtp_password=settings.VERIFICATION_SMTP_PASSWORD,
            subject=subject,
            body=body
        )
        
        logger.info(f"Invitation email sent to {invite_data.email} for workspace {workspace.name}")
    except Exception as e:
        logger.error(f"Failed to send invitation email: {e}", exc_info=True)
        # We don't want to fail the invitation creation if email sending fails
        # Just log the error and continue
    
    # Return the invitation details
    return WorkspaceInviteResponse(
        email=invite_data.email,
        role=invite_data.role.value,
        invite_link=invite_link,
        expires_at=datetime.fromisoformat(invite["expires_at"])
    )

@invite_router.get("/workspace/{workspace_id}", response_model=List[Dict[str, Any]])
async def get_workspace_invites(
    workspace_id: str = Path(..., description="Workspace ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(),
    redis: Redis = Depends(redis_context)
):
    """
    Get all pending invitations for a workspace.
    
    This endpoint retrieves all pending invitations for a workspace.
    """
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if the current user has permission to view invites
    members = await workspace_dao.get_workspace_members(workspace_id)
    current_user_member = next((m for m in members if m["id"] == current_user["user_id"]), None)
    
    if not current_user_member:
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    
    if current_user_member["role"] not in [WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="You don't have permission to view invites")
    
    # Get all keys matching the invite prefix
    invite_keys = await redis.keys(f"{INVITE_KEY_PREFIX}*")
    
    invites = []
    for key in invite_keys:
        invite_data = await redis.get(key)
        if invite_data:
            invite = json.loads(invite_data)
            if invite["workspace_id"] == workspace_id:
                # Extract token from key
                # Handle both string and bytes cases
                if isinstance(key, bytes):
                    token = key.decode('utf-8').replace(INVITE_KEY_PREFIX, "")
                else:
                    token = key.replace(INVITE_KEY_PREFIX, "")
                invites.append({
                    "token": token,
                    "email": invite["email"],
                    "role": invite["role"],
                    "invited_by": invite["invited_by"],
                    "created_at": invite["created_at"],
                    "expires_at": invite["expires_at"]
                })
    
    return invites

@invite_router.delete("/workspace/{workspace_id}/{token}")
async def delete_workspace_invite(
    workspace_id: str = Path(..., description="Workspace ID"),
    token: str = Path(..., description="Invitation token"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(),
    redis: Redis = Depends(redis_context)
):
    """
    Delete a workspace invitation.
    
    This endpoint deletes a workspace invitation.
    """
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if the current user has permission to delete invites
    members = await workspace_dao.get_workspace_members(workspace_id)
    current_user_member = next((m for m in members if m["id"] == current_user["user_id"]), None)
    
    if not current_user_member:
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    
    if current_user_member["role"] not in [WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="You don't have permission to delete invites")
    
    # Get the invitation
    redis_key = f"{INVITE_KEY_PREFIX}{token}"
    invite_data = await redis.get(redis_key)
    
    if not invite_data:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    invite = json.loads(invite_data)
    if invite["workspace_id"] != workspace_id:
        raise HTTPException(status_code=400, detail="Invitation does not belong to this workspace")
    
    # Delete the invitation
    await redis.delete(redis_key)
    
    return {"message": "Invitation deleted successfully"}

@invite_router.post("/accept", response_model=Dict[str, Any])
async def accept_workspace_invite(
    invite_data: WorkspaceInviteAccept = Body(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_current_user),
    workspace_dao: WorkspaceDAO = Depends(),
    auth_dao: AuthDAO = Depends(),
    redis: Redis = Depends(redis_context)
):
    """
    Accept a workspace invitation.
    
    This endpoint accepts a workspace invitation and adds the user to the workspace.
    If the user is not logged in, they will need to register or log in first.
    """
    # Get the invitation
    redis_key = f"{INVITE_KEY_PREFIX}{invite_data.token}"
    invite_data_str = await redis.get(redis_key)
    
    if not invite_data_str:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    invite = json.loads(invite_data_str)
    
    # Check if the invitation has expired
    expires_at = datetime.fromisoformat(invite["expires_at"])
    if expires_at < datetime.utcnow():
        await redis.delete(redis_key)
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Check if the user is logged in
    if not current_user:
        # Return information about the invitation for the frontend to handle registration/login
        return {
            "status": "auth_required",
            "message": "You need to register or log in to accept this invitation",
            "email": invite["email"],
            "workspace_id": invite["workspace_id"],
            "token": invite_data.token
        }
    
    # Check if the invitation is for the current user
    if current_user["email"].lower() != invite["email"].lower():
        raise HTTPException(
            status_code=400, 
            detail=f"This invitation is for {invite['email']}, but you are logged in as {current_user['email']}"
        )
    
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(invite["workspace_id"])
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Add the user to the workspace with the specified role
    await workspace_dao.add_workspace_member(
        workspace_id=invite["workspace_id"],
        user_id=current_user["user_id"],
        role=invite["role"]
    )
    
    # Delete the invitation
    await redis.delete(redis_key)
    
    return {
        "status": "success",
        "message": "You have successfully joined the workspace",
        "workspace_id": invite["workspace_id"],
        "role": invite["role"]
    }

@invite_router.get("/validate/{token}")
async def validate_workspace_invite(
    token: str = Path(..., description="Invitation token"),
    redis: Redis = Depends(redis_context)
):
    """
    Validate a workspace invitation.
    
    This endpoint checks if an invitation is valid and returns information about it.
    """
    # Get the invitation
    redis_key = f"{INVITE_KEY_PREFIX}{token}"
    invite_data = await redis.get(redis_key)
    
    if not invite_data:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    invite = json.loads(invite_data)
    
    # Check if the invitation has expired
    expires_at = datetime.fromisoformat(invite["expires_at"])
    if expires_at < datetime.utcnow():
        await redis.delete(redis_key)
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    return {
        "email": invite["email"],
        "role": invite["role"],
        "workspace_id": invite["workspace_id"],
        "expires_at": invite["expires_at"]
    }
