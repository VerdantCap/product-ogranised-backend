import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import uuid4

from models.transport_model import Transport
from daos.transport_dao import TransportDAO
from models.user_model import User
from services.auth_service import get_current_user
from utils.route import APIRouter
from schemas import TransportCreate, TransportUpdate

# Create a router for transport-related endpoints
transport_router = APIRouter()

# Set up a logger for the transport controller
logger = logging.getLogger(__name__)

@transport_router.get("/list")
async def list_transports(
    skip: int = Query(0, description="Skip transports"),
    limit: int = Query(100, description="Limit transports"),
    user: User = Depends(get_current_user),
    transport_dao: TransportDAO = Depends(TransportDAO),
):
    """
    Get all transports with pagination.
    """
    return transport_dao.get_multi(skip, limit)

@transport_router.get("/by-item/{item_id}")
async def get_transports_by_item(
    item_id: str,
    user: User = Depends(get_current_user),
    transport_dao: TransportDAO = Depends(TransportDAO),
):
    """
    Get transports by item ID.
    """
    return transport_dao.get_by_item(item_id)

@transport_router.get("/{transport_id}")
async def get_transport(
    transport_id: str,
    user: User = Depends(get_current_user),
    transport_dao: TransportDAO = Depends(TransportDAO),
):
    """
    Get a specific transport by ID.
    """
    transport = transport_dao.get_by_id(transport_id)
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    return transport

@transport_router.post("/create")
async def create_transport(
    transport_data: TransportCreate,
    user: User = Depends(get_current_user),
    transport_dao: TransportDAO = Depends(TransportDAO),
):
    """
    Create a new transport.
    """
    transport = Transport(
        id=str(uuid4()),
        item_id=transport_data.item_id,
        transport_mode=transport_data.type,
        trip_type="one-way" if transport_data.arrival_time else "round-trip",
        details={
            "provider": transport_data.provider,
            "booking_reference": transport_data.booking_reference,
            "departure_location": transport_data.departure_location,
            "arrival_location": transport_data.arrival_location,
            "departure_time": transport_data.departure_time.isoformat() if transport_data.departure_time else None,
            "arrival_time": transport_data.arrival_time.isoformat() if transport_data.arrival_time else None,
            "cost": transport_data.cost,
            "currency": transport_data.currency,
            "notes": transport_data.notes
        }
    )
    return transport_dao.create_transport(transport)

@transport_router.put("/{transport_id}/update")
async def update_transport(
    transport_id: str,
    transport_data: TransportUpdate,
    user: User = Depends(get_current_user),
    transport_dao: TransportDAO = Depends(TransportDAO),
):
    """
    Update an existing transport.
    """
    transport = transport_dao.get_by_id(transport_id)
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    # Update fields that are provided
    if transport_data.type:
        transport.transport_mode = transport_data.type
    
    # Update details dictionary
    details = transport.details or {}
    
    if transport_data.provider:
        details["provider"] = transport_data.provider
    if transport_data.booking_reference:
        details["booking_reference"] = transport_data.booking_reference
    if transport_data.departure_location:
        details["departure_location"] = transport_data.departure_location
    if transport_data.arrival_location:
        details["arrival_location"] = transport_data.arrival_location
    if transport_data.departure_time:
        details["departure_time"] = transport_data.departure_time.isoformat()
    if transport_data.arrival_time:
        details["arrival_time"] = transport_data.arrival_time.isoformat()
    if transport_data.cost is not None:
        details["cost"] = transport_data.cost
    if transport_data.currency:
        details["currency"] = transport_data.currency
    if transport_data.notes:
        details["notes"] = transport_data.notes
    
    transport.details = details
    
    # Update trip_type based on arrival_time
    if "arrival_time" in details:
        transport.trip_type = "one-way" if details["arrival_time"] else "round-trip"
    
    return transport_dao.update_transport(transport)

@transport_router.delete("/{transport_id}/delete")
async def delete_transport(
    transport_id: str,
    user: User = Depends(get_current_user),
    transport_dao: TransportDAO = Depends(TransportDAO),
):
    """
    Delete a transport.
    """
    transport = transport_dao.get_by_id(transport_id)
    if not transport:
        raise HTTPException(status_code=404, detail="Transport not found")
    
    transport_dao.delete_transport(transport)
    return {"detail": "Transport deleted successfully"}
