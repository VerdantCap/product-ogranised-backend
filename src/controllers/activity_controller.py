import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from models.user_model import User
from services.auth_service import get_current_user
from utils.route import APIRouter

# Create a router for activity-related endpoints
activity_router = APIRouter()

# Set up a logger for the activity controller
logger = logging.getLogger(__name__)

# Mock data for activities (since there's no activity model or DAO yet)
ACTIVITIES = [
    {
        "id": "1",
        "user_id": "user_1",
        "workspace_id": "workspace_1",
        "type": "item_created",
        "entity_id": "item_1",
        "entity_type": "item",
        "details": {"title": "Car Insurance", "type": "car-insurance"},
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "2",
        "user_id": "user_1",
        "workspace_id": "workspace_1",
        "type": "task_completed",
        "entity_id": "task_1",
        "entity_type": "task",
        "details": {"title": "Renew passport"},
        "created_at": datetime.now().isoformat()
    }
]

@activity_router.get("/")
async def get_activities(
    skip: int = Query(0, description="Skip activities"),
    limit: int = Query(100, description="Limit activities"),
    user: User = Depends(get_current_user),
):
    """
    Get all activities with pagination.
    """
    # In a real implementation, this would query the database
    # For now, return mock data
    return ACTIVITIES[skip:skip+limit]

@activity_router.get("/recent")
async def get_recent_activities(
    limit: int = Query(10, description="Limit activities"),
    user: User = Depends(get_current_user),
):
    """
    Get recent activities.
    """
    # In a real implementation, this would query the database and sort by created_at
    # For now, return mock data
    return ACTIVITIES[:limit]

@activity_router.post("/")
async def create_activity(
    activity_type: str,
    entity_id: str,
    entity_type: str,
    details: dict = {},
    user: User = Depends(get_current_user),
):
    """
    Create a new activity.
    """
    # In a real implementation, this would create a new activity in the database
    # For now, just return a mock response
    new_activity = {
        "id": str(uuid4()),
        "user_id": user.id,
        "workspace_id": user.active_workspace_id,
        "type": activity_type,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "details": details,
        "created_at": datetime.now().isoformat()
    }
    
    # In a real implementation, we would add this to the database
    # For now, just return it
    return new_activity

@activity_router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    user: User = Depends(get_current_user),
):
    """
    Delete an activity.
    """
    # In a real implementation, this would delete the activity from the database
    # For now, just return a success message
    return {"detail": "Activity deleted successfully"}
