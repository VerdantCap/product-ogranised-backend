import logging
from fastapi import HTTPException, Depends, Query, status 
from fastapi.responses import RedirectResponse
from models.user_model import User  
from services.auth_service import get_current_user
from services.event_service import EventService
from daos.workspace_dao import WorkspaceDAO
from daos.event_dao import EventDAO
from daos.activity_dao import ActivityDAO
from utils.route import APIRouter
from schemas import Event, EventCreate, EventUpdate
from datetime import datetime

# Create a new API router for event-related endpoints
event_router = APIRouter()

# Set up a logger for the event controller
logger = logging.getLogger(__name__)

# Create a dependency for the EventService
def get_event_service(
    event_dao: EventDAO = Depends(EventDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    activity_dao: ActivityDAO = Depends(ActivityDAO)
) -> EventService:
    return EventService(event_dao, workspace_dao, activity_dao)

@event_router.get("/")
async def list_events(
    user: User = Depends(get_current_user),
    events_dao: EventDAO= Depends(EventDAO),
    start: datetime = Query(..., description="Start date for events"),
    end: datetime = Query(..., description="End date for events"),
    include_google: bool = Query(False, description="Include Google Calendar events"),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    event_service: EventService = Depends(get_event_service),
    ):
    """
    Get events within a date range.
    """
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
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    event_service: EventService = Depends(get_event_service),
    ):
    """
    Create a new event.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    
    try:
        # Validate event dates
        if data.start_at and data.end_at and data.start_at > data.end_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event end time must be after start time"
            )
            
        # Use the event service to create the event
        created_event = await event_service.create_event(
            user_id=user["user_id"],
            event_data=data.dict()
        )
        
        return created_event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@event_router.get("/{event_id}")
async def get_event(
    event_id: str,
    user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    ):
    """
    Get an event by ID.
    """
    try:
        event = await event_service.get_event_by_id(event_id)
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting event: {str(e)}")

@event_router.put("/{event_id}/update")
async def update_event(
    event_id: str,
    event_up: EventUpdate,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    event_service: EventService = Depends(get_event_service),
    ):
    """
    Update an existing event.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    
    try:
        # Validate event dates
        if event_up.start_at and event_up.end_at and event_up.start_at > event_up.end_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event end time must be after start time"
            )
            
        # Use the event service to update the event
        updated_event = await event_service.update_event(
            user_id=user["user_id"],
            event_id=event_id,
            event_data=event_up.dict(exclude_unset=True)
        )
        
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
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    event_service: EventService = Depends(get_event_service),
    ):
    """
    Delete an event.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    
    try:
        # Use the event service to delete the event
        result = await event_service.delete_event(
            user_id=user["user_id"],
            event_id=event_id
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")

@event_router.get("/date/{date}")
async def get_events_by_date(
    date: str,
    user: User = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    event_service: EventService = Depends(get_event_service),
    ):
    """
    Get events for a specific date.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    
    try:
        # Use the event service to get events by date
        events = await event_service.get_events_by_date(
            user_id=user["user_id"],
            date_str=date
        )
        
        return events
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error getting events by date: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting events by date: {str(e)}")

@event_router.get("/upcoming")
async def get_upcoming_events(
    user: User = Depends(get_current_user),
    skip: int = Query(0, description="Skip events"),
    limit: int = Query(100, description="Limit events"),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
    event_service: EventService = Depends(get_event_service),
    ):
    """
    Get upcoming events.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no workspaces"
        )
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    
    try:
        # Use the event service to get upcoming events
        events = await event_service.get_upcoming_events(
            user_id=user["user_id"],
            skip=skip,
            limit=limit
        )
        
        return events
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting upcoming events: {str(e)}")
