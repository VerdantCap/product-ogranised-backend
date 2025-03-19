from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timedelta
from daos.workspace_dao import WorkspaceDAO
from daos.task_dao import TaskDAO
from models.task_model import Task, TaskPriority, TaskStatus, TaskType
from services.task_service import TaskService
from schemas import TaskCreate, TaskUpdate, TaskResponse, TaskFilterParams
from services.auth_service import get_current_user

# Create a router for task-related endpoints
task_router = APIRouter()

# Dependency to get the TaskService
def get_task_service(task_dao: TaskDAO = Depends(TaskDAO)):
    return TaskService(task_dao=task_dao)

@task_router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    completed: Optional[bool] = None,
    priority: Optional[TaskPriority] = None,
    status: Optional[TaskStatus] = None,
    type: Optional[TaskType] = None,
    parent_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
    tags: Optional[List[str]] = Query(None),
    skip: int = 0, 
    limit: int = 100,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get tasks with advanced filtering options.
    """
    # If workspace_id is not provided, use the first workspace of the user
    
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        # If user has no workspaces, return empty list
        return []
    workspace_id = workspaces[0].id
    
    # Create filter parameters
    filter_params = TaskFilterParams(
        workspace_id=workspace_id,
        completed=completed,
        priority=priority,
        status=status,
        type=type,
        parent_id=parent_id,
        assignee_id=assignee_id,
        owner_id=owner_id,
        due_before=due_before,
        due_after=due_after,
        tags=tags
    )
    
    return await task_service.get_filtered_tasks(filter_params, skip, limit)

@task_router.get("/upcoming", response_model=List[TaskResponse])
async def get_upcoming_tasks(
    days: int = 7,
    limit: int = 10,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get upcoming tasks due within the specified number of days.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        return []
    
    workspace_id = workspaces[0].id
    return await task_service.get_upcoming_tasks(workspace_id, days, limit)

@task_router.get("/overdue", response_model=List[TaskResponse])
async def get_overdue_tasks(
    limit: int = 10,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Get overdue tasks.
    """
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        return []
    
    workspace_id = workspaces[0].id
    return await task_service.get_overdue_tasks(workspace_id, limit)

@task_router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
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

@task_router.get("/{task_id}/subtasks", response_model=List[TaskResponse])
async def get_subtasks(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Get all subtasks for a specific task.
    """
    return await task_service.get_subtasks(task_id)

@task_router.post("/create", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user),
    workspace_dao: WorkspaceDAO = Depends(WorkspaceDAO),
):
    """
    Create a new task.
    """
    # If owner_id is not provided, use the current user's ID
    if not task_data.owner_id:
        task_data.owner_id = user["user_id"]
    
    # If assignee_id is not provided, use the current user's ID
    if not task_data.assignee_id:
        task_data.assignee_id = user["user_id"]
    
    workspaces = await workspace_dao.get_workspaces_by_user_id(user["user_id"])
    if not workspaces:
        # If user has no workspaces, return empty list
        return []
    workspace_id = workspaces[0].id
    # Create task instance
    task = Task(
        id=str(uuid4()),
        workspace_id=workspace_id,
        title=task_data.title,
        description=task_data.description,
        due_at=task_data.due_at,
        owner_id=task_data.owner_id,
        assignee_id=task_data.assignee_id,
        completed_at=None,
        priority=task_data.priority,
        status=task_data.status,
        type=task_data.type,
        parent_id=task_data.parent_id,
        position=task_data.position,
        tags=task_data.tags,
        notifications=task_data.notifications,
        is_recurring=task_data.is_recurring,
        recurrence_pattern=task_data.recurrence_pattern
    )
    
    return await task_service.create_task(task)

@task_router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Update an existing task.
    """
    # Get the task to verify ownership
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Only allow the owner or assignee to update the task
    if task.owner_id != user["user_id"] and task.assignee_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task"
        )
    
    return await task_service.update_task(task_id, task_data)

@task_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Delete a task.
    """
    # Get the task to verify ownership
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Only allow the owner to delete the task
    if task.owner_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this task"
        )
    
    await task_service.delete_task(task_id)
    return {"detail": "Task deleted successfully"}

@task_router.patch("/{task_id}/toggle", response_model=TaskResponse)
async def toggle_task_completion(
    task_id: str,
    completed: bool,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Toggle the completion status of a task.
    """
    # Get the task to verify permissions
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Allow both owner and assignee to toggle completion
    if task.owner_id != user["user_id"] and task.assignee_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task"
        )
    
    return await task_service.toggle_task_completion(task_id, completed)

@task_router.patch("/{task_id}/priority", response_model=TaskResponse)
async def update_task_priority(
    task_id: str,
    priority: TaskPriority,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Update the priority of a task.
    """
    # Get the task to verify permissions
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Allow both owner and assignee to update priority
    if task.owner_id != user["user_id"] and task.assignee_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task"
        )
    
    return await task_service.update_task_priority(task_id, priority)

@task_router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status: TaskStatus,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Update the status of a task.
    """
    # Get the task to verify permissions
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Allow both owner and assignee to update status
    if task.owner_id != user["user_id"] and task.assignee_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task"
        )
    
    return await task_service.update_task_status(task_id, status)

@task_router.patch("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    assignee_id: str,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Assign a task to a user.
    """
    # Get the task to verify ownership
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Only allow the owner to assign the task
    if task.owner_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to assign this task"
        )
    
    return await task_service.assign_task(task_id, assignee_id)

@task_router.post("/{task_id}/tags", response_model=TaskResponse)
async def add_tag_to_task(
    task_id: str,
    tag: str,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Add a tag to a task.
    """
    # Get the task to verify permissions
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Allow both owner and assignee to add tags
    if task.owner_id != user["user_id"] and task.assignee_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task"
        )
    
    return await task_service.add_tag_to_task(task_id, tag)

@task_router.delete("/{task_id}/tags/{tag}", response_model=TaskResponse)
async def remove_tag_from_task(
    task_id: str,
    tag: str,
    task_service: TaskService = Depends(get_task_service),
    user: dict = Depends(get_current_user)
):
    """
    Remove a tag from a task.
    """
    # Get the task to verify permissions
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Allow both owner and assignee to remove tags
    if task.owner_id != user["user_id"] and task.assignee_id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task"
        )
    
    return await task_service.remove_tag_from_task(task_id, tag)
