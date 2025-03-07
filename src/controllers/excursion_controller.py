import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import uuid4

from models.excursion_model import Excursion
from daos.excursion_dao import ExcursionDAO
from models.user_model import User
from services.auth_service import get_current_user
from utils.route import APIRouter
from schemas import ExcursionCreate, ExcursionUpdate

# Create a router for excursion-related endpoints
excursion_router = APIRouter()

# Set up a logger for the excursion controller
logger = logging.getLogger(__name__)

@excursion_router.get("/list")
async def list_excursions(
    skip: int = Query(0, description="Skip excursions"),
    limit: int = Query(100, description="Limit excursions"),
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO),
):
    """
    Get all excursions with pagination.
    """
    return excursion_dao.get_multi(skip, limit)

@excursion_router.get("/by-item/{item_id}")
async def get_excursions_by_item(
    item_id: str,
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO),
):
    """
    Get excursions by item ID.
    """
    return excursion_dao.get_by_item(item_id)

@excursion_router.get("/{excursion_id}")
async def get_excursion(
    excursion_id: str,
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO),
):
    """
    Get a specific excursion by ID.
    """
    excursion = excursion_dao.get_by_id(excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Excursion not found")
    return excursion

@excursion_router.post("/create")
async def create_excursion(
    excursion_data: ExcursionCreate,
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO),
):
    """
    Create a new excursion.
    """
    excursion = Excursion(
        id=str(uuid4()),
        item_id=excursion_data.item_id,
        name=excursion_data.provider,
        booking_ref=excursion_data.booking_ref,
        provider=excursion_data.provider,
        excursion_date=excursion_data.start_time.date(),
        start_time=excursion_data.start_time,
        end_time=excursion_data.end_time,
        contact_number=None,
        contact_email=None,
        total_cost=excursion_data.cost,
        deposit_paid=False,
        deposit_amount=0.0,
        deposit_date=None,
        remaining_balance=excursion_data.cost,
        balance_due_date=None,
        notes=excursion_data.notes,
        attachments=[]
    )
    return excursion_dao.create_excursion(excursion)

@excursion_router.put("/{excursion_id}/update")
async def update_excursion(
    excursion_id: str,
    excursion_data: ExcursionUpdate,
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO),
):
    """
    Update an existing excursion.
    """
    excursion = excursion_dao.get_by_id(excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Excursion not found")
    
    # Update fields that are provided
    if excursion_data.provider:
        excursion.provider = excursion_data.provider
        excursion.name = excursion_data.provider
    if excursion_data.booking_ref:
        excursion.booking_ref = excursion_data.booking_ref
    if excursion_data.location:
        excursion.location = excursion_data.location
    if excursion_data.start_time:
        excursion.start_time = excursion_data.start_time
        excursion.excursion_date = excursion_data.start_time.date()
    if excursion_data.end_time:
        excursion.end_time = excursion_data.end_time
    if excursion_data.cost is not None:
        excursion.total_cost = excursion_data.cost
        excursion.remaining_balance = excursion_data.cost - (excursion.deposit_amount or 0)
    if excursion_data.notes:
        excursion.notes = excursion_data.notes
    
    return excursion_dao.update_excursion(excursion)

@excursion_router.delete("/{excursion_id}/delete")
async def delete_excursion(
    excursion_id: str,
    user: User = Depends(get_current_user),
    excursion_dao: ExcursionDAO = Depends(ExcursionDAO),
):
    """
    Delete an excursion.
    """
    excursion = excursion_dao.get_by_id(excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Excursion not found")
    
    excursion_dao.delete_excursion(excursion)
    return {"detail": "Excursion deleted successfully"}
