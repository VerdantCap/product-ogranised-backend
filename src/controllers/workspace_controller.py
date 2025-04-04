import logging
import uuid
from typing import List, Dict, Any
from fastapi import HTTPException, Depends, Path, Body
from fastapi.responses import RedirectResponse
from models.user_model import User
from models.workspace_model import Workspace
from models.space_model import Space
from services.auth_service import get_current_user
from utils.route import APIRouter
from schemas import WorkspaceCreate, WorkspaceUpdate, WorkspaceMemberRoleUpdate
from daos.workspace_dao import WorkspaceDAO
from daos.auth_dao import AuthDAO
from daos.space_dao import SpaceDAO
from services.stripe_service import StripeService
from enums import ItemSpace, WorkspaceRole
from datetime import datetime

# Create a new API router for workspace-related endpoints
workspace_router = APIRouter()

# Set up a logger for the workspace controller
logger = logging.getLogger(__name__)

@workspace_router.post("/create")  
async def create_workspace(
    data: WorkspaceCreate,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    stripe_service: StripeService = Depends(StripeService),
    auth_dao: AuthDAO = Depends(AuthDAO),
    space_dao: SpaceDAO = Depends(SpaceDAO)
    ):  
    """
    Create a new workspace.
    """
    logger.info(data)
    if data.user_id != user["user_id"]:  
        raise HTTPException(status_code=401, detail="Unauthorized")  

    session = await stripe_service.create_funding_session(data.user_id, user["email"], data.success_url, data.cancel_url)

    # Create workspace instance with generated ID
    workspace_id = f"workspace_{str(uuid.uuid4())}"
    workspace = Workspace(
        id=workspace_id,
        name=data.name,
        owner_id=data.user_id,
        stripe_id=session.id,
        billing_plan=data.plan
    )
    
    # Save workspace to database and get refreshed instance
    workspace = await workspace_dao.create_workspace(workspace)
    
    # Create default spaces for the workspace
    default_spaces = ['insurance', 'household', 'finance', 'pets', 'travel', 'vehicles']
    for space_type in default_spaces:
        space_id = f"space_{str(uuid.uuid4())}"
        from models.space_model import Space
        space = Space(
            id=space_id,
            spacetype=space_type,
            workspace_id=workspace.id,
            user_id=data.user_id,
            status=True  # Enable all spaces by default
        )
        await space_dao.create_space(space)

    # Get actual User object and join workspace
    db_user = await auth_dao.get_user_by_id(user["user_id"])
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    await auth_dao.join_workspace(db_user, workspace)

    return session.url

@workspace_router.get('/{workspace_id}/manage')
async def manage_workspace(
    workspace_id: str,
    user: User=Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    stripe_service: StripeService = Depends(StripeService)
    ): 
    """
    Manage workspace.

    This function handles the management of a workspace, including retrieval of the workspace,
    verification of ownership, and creation of a billing portal session.

    Returns a redirect response to the billing portal or home page.
    """
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)  
    if workspace.owner_id != user["user_id"]:  
        raise HTTPException(status_code=403, detail="Access forbidden")  

    subscription_id = workspace.stripe_id  
    if not subscription_id:  
        raise HTTPException(status_code=400, detail="Bad request: No subscription ID found") 

    try:  
        subscription = await stripe_service.retrieve_stripe_subscription(subscription_id)  
        portal = await stripe_service.create_billing_portal_session(subscription, "settings")  
        return RedirectResponse(url=portal.url)
    except HTTPException as e:
        raise e
    except Exception:  
        return RedirectResponse(url="home")
    

@workspace_router.put("/{workspace_id}/update")
async def update_workspace(
    workspace_id: str,
    workspace_up: WorkspaceUpdate,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):

    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Update fields if provided
    if workspace_up.name is not None:
        workspace.name = workspace_up.name
    if workspace_up.cancelled_at is not None:
        workspace.cancelled_at = workspace_up.cancelled_at
    if workspace_up.expires_at is not None:
        workspace.expires_at = workspace_up.expires_at

    # Save and return updated workspace
    return await workspace_dao.update_workspace(workspace)


@workspace_router.delete("/{workspace_id}/delete")
async def delete_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO) 
    ):
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)

    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    else:
        await workspace_dao.delete_workspace(workspace_id=workspace_id, user_id = workspace.owner_id)

@workspace_router.get("/{workspace_id}/renewal-required")  
async def renewal_required(
    workspace_id: str,
    user: User=Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    stripe_service: StripeService = Depends(StripeService)
    ):  
    """
    Check if workspace renewal is required.

    This function checks if a workspace requires renewal based on the provided workspace ID.

    Returns a redirect response to the dashboard if the subscription is active, or a message indicating renewal is required.
    """
    # Fetch the workspace based on the provided workspace_id  
    workspace = await workspace_dao.get_workspace_by_id(workspace_id) 
    if not workspace or workspace.owner_id != user["user_id"]:  
        raise HTTPException(status_code=404, detail="Workspace not found")    
    if workspace.has_active_subscription():
        return RedirectResponse(url=f"/dashboard?workspace_id={workspace.id}")  
    return {"message": "Please renew your subscription."}  

@workspace_router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    """
    Get workspace by ID.

    This function retrieves a workspace by its ID.

    Returns the workspace if found and the user has access to it.
    """
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return workspace

@workspace_router.get("/{workspace_id}/spaces")
async def get_workspace_spaces(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    space_dao: SpaceDAO = Depends(SpaceDAO)
    ):
    """
    Get workspace spaces.

    This function retrieves the enabled spaces for a workspace based on the provided workspace ID.

    Returns the enabled spaces in the workspace.
    """
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    enabled_spaces = await space_dao.get_enabled_spaces(workspace_id, user["user_id"])
    return {"enabled_spaces": enabled_spaces}

@workspace_router.get("/{workspace_id}/refresh-spaces")
async def refresh_spaces(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    space_dao: SpaceDAO = Depends(SpaceDAO)
    ):
    """
    Refresh workspace spaces.

    This function refreshes the enabled spaces for a workspace based on the provided workspace ID.

    Returns the enabled spaces in the workspace.
    """
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if workspace.owner_id == user["user_id"]:
        enabled_spaces = await space_dao.get_enabled_spaces(workspace_id, user["user_id"])
        return {"enabled_spaces": enabled_spaces}
    else:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
@workspace_router.post("/{workspace_id}/update-item-space-order") 
async def update_item_space_order(
    workspace_id: str,
    order: list,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    space_dao: SpaceDAO = Depends(SpaceDAO)
    ): 
    """
    Update enabled spaces.

    This function updates the list of enabled spaces in a workspace based on the provided workspace ID and list.

    Returns a message indicating success and the updated enabled spaces.
    """
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Validate that all items in the list are valid ItemSpace enum values
    valid_spaces = [space.value for space in ItemSpace]
    for space in order:
        if space not in valid_spaces:
            raise HTTPException(
                status_code=422, 
                detail=f"Invalid space value: {space}. Valid values are: {', '.join(valid_spaces)}"
            )
    
    workspace = await workspace_dao.set_spaces(workspace, order, user["user_id"])
    enabled_spaces = await space_dao.get_enabled_spaces(workspace_id, user["user_id"])
    return {"message": "Success", "enabled_spaces": enabled_spaces}

@workspace_router.post("/{workspace_id}/spaces/{space}")
async def toggle_space(
    workspace_id: str,
    space: ItemSpace,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    space_dao: SpaceDAO = Depends(SpaceDAO)
    ):
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Toggle the space and get the updated workspace
    updated_workspace = await workspace_dao.toggle_space(workspace, space, user["user_id"])
    
    # Get the enabled spaces
    enabled_spaces = await space_dao.get_enabled_spaces(workspace_id, user["user_id"])
    
    # Return the data in the format expected by the frontend
    return {
        "message": "Space toggled successfully",
        "enabled_spaces": enabled_spaces
    }

@workspace_router.post("/{workspace_id}/subscription/maintain")
async def maintain_subscription(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return await workspace_dao.maintain_subscription(workspace=workspace)

@workspace_router.post("/{workspace_id}/subscription/cancel")
async def cancel_subscription(
    workspace_id: str,
    expires_at: datetime,
    user: User = Depends(get_current_user),
    workspace_dao : WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return await workspace_dao.cancel_subscription(workspace, expires_at)


@workspace_router.get("/{workspace_id}/members", response_model=List[Dict[str, Any]])
async def list_members(
    workspace_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    """
    Get all members of a workspace with their roles.
    
    This endpoint retrieves all members of a workspace, including their roles.
    """
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if the current user is a member of the workspace
    members = await workspace_dao.get_workspace_members(workspace_id)
    current_user_member = next((m for m in members if m["id"] == user["user_id"]), None)
    
    if not current_user_member:
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    
    return members

@workspace_router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    user_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    """
    Remove a member from a workspace.
    
    This endpoint removes a member from a workspace. Only workspace owners and admins can remove members.
    """
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if the current user has permission to remove members
    members = await workspace_dao.get_workspace_members(workspace_id)
    current_user_member = next((m for m in members if m["id"] == user["user_id"]), None)
    
    if not current_user_member:
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    
    if current_user_member["role"] not in [WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="You don't have permission to remove members")
    
    # Remove the member
    await workspace_dao.remove_workspace_member(workspace_id, user_id)
    
    return {"message": "Member removed successfully"}

@workspace_router.put("/{workspace_id}/members/{user_id}/role")
async def update_member_role(
    workspace_id: str,
    user_id: str,
    role_data: WorkspaceMemberRoleUpdate,
    user: Dict[str, Any] = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    """
    Update a member's role in a workspace.
    
    This endpoint updates a member's role in a workspace. Only workspace owners and admins can update roles.
    """
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if the current user has permission to update roles
    members = await workspace_dao.get_workspace_members(workspace_id)
    current_user_member = next((m for m in members if m["id"] == user["user_id"]), None)
    
    if not current_user_member:
        raise HTTPException(status_code=403, detail="You are not a member of this workspace")
    
    if current_user_member["role"] not in [WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="You don't have permission to update roles")
    
    # Update the member's role
    await workspace_dao.update_member_role(workspace_id, user_id, role_data.role.value)
    
    return {"message": "Member role updated successfully"}

@workspace_router.post("/{workspace_id}/transfer-ownership/{new_owner_id}")
async def transfer_workspace_ownership(
    workspace_id: str,
    new_owner_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    """
    Transfer ownership of a workspace to another user.
    
    This endpoint transfers ownership of a workspace to another user. Only the workspace owner can transfer ownership.
    """
    # Get the workspace
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if the current user is the owner
    if workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Only the workspace owner can transfer ownership")
    
    # Transfer ownership
    await workspace_dao.transfer_ownership(workspace_id, user["user_id"], new_owner_id)
    
    return {"message": "Workspace ownership transferred successfully"}
