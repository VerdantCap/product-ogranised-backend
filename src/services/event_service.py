import logging
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from models.event_model import Event
from daos.event_dao import EventDAO
from daos.workspace_dao import WorkspaceDAO
from daos.activity_dao import ActivityDAO
from uuid import uuid4

# Set up a logger for the event service
logger = logging.getLogger(__name__)

class EventService:
    """
    Service layer for Event operations.
    
    This class provides methods to handle business logic for Event operations,
    separating it from the controller and data access layers.
    """
    
    def __init__(
        self,
        event_dao: EventDAO,
        workspace_dao: WorkspaceDAO,
        activity_dao: ActivityDAO
    ):
        self.event_dao = event_dao
        self.workspace_dao = workspace_dao
        self.activity_dao = activity_dao
    
    async def get_events_by_date_range(self, user_id: str, start: datetime, end: datetime, include_google: bool = False) -> List[dict]:
        """
        Get events within a date range for a user's workspace.
        
        Args:
            user_id: The ID of the user
            start: Start date for events
            end: End date for events
            include_google: Whether to include Google Calendar events
            
        Returns:
            List of events formatted for the API response
        """
        # Get user's workspaces
        workspaces = await self.workspace_dao.get_workspaces_by_user_id(user_id)
        
        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no workspaces"
            )
        
        # Use the first workspace's ID (this could be enhanced to support multiple workspaces)
        workspace_id = workspaces[0].id
        local_events = await self.event_dao.get_by_date_range(workspace_id, start, end)
        
        events = [
            {
                "id": str(event.id),
                "name": event.name,
                "description": event.description,
                "location": event.location,
                "start_at": event.start_at,
                "end_at": event.end_at,
                "lead": event.lead,
                "source": "local",
            }
            for event in local_events
        ]
        
        # Google Calendar integration could be implemented here
        # if include_google and user.is_oauthed:
        #     google_events = await self.get_google_calendar_events(user, start, end)
        #     events.extend(google_events)
        
        return events
    
    async def create_event(self, user_id: str, event_data: dict) -> Event:
        """
        Create a new event.
        
        Args:
            user_id: The ID of the user creating the event
            event_data: Event data from the request
            
        Returns:
            The created Event object
        """
        # Get user's workspaces
        workspaces = await self.workspace_dao.get_workspaces_by_user_id(user_id)
        
        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no workspaces"
            )
        
        # Use the first workspace's ID
        workspace_id = workspaces[0].id
        
        # Validate event dates
        start_at = event_data.get("start_at")
        end_at = event_data.get("end_at")
        
        if start_at and end_at and start_at > end_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event end time must be after start time"
            )
        
        try:
            # Create a new event with a UUID
            event = Event(
                id=str(uuid4()),
                workspace_id=workspace_id,
                **event_data
            )
            
            created_event = await self.event_dao.create_event(event)
            
            # Create an activity record for this event creation
            try:
                await self.activity_dao.create_activity(
                    user_id=user_id,
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error creating event: {str(e)}"
            )
    
    async def get_event_by_id(self, event_id: str) -> Event:
        """
        Get an event by ID.
        
        Args:
            event_id: The ID of the event to retrieve
            
        Returns:
            The Event object
        """
        event = await self.event_dao.get_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        return event
    
    async def update_event(self, user_id: str, event_id: str, event_data: dict) -> Event:
        """
        Update an existing event.
        
        Args:
            user_id: The ID of the user updating the event
            event_id: The ID of the event to update
            event_data: Updated event data
            
        Returns:
            The updated Event object
        """
        # Get user's workspaces
        workspaces = await self.workspace_dao.get_workspaces_by_user_id(user_id)
        
        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no workspaces"
            )
        
        # Use the first workspace's ID
        workspace_id = workspaces[0].id
        
        try:
            # Get the existing event
            event = await self.event_dao.get_by_id(event_id)
            if not event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found"
                )
            
            # Update event fields
            if "name" in event_data and event_data["name"]:
                event.name = event_data["name"]
            if "description" in event_data and event_data["description"] is not None:
                event.description = event_data["description"]
            if "location" in event_data and event_data["location"] is not None:
                event.location = event_data["location"]
            if "start_at" in event_data and event_data["start_at"]:
                event.start_at = event_data["start_at"]
            if "end_at" in event_data and event_data["end_at"]:
                event.end_at = event_data["end_at"]
            if "lead" in event_data and event_data["lead"] is not None:
                event.lead = event_data["lead"]
            
            # Validate event dates
            if event.start_at and event.end_at and event.start_at > event.end_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Event end time must be after start time"
                )
            
            updated_event = await self.event_dao.update_event(event)
            
            # Create an activity record for this event update
            try:
                await self.activity_dao.create_activity(
                    user_id=user_id,
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating event: {str(e)}"
            )
    
    async def delete_event(self, user_id: str, event_id: str) -> dict:
        """
        Delete an event.
        
        Args:
            user_id: The ID of the user deleting the event
            event_id: The ID of the event to delete
            
        Returns:
            A success message
        """
        # Get user's workspaces
        workspaces = await self.workspace_dao.get_workspaces_by_user_id(user_id)
        
        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no workspaces"
            )
        
        # Use the first workspace's ID
        workspace_id = workspaces[0].id
        
        try:
            # Get the event to delete
            event = await self.event_dao.get_by_id(event_id)
            if not event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Event not found"
                )
            
            # Store event details before deletion for activity logging
            event_name = event.name
            
            # Delete the event
            await self.event_dao.delete_event(event)
            
            # Create an activity record for this event deletion
            try:
                await self.activity_dao.create_activity(
                    user_id=user_id,
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting event: {str(e)}"
            )
    
    async def get_events_by_date(self, user_id: str, date_str: str) -> List[dict]:
        """
        Get events for a specific date.
        
        Args:
            user_id: The ID of the user
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            List of events formatted for the API response
        """
        # Get user's workspaces
        workspaces = await self.workspace_dao.get_workspaces_by_user_id(user_id)
        
        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no workspaces"
            )
        
        # Use the first workspace's ID
        workspace_id = workspaces[0].id
        
        # Convert date string to datetime objects for start and end of day
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            start = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0)
            end = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59)
            
            events = await self.event_dao.get_by_date_range(workspace_id, start, end)
            return [
                {
                    "id": str(event.id),
                    "name": event.name,
                    "description": event.description,
                    "location": event.location,
                    "start_at": event.start_at,
                    "end_at": event.end_at,
                    "lead": event.lead,
                    "source": "local",
                }
                for event in events
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    
    async def get_upcoming_events(self, user_id: str, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        Get upcoming events.
        
        Args:
            user_id: The ID of the user
            skip: Number of events to skip
            limit: Maximum number of events to return
            
        Returns:
            List of events formatted for the API response
        """
        # Get user's workspaces
        workspaces = await self.workspace_dao.get_workspaces_by_user_id(user_id)
        
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
            upcoming_events = await self.event_dao.get_upcoming_events(
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
                    "location": event.location,
                    "start_at": event.start_at,
                    "end_at": event.end_at,
                    "lead": event.lead,
                    "source": "local",
                }
                for event in upcoming_events
            ]
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting upcoming events: {str(e)}"
            )
