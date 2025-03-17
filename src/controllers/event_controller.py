import logging
from fastapi import HTTPException, Depends, Query, status 
from fastapi.responses import RedirectResponse
from models.user_model import User  
from services.auth_service import get_current_user
from daos.workspace_dao import WorkspaceDAO
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

@event_router.get("/")
async def list_events(
    user: User = Depends(get_current_user),
    events_dao: EventDAO= Depends(EventDAO),
    start: datetime = Query(..., description="Start date for events"),
    end: datetime = Query(..., description="End date for events"),
    include_google: bool = Query(False, description="Include Google Calendar events"),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    ):
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    local_events = await events_dao.get_by_date_range(workspace_id, start, end)
    
    events = [
        {
            "id": str(event.id),
            "name": event.name,
            "description": event.description,
            "start_at": event.start_at,
            "end_at": event.end_at,
            "lead": event.lead,
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
    data: EventCreate,
    user: User = Depends(get_current_user),
    event_dao: EventDAO = Depends(EventDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    ):
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    try:
        event = Event(
            **data.dict(),
            workspace_id = workspace_id
        )
        created_event = await event_dao.create_event(event)
        
        # Create an activity record for this event creation
        try:
            from daos.activity_dao import ActivityDAO
            activity_dao = ActivityDAO()
            await activity_dao.create_activity(
                user_id=user["user_id"],
                workspace_id=workspace_id,
                activity_type="event_created",
                entity_id=created_event.id,
                entity_type="event",
                details={"title": created_event.name}
            )
        except Exception as e:
            logger.error(f"Error creating activity for event: {e}")
        
        return created_event
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@event_router.get("/{event_id}")
async def get_event(
    event_id: str,
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    ):
    event = await event_dao.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@event_router.put("/{event_id}/update")
async def update_event(
    event_id: str,
    event_up: EventUpdate,
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    ):
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    try:
        event = await event_dao.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Update event fields
        if event_up.name:
            event.name = event_up.name
        if event_up.description:
            event.description = event_up.description
        if event_up.start_at:
            event.start_at = event_up.start_at
        if event_up.end_at:
            event.end_at = event_up.end_at
        if event_up.lead:
            event.lead = event_up.lead
            
        updated_event = await event_dao.update_event(event)
        
        # Create an activity record for this event update
        try:
            from daos.activity_dao import ActivityDAO
            activity_dao = ActivityDAO()
            await activity_dao.create_activity(
                user_id=user["user_id"],
                workspace_id=workspace_id,
                activity_type="event_updated",
                entity_id=updated_event.id,
                entity_type="event",
                details={"title": updated_event.name}
            )
        except Exception as e:
            logger.error(f"Error creating activity for event update: {e}")
        
        return updated_event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")

@event_router.delete("/{event_id}/delete")
async def delete_event(
    event_id: str,
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    ):
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    try:
        event = await event_dao.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Store event details before deletion for activity logging
        event_name = event.name
        
        # Delete the event
        await event_dao.delete_event(event)
        
        # Create an activity record for this event deletion
        try:
            from daos.activity_dao import ActivityDAO
            activity_dao = ActivityDAO()
            await activity_dao.create_activity(
                user_id=user["user_id"],
                workspace_id=workspace_id,
                activity_type="event_deleted",
                entity_id=event_id,
                entity_type="event",
                details={"title": event_name}
            )
        except Exception as e:
            logger.error(f"Error creating activity for event deletion: {e}")
        
        return {"detail": "Event deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")

@event_router.get("/date/{date}")
async def get_events_by_date(
    date: str,
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    ):
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    # Convert date string to datetime objects for start and end of day
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        start = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0)
        end = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59)
        
        events = await event_dao.get_by_date_range(workspace_id, start, end)
        return [
            {
                "id": str(event.id),
                "name": event.name,
                "description": event.description,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "lead": event.lead,
                "source": "local",
            }
            for event in events
        ]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

@event_router.get("/upcoming")
async def get_upcoming_events(
    user: User = Depends(get_current_user),
    event_dao: EventDAO= Depends(EventDAO),
    skip: int = Query(0, description="Skip events"),
    limit: int = Query(100, description="Limit events"),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    ):
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    try:
        # Get current date and time
        now = datetime.now()
        
        # Get events that start after the current time
        upcoming_events = await event_dao.get_upcoming_events(
            workspace_id=workspace_id,
            from_date=now,
            skip=skip,
            limit=limit
        )
        
        return [
            {
                "id": str(event.id),
                "name": event.name,
                "description": event.description,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "lead": event.lead,
                "source": "local",
            }
            for event in upcoming_events
        ]
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting upcoming events: {str(e)}")
