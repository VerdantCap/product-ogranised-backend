from fastapi import APIRouter, Depends
from app.middleware import MetricsMiddleware
from ..main import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])
router.middleware("http")(MetricsMiddleware)

@router.get("/workspace/{workspace_uid}/events", tags=["events"])
async def events(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/events/create", tags=["events"])
async def create_event(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/events/list", tags=["events"])
async def list_events(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/events/{event_uid}", tags=["events"])
async def edit_event(workspace_uid: str, event_uid: str):
    return {"workspace_uid": workspace_uid, "event_uid": event_uid}

@router.get("/workspace/{workspace_uid}/events/google/{event_id}/edit", tags=["events"])
async def edit_google_event(workspace_uid: str, event_id: str):
    return {"workspace_uid": workspace_uid, "event_id": event_id}
