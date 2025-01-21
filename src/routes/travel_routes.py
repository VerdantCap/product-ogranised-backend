from fastapi import APIRouter, Depends
from app.middleware import MetricsMiddleware
from ..main import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])
router.middleware("http")(MetricsMiddleware)

@router.get("/workspace/{workspace_uid}/items/travels/{item_uid}/show", tags=["travels"])
async def show_travel(workspace_uid: str, item_uid: str):
    return {"workspace_uid": workspace_uid, "item_uid": item_uid}

@router.get("/workspace/{workspace_uid}/travel/{item}/transport/create", tags=["transport"])
async def create_transport(workspace_uid: str, item: str):
    return {"workspace_uid": workspace_uid, "item": item}

@router.get("/workspace/{workspace_uid}/travel/{item}/transport/{transport}/edit", tags=["transport"])
async def edit_transport(workspace_uid: str, item: str, transport: int):
    return {"workspace_uid": workspace_uid, "item": item, "transport": transport}

@router.delete("/workspace/{workspace_uid}/travel/{item}/transport/{transport}", tags=["transport"])
async def destroy_transport(workspace_uid: str, item: str, transport: int):
    return {"workspace_uid": workspace_uid, "item": item, "transport": transport}

@router.get("/workspace/{workspace_uid}/travel/{item}/accommodations/create", tags=["accommodations"])
async def create_accommodation(workspace_uid: str, item: str):
    return {"workspace_uid": workspace_uid, "item": item}

@router.get("/workspace/{workspace_uid}/travel/{item}/accommodations/{accommodation}/edit", tags=["accommodations"])
async def edit_accommodation(workspace_uid: str, item: str, accommodation: str):
    return {"workspace_uid": workspace_uid, "item": item, "accommodation": accommodation}

@router.delete("/workspace/{workspace_uid}/travel/{item}/accommodations/{accommodation}", tags=["accommodations"])
async def destroy_accommodation(workspace_uid: str, item: str, accommodation: str):
    return {"workspace_uid": workspace_uid, "item": item, "accommodation": accommodation}

@router.get("/workspace/{workspace_uid}/travel/{item}/excursions/create", tags=["excursions"])
async def create_excursion(workspace_uid: str, item: str):
    return {"workspace_uid": workspace_uid, "item": item}

@router.get("/workspace/{workspace_uid}/travel/{item}/excursions/{excursion}/edit", tags=["excursions"])
async def edit_excursion(workspace_uid: str, item: str, excursion: str):
    return {"workspace_uid": workspace_uid, "item": item, "excursion": excursion}

@router.delete("/workspace/{workspace_uid}/travel/{item}/excursions/{excursion}", tags=["excursions"])
async def destroy_excursion(workspace_uid: str, item: str, excursion: str):
    return {"workspace_uid": workspace_uid, "item": item, "excursion": excursion}
