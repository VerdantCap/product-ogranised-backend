import logging
from fastapi import HTTPException, Depends, Query  
from fastapi.responses import RedirectResponse
from models.user_model import User  
from services.auth_service import get_current_user
from utils.route import APIRouter
from daos.auth_dao import AuthDAO
from daos.event_dao import EventDAO
from schemas import Event, EventCreate, EventUpdate
# from enums import ItemSpace
from datetime import datetime

# Create a new API router for event-related endpoints
event_router = APIRouter()

# Set up a logger for the event controller
logger = logging.getLogger(__name__)

@event_router.get("/list")
async def list_events(
    user: User = Depends(get_current_user),
    events_dao: EventDAO= Depends(EventDAO),
    start: datetime = Query(..., description="Start date for events"),
    end: datetime = Query(..., description="End date for events"),
    include_google: bool = Query(False, description="Include Google Calendar events"),
    ):
    local_events = await events_dao.get_by_date_range(user.active_workspace_id, start, end)
    
    events = [
        {
            "id": str(event.id),
            "name": event.name,
            "description": event.description,
            "start_at": event.start_at,
            "end_at": event.end_at,
            "source": "local",
        }
        for event in local_events
    ]

    # if include_google and user.is_oauthed:
    #     google_events = await events_dao.get_google_calendar_events(
    #         user = user, 
    #         start=start, 
    #         end= end
    #     )
    #     events.extend(google_events)
    
    return events

@event_router.post("/create")
async def create_event(
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    event_data: EventCreate = Depends(EventCreate),
    ):
    event = Event(
        **event_data.dict(),
        workspace_id = user.active_workspace_id
    )
    return event_dao.create_event(event)

@event_router.get("/{event_id}")
async def get_event(
    event_id: str,
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    ):
    event = event_dao.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@event_router.put("/{event_id}/update")
async def update_event(
    event_id: str,
    event_up: EventUpdate,
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    ):
    event = event_dao.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event_up.name:
        event.name = event_up.name
    if event_up.description:
        event.description = event_up.description
    if event_up.start_at:
        event.start_at = event_up.start_at
    if event_up.end_at:
        event.end_at = event_up.end_at 
    return event_dao.update_event(event)

@event_router.delete("/{event_id}/delete")
async def delete_event(
    event_id: str,
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    ):
    event = event_dao.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event_dao.delete_event(event)

@event_router.get("/upcoming")
async def get_upcoming_events(
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    skip: int = Query(0, description="Skip events"),
    limit: int = Query(100, description="Limit events"),
    ):
    return event_dao.get_upcoming(user.active_workspace_id,skip,limit)
