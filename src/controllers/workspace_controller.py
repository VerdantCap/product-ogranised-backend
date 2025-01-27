import logging
from fastapi import HTTPException, Depends  
from fastapi.responses import RedirectResponse
from models.user_model import User  
from services.auth_service import get_current_user
from utils.route import APIRouter
from schemas.workspace_schema import WorkspaceCreate, WorkspaceUpdate
from daos.workspace_dao import WorkspaceDAO
from daos.auth_dao import AuthDAO
from daos.event_dao import EventDAO
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
    stripe_service: StripeService = Depends(StripeService)
    ):  
    """
    Create a new workspace.

    This function handles the creation of a new workspace, including validation of the HMAC hash,
    retrieval of Stripe session and subscription, and user joining the workspace.

    Returns a redirect response to the dashboard with the newly created workspace.
    """
    # Validate HMAC hash  
    hash_data = {  
        'plan': data.plan,  
        'uid': data.workspace,  
        'user': data.user,  
        'workspace': data.workspace,  
        'spaces': data.spaces,  
    }  

    if not stripe_service.verify_hash(hash_data, data.hash):  
        raise HTTPException(status_code=400, detail="Invalid hash")  

    if data.user != user.id:  
        raise HTTPException(status_code=401, detail="Unauthorized")  

    # Retrieve Stripe session  
    session = await stripe_service.retrieve_stripe_session(data.session_id)  
    if data.workspace != session.client_reference_id:  
        raise HTTPException(status_code=400, detail="Invalid client reference")  

    # Retrieve Stripe subscription  
    subscription = await stripe_service.retrieve_stripe_subscription(session.subscription)  
    if subscription.status != 'active':  
        raise HTTPException(status_code=400, detail="Inactive subscription")  

    # Create workspace  
    workspace = workspace_dao.create_workspace(  
        name=data.workspace.strip(),  
        billing_plan=data.plan,  
        stripe_id=subscription.id,  
        user_id=user.id,  
        selected_spaces=data.spaces  
    )  

    # User joins workspace  
    user.join_workspace(workspace)  

    return RedirectResponse(url=f"/dashboard?workspace={workspace['name']}")

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
    workspace = await workspace.get_workspace_by_id(workspace_id)  
    if workspace.owner_id != user.id:  
        raise HTTPException(status_code=403, detail="Access forbidden")  

    subscription_id = workspace.stripe_id  
    if not subscription_id:  
        raise HTTPException(status_code=400, detail="Bad request: No subscription ID found") 

    try:  
        subscription = stripe_service.retrieve_stripe_subscription(subscription_id)  
        portal = stripe_service.create_billing_portal_session(subscription, "settings")  
        RedirectResponse(url = portal.url)
    except HTTPException as e:
        raise e
    except Exception:  
        return RedirectResponse(url="home")
    

@workspace_router.put("/{workspace_id}/update")
async def update_workspace(
    workspace_id: str,
    workspace_up: WorkspaceUpdate,
    user: User= Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if workspace.owner_id != current_user.id or not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    else:
        
        return workspace_dao.update_workspace(workspace)


@workspace_router.delete("/{workspace_id}/delete")
async def delete_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO) 
    ):
    workspace = workspace_dao.get_workspace_by_id(workspace_id)

    if not workpsace or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    else:
        workspace_dao.delete_workspace(workspace_id=workspace_id)

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
    if not workspace or workspace.owner_id != user.id:  
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
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if workspace.owner_id == user.id:
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
    workspace = workspace_dao.get_workspace_by_id(workspace_dao)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace = workspace_dao.set_spaces(workspace, order)
    return {"message": "Success", "enabled_spaces": workspace.enabled_spaces_ordered()}

@router.post("/{workspace_id}/spaces/{space}")
async def toggle_space(
    workspace_id: str,
    space: ItemSpace,
    user: User = Depends(get_current_user),
    workspace_dao : WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace_dao.toggle_space()

@workspace_router.post("/{workspace_id}/subscription/maintain")
async def maintain_subscription(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return workspace_dao.maintain_subscription(workspace=workspace)

@workspace_router.post("/{workspace_id}/subscription/cancel")
async def cancel_subscription(
    workspace_id: str,
    expires_at: datetime,
    user: User = Depends(get_current_user),
    workspace_dao : WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return workspace_dao.cancel_subscription(workspace, expires_at)

@workspace_router.post("/{workspace_id}/set-active")
async def set_active_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    auth_dao: AuthDAO = Depends(AuthDAO)
    ):
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return auth_dao.set_active_workspace(user, workspace)



@workspace_router.get("/{workspace_id}/members")
async def list_members(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO)
    ):
    workspace = workspace_dao.get_workspace_by_id(workspace_id)

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
    
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    t_user = auth_dao.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    auth_dao.join_workspace(t_user, workspace)
    return {"message": "Member added successfully", "status": "success"}

@workspace_router.delete("/{workspace_id}/members/{user_id}")
async def add_member(
    workspace_id: str,
    user_id: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    auth_dao: AuthDAO = Depends(AuthDAO)
    ):
    
    workspace = workspace_dao.get_workspace_by_id(workspace_id)
    if not workspace or workspace.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    t_user = auth_dao.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    auth_dao.leave_workspace(t_user, workspace)
    return {"message": "Member removed successfully", "status": "success"}