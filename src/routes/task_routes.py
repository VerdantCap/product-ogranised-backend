from fastapi import APIRouter, Depends
from app.middleware import MetricsMiddleware
from ..main import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])
router.middleware("http")(MetricsMiddleware)

@router.get("/workspace/{workspace_uid}/tasks", tags=["tasks"])
async def tasks(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/tasks/create", tags=["tasks"])
async def create_task(workspace_uid: str):
    return {"workspace_uid": workspace_uid}

@router.get("/workspace/{workspace_uid}/tasks/{task_uid}", tags=["tasks"])
async def edit_task(workspace_uid: str, task_uid: str):
    return {"workspace_uid": workspace_uid, "task_uid": task_uid}
