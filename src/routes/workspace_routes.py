from fastapi import APIRouter, Depends
from app.middleware import MetricsMiddleware
from ..main import get_current_user
from app.complete_onboarding import complete_onboarding

router = APIRouter(dependencies=[Depends(get_current_user)])
router.include_router(complete_onboarding.router, prefix="/workspace")
router.middleware("http")(MetricsMiddleware)

@router.get("/workspace/setup", tags=["workspace"])
async def workspace_setup():
    return {"message": "Workspace Setup"}

@router.get("/workspace/setup/complete", tags=["workspace"])
async def workspace_setup_complete():
    return {"message": "Workspace Setup Complete"}

@router.get("/workspace/{workspace_uid}/manage", tags=["workspace"])
async def manage_subscription(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/expired", tags=["workspace"])
async def renewal_required(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/dashboard", tags=["workspace"])
async def dashboard(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/", tags=["workspace"])
async def workspace_dashboard(workspace_uid: str):
    return {"workspace_uid": workspace_uid}
