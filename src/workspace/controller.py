import logging
from fastapi import HTTPException, Depends, Request  
from fastapi.responses import RedirectResponse  
from workspace.service import WorkspaceService
from models.user_model import User  
from auth.service import get_current_user
from utils.route import APIRouter
from workspace.schema import OnboardingRequest
from workspace.service import WorkspaceService

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/create")  
async def create_workspace(
    data: OnboardingRequest, 
    user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(WorkspaceService)
    ):  
    # Validate HMAC hash  
    hash_data = {  
        'plan': data.plan,  
        'uid': data.workspace,  
        'user': data.user,  
        'workspace': data.workspace,  
        'spaces': data.spaces,  
    }  

    if not workspace_service.verify_hash(hash_data, data.hash):  
        raise HTTPException(status_code=400, detail="Invalid hash")  

    if data.user != user.id:  
        raise HTTPException(status_code=401, detail="Unauthorized")  

    # Retrieve Stripe session  
    session = await workspace_service.retrieve_stripe_session(data.session_id)  
    if data.workspace != session.client_reference_id:  
        raise HTTPException(status_code=400, detail="Invalid client reference")  

    # Retrieve Stripe subscription  
    subscription = await workspace_service.retrieve_stripe_subscription(session.subscription)  
    if subscription.status != 'active':  
        raise HTTPException(status_code=400, detail="Inactive subscription")  

    # Create workspace  
    workspace = workspace_service.create_workspace(  
        name=data.workspace.strip(),  
        billing_plan=data.plan,  
        stripe_id=subscription.id,  
        user_id=user.id,  
        selected_spaces=data.spaces  
    )  

    # User joins workspace  
    user.join_workspace(workspace)  

    return RedirectResponse(url=f"/dashboard?workspace={workspace['name']}")

@router.get('/{workspace_id}/manage')
async def manage_workspace(
    workspace_id: str,
    user: User=Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(WorkspaceService)
    ): 
    workspace = await workspace.get_workspace(workspace_id)  
    if workspace.owner_id != user.id:  
        raise HTTPException(status_code=403, detail="Access forbidden")  

    subscription_id = workspace.stripe_id  
    if not subscription_id:  
        raise HTTPException(status_code=400, detail="Bad request: No subscription ID found") 

    try:  
        subscription = workspace_service.retrieve_stripe_subscription(subscription_id)  
        portal = workspace_service.create_billing_portal_session(subscription, "settings")  
        RedirectResponse(url = portal.url)
    except HTTPException as e:
        raise e
    except Exception:  
        return RedirectResponse(url="home")
    

@router.get("/{workspace_id}/renewal-required")  
async def renewal_required(
    workspace_id: str,
    user: User=Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(WorkspaceService)
    ):  
    # Fetch the workspace based on the provided workspace_id  
    workspace = await workspace_service.get_workspace(workspace_id) 
    if not workspace or workspace.owner_id != user.id:  
        raise HTTPException(status_code=404, detail="Workspace not found")    
    if workspace.has_active_subscription():
        return RedirectResponse(url=f"/dashboard?workspace_id={workspace.id}")  
    return {"message": "Please renew your subscription."}  

@router.get("/{workspace_id}/refresh-spaces")
async def refresh_spaces(
    workspace_id: str,
    user: User = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(WorkspaceService)
    ):
    workspace = workspace_service.get_workspace(workspace_id)
    if workspace.owner_id == user.id:
        return {"enabled_spaces": workspace.enabled_spaces_ordered()}
    else:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
@router.post("/{workspace_id}/update-item-space-order") 
async def update_item_space_order(
    workspace_id: str,
    order: list,
    workspace_service: WorkspaceService = Depends(WorkspaceService)
    ): 
    workspace = workspace_service.get_workspace(workspace_id)
    workspace = workspace_service.update_workspace(workspace, order)

    return {"message": "Success", "enabled_spaces": workspace.enabled_spaces_ordered()}