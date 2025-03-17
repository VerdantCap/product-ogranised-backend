import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel

from models.user_model import User
from models.activity_model import Activity
from daos.activity_dao import ActivityDAO
from daos.workspace_dao import WorkspaceDAO
from services.auth_service import get_current_user
from utils.route import APIRouter

# Create a router for activity-related endpoints
activity_router = APIRouter()

# Set up a logger for the activity controller
logger = logging.getLogger(__name__)

# Define request and response models
class ActivityCreate(BaseModel):
    activity_type: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    details: Optional[dict] = None

class ActivityResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    type: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    class Config:
        orm_mode = True

@activity_router.get("/", response_model=List[ActivityResponse])
async def get_activities(
    skip: int = Query(0, description="Skip activities"),
    limit: int = Query(100, description="Limit activities"),
    user: User = Depends(get_current_user),
    activity_dao: ActivityDAO = Depends(ActivityDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get all activities with pagination.
    """
    try:
        # Get workspaces for the user
        workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
        if not workspaces:
            # If user has no workspaces, return empty list
            return []
        
        # Use the first workspace's ID
        workspace_id = workspaces[0].id
        
        return await activity_dao.get_by_workspace(workspace_id, skip, limit)
    except Exception as e:
        # Handle case where activities table might not exist yet
        logger.warning(f"Error getting activities: {e}")
        return []

@activity_router.get("/recent", response_model=List[ActivityResponse])
async def get_recent_activities(
    limit: int = Query(10, description="Limit activities"),
    user: User = Depends(get_current_user),
    activity_dao: ActivityDAO = Depends(ActivityDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get recent activities.
    """
    try:
        # Get workspaces for the user
        workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
        if not workspaces:
            # If user has no workspaces, return empty list
            return []
        
        # Use the first workspace's ID
        workspace_id = workspaces[0].id
        
        return await activity_dao.get_recent_activities(workspace_id, limit)
    except Exception as e:
        # Handle case where activities table might not exist yet
        logger.warning(f"Error getting recent activities: {e}")
        return []

@activity_router.post("/create", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    user: User = Depends(get_current_user),
    activity_dao: ActivityDAO = Depends(ActivityDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Create a new activity.
    """
    try:
        # Get workspaces for the user
        workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
        if not workspaces:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no workspaces"
            )
        
        # Use the first workspace's ID
        workspace_id = workspaces[0].id
        
        # Extract the activity type from the request
        activity_type = activity_data.activity_type
        
        # Handle both formats: activity_type from ActivityCreate or type from direct request
        if not activity_type and hasattr(activity_data, 'type'):
            activity_type = activity_data.type
            
        if not activity_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity type is required"
            )
            
        new_activity = await activity_dao.create_activity(
            user_id=user["user_id"],
            workspace_id=workspace_id,
            activity_type=activity_type,
            entity_id=activity_data.entity_id,
            entity_type=activity_data.entity_type,
            details=activity_data.details
        )
        return new_activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )

@activity_router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
    user: User = Depends(get_current_user),
    activity_dao: ActivityDAO = Depends(ActivityDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get a specific activity by ID.
    """
    try:
        activity = await activity_dao.get_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Get workspaces for the user
        workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
        # Check if the activity belongs to one of the user's workspaces
        if not workspaces or activity.workspace_id not in [ws.id for ws in workspaces]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this activity"
            )
        
        return activity
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Error getting activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or table does not exist"
        )

@activity_router.put("/{activity_id}/update", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
    activity_data: ActivityCreate,
    user: User = Depends(get_current_user),
    activity_dao: ActivityDAO = Depends(ActivityDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Update an existing activity.
    """
    try:
        # Check if the activity exists
        activity = await activity_dao.get_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Get workspaces for the user
        workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
        # Check if the activity belongs to one of the user's workspaces
        if not workspaces or activity.workspace_id not in [ws.id for ws in workspaces]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this activity"
            )
        
        # Extract the activity type from the request
        activity_type = activity_data.activity_type
        
        # Handle both formats: activity_type from ActivityCreate or type from direct request
        if not activity_type and hasattr(activity_data, 'type'):
            activity_type = activity_data.type
            
        if not activity_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Activity type is required"
            )
        
        # Update the activity
        updated_activity = await activity_dao.update_activity(
            activity_id=activity_id,
            activity_type=activity_type,
            entity_id=activity_data.entity_id,
            entity_type=activity_data.entity_type,
            details=activity_data.details
        )
        
        return updated_activity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update activity: {str(e)}"
        )

@activity_router.delete("/{activity_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: str,
    user: User = Depends(get_current_user),
    activity_dao: ActivityDAO = Depends(ActivityDAO),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Delete an activity.
    """
    try:
        activity = await activity_dao.get_by_id(activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found"
            )
        
        # Get workspaces for the user
        workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
        # Check if the activity belongs to one of the user's workspaces
        if not workspaces or activity.workspace_id not in [ws.id for ws in workspaces]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this activity"
            )
        
        await activity_dao.delete_activity(activity)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Error deleting activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found or table does not exist"
        )
    return {"detail": "Activity deleted successfully"}
