from fastapi import APIRouter, Depends
from app.middleware import MetricsMiddleware
from ..main import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])
router.middleware("http")(MetricsMiddleware)

@router.get("/workspace/{workspace_uid}/items/{space}", tags=["items"])
async def list_items(workspace_uid: str, space: str):
    return {"workspace_uid": workspace_uid, "space": space}

@router.get("/workspace/{workspace_uid}/items/{space}/create", tags=["items"])
async def create_item(workspace_uid: str, space: str):
    return {"workspace_uid": workspace_uid, "space": space}

@router.get("/workspace/{workspace_uid}/items/{space}/{item_uid}", tags=["items"])
async def edit_item(workspace_uid: str, space: str, item_uid: str):
    return {"workspace_uid": workspace_uid, "space": space, "item_uid": item_uid}
