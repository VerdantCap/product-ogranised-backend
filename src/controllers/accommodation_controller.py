import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import uuid4

from models.accommodation_model import Accommodation
from daos.accommodation_dao import AccommodationDAO
from models.user_model import User
from services.auth_service import get_current_user
from utils.route import APIRouter
from schemas import AccommodationCreate, AccommodationUpdate

# Create a router for accommodation-related endpoints
accommodation_router = APIRouter()

# Set up a logger for the accommodation controller
logger = logging.getLogger(__name__)

@accommodation_router.get("/list")
async def list_accommodations(
    skip: int = Query(0, description="Skip accommodations"),
    limit: int = Query(100, description="Limit accommodations"),
    user: User = Depends(get_current_user),
    accommodation_dao: AccommodationDAO = Depends(AccommodationDAO),
):
    """
    Get all accommodations with pagination.
    """
    return accommodation_dao.get_multi(skip, limit)

@accommodation_router.get("/by-item/{item_id}")
async def get_accommodations_by_item(
    item_id: str,
    user: User = Depends(get_current_user),
    accommodation_dao: AccommodationDAO = Depends(AccommodationDAO),
):
    """
    Get accommodations by item ID.
    """
    return accommodation_dao.get_by_item(item_id)

@accommodation_router.get("/{accommodation_id}")
async def get_accommodation(
    accommodation_id: str,
    user: User = Depends(get_current_user),
    accommodation_dao: AccommodationDAO = Depends(AccommodationDAO),
):
    """
    Get a specific accommodation by ID.
    """
    accommodation = accommodation_dao.get_by_id(accommodation_id)
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return accommodation

@accommodation_router.post("/create")
async def create_accommodation(
    accommodation_data: AccommodationCreate,
    user: User = Depends(get_current_user),
    accommodation_dao: AccommodationDAO = Depends(AccommodationDAO),
):
    """
    Create a new accommodation.
    """
    accommodation = Accommodation(
        id=str(uuid4()),
        item_id=accommodation_data.item_id,
        name=accommodation_data.provider,
        booking_ref=accommodation_data.booking_reference,
        provider=accommodation_data.provider,
        arrival_date=accommodation_data.check_in.date(),
        departure_date=accommodation_data.check_out.date(),
        contact_number=None,
        contact_email=None,
        food_drink_included=False,
        total_cost=accommodation_data.cost,
        deposit_paid=False,
        deposit_amount=0.0,
        deposit_date=None,
        remaining_balance=accommodation_data.cost,
        balance_due_date=None,
        notes=accommodation_data.notes,
        attachments=[]
    )
    return accommodation_dao.create_accommodation(accommodation)

@accommodation_router.put("/{accommodation_id}/update")
async def update_accommodation(
    accommodation_id: str,
    accommodation_data: AccommodationUpdate,
    user: User = Depends(get_current_user),
    accommodation_dao: AccommodationDAO = Depends(AccommodationDAO),
):
    """
    Update an existing accommodation.
    """
    accommodation = accommodation_dao.get_by_id(accommodation_id)
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    
    # Update fields that are provided
    if accommodation_data.provider:
        accommodation.provider = accommodation_data.provider
        accommodation.name = accommodation_data.provider
    if accommodation_data.booking_reference:
        accommodation.booking_ref = accommodation_data.booking_reference
    if accommodation_data.location:
        accommodation.location = accommodation_data.location
    if accommodation_data.check_in:
        accommodation.arrival_date = accommodation_data.check_in.date()
    if accommodation_data.check_out:
        accommodation.departure_date = accommodation_data.check_out.date()
    if accommodation_data.cost is not None:
        accommodation.total_cost = accommodation_data.cost
        accommodation.remaining_balance = accommodation_data.cost - (accommodation.deposit_amount or 0)
    if accommodation_data.notes:
        accommodation.notes = accommodation_data.notes
    
    return accommodation_dao.update_accommodation(accommodation)

@accommodation_router.delete("/{accommodation_id}/delete")
async def delete_accommodation(
    accommodation_id: str,
    user: User = Depends(get_current_user),
    accommodation_dao: AccommodationDAO = Depends(AccommodationDAO),
):
    """
    Delete an accommodation.
    """
    accommodation = accommodation_dao.get_by_id(accommodation_id)
    if not accommodation:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    
    accommodation_dao.delete_accommodation(accommodation)
    return {"detail": "Accommodation deleted successfully"}
