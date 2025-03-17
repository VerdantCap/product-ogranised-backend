import logging
import uuid
from fastapi import HTTPException, Depends  
from fastapi.responses import RedirectResponse
from models.user_model import User
from models.workspace_model import Workspace
from services.auth_service import get_current_user
from utils.route import APIRouter
from schemas import WorkspaceCreate, WorkspaceUpdate
from daos.workspace_dao import WorkspaceDAO
from daos.auth_dao import AuthDAO
from services.stripe_service import StripeService
from enums import ItemSpace
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
    auth_dao: AuthDAO = Depends(AuthDAO)
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
        spaces_order=data.spaces_order,
        billing_plan=data.plan
    )
    
    # Save workspace to database and get refreshed instance
    workspace = await workspace_dao.create_workspace(workspace)

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
    if workspace_up.spaces_order is not None:
        workspace.spaces_order = workspace_up.spaces_order
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

@workspace_router.get("/{workspace_id}/refresh-spaces")
async def refresh_spaces(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    """
    Refresh workspace spaces.

    This function refreshes the enabled spaces for a workspace based on the provided workspace ID.

    Returns the enabled spaces in the workspace.
    """
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if workspace.owner_id == user["user_id"]:
        return {"enabled_spaces": workspace.enabled_spaces_ordered()}
    else:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
@workspace_router.post("/{workspace_id}/update-item-space-order") 
async def update_item_space_order(
    workspace_id: str,
    order: list,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ): 
    """
    Update item space order.

    This function updates the order of item spaces in a workspace based on the provided workspace ID and order.

    Returns a message indicating success and the updated enabled spaces.
    """
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace = await workspace_dao.set_spaces(workspace, order)
    return {"message": "Success", "enabled_spaces": workspace.enabled_spaces_ordered()}

@workspace_router.post("/{workspace_id}/spaces/{space}")
async def toggle_space(
    workspace_id: str,
    space: ItemSpace,
    user: User = Depends(get_current_user),
    workspace_dao : WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return await workspace_dao.toggle_space(workspace, space)

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


@workspace_router.get("/{workspace_id}/members")
async def list_members(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)

    if not workspace or workspace.owner_id not in [w.id for w in user.workspaces]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return workspace.users
    
@workspace_router.post("/{workspace_id}/members/{user_id}")
async def add_member(
    workspace_id: str,
    user_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    auth_dao: AuthDAO = Depends(AuthDAO)
    ):
    
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    t_user = await auth_dao.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await auth_dao.join_workspace(t_user, workspace)
    return {"message": "Member added successfully", "status": "success"}

@workspace_router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    user_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    auth_dao: AuthDAO = Depends(AuthDAO)
    ):
    
    workspace = await workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user["user_id"]:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    t_user = await auth_dao.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await auth_dao.leave_workspace(t_user, workspace)
    return {"message": "Member removed successfully", "status": "success"}
