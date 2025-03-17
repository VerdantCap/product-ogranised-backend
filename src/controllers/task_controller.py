from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from daos.workspace_dao import WorkspaceDAO
from daos.task_dao import TaskDAO
from models.task_model import Task
from services.task_service import TaskService
from schemas import TaskCreate, TaskUpdate, TaskResponse
from services.auth_service import get_current_user

# Create a router for task-related endpoints
task_router = APIRouter()

# Dependency to get the TaskService
def get_task_service(task_dao: TaskDAO = Depends(TaskDAO)):
    return TaskService(task_dao=task_dao)

@task_router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    completed: Optional[bool] = None,
    skip: int = 0, 
    limit: int = 100,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get all tasks for a workspace with optional filtering by completion status.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
        
    if not workspaces:
        # If user has no workspaces, return empty list
        return []
    
    # Use the first workspace's ID
    workspace_id = workspaces[0].id
    if completed is not None:
        return await task_service.get_tasks_by_completion_status(workspace_id, completed)
    return await task_service.get_tasks_by_workspace(workspace_id, skip, limit)

@task_router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    user_info: dict = Depends(get_current_user)
):
    """
    Get a specific task by ID.
    """
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task

@task_router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
    user_info: dict = Depends(get_current_user)
):
    """
    Create a new task.
    """
    task = Task(
        id=str(uuid4()),
        workspace_id=task_data.workspace_id,
        title=task_data.title,
        description=task_data.description,
        due_at=task_data.due_at,
        owner_id=task_data.owner_id,
        assignee_id=task_data.assignee_id,
        completed_at=None
    )
    return await task_service.create_task(task)

@task_router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
    user_info: dict = Depends(get_current_user)
):
    """
    Update an existing task.
    """
    return await task_service.update_task(task_id, task_data)

@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    user_info: dict = Depends(get_current_user)
):
    """
    Delete a task.
    """
    await task_service.delete_task(task_id)
    return {"detail": "Task deleted successfully"}

@task_router.patch("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task_completion(
    task_id: str,
    completed: bool,
    task_service: TaskService = Depends(get_task_service),
    user_info: dict = Depends(get_current_user)
):
    """
    Toggle the completion status of a task.
    """
    return await task_service.toggle_task_completion(task_id, completed)
