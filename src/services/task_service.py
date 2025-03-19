import logging
from typing import List, Optional
from fastapi import Depends, HTTPException
from datetime import datetime, timedelta

from models.task_model import Task, TaskPriority, TaskStatus, TaskType
from daos.task_dao import TaskDAO
from schemas import TaskCreate, TaskUpdate, TaskFilterParams

# Set up a logger for the TaskService
logger = logging.getLogger(__name__)

class TaskService:
    """
    Service class for handling task operations.

    This class provides methods for creating, updating, and retrieving tasks.
    """

    def __init__(self, task_dao: TaskDAO = Depends(TaskDAO)):
        """Initialize the TaskService with a TaskDAO instance."""
        self.task_dao = task_dao

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Returns the Task object if found, otherwise None.
        """
        return await self.task_dao.get_by_id(task_id)

    async def get_tasks_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Get all tasks for a workspace with pagination.

        Returns a list of Task objects.
        """
        return await self.task_dao.get_by_workspace(workspace_id, skip, limit)

    async def get_filtered_tasks(self, filter_params: TaskFilterParams, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Get tasks with advanced filtering.

        Returns a list of Task objects that match the filter criteria.
        """
        # Start with all tasks in the workspace
        tasks = await self.task_dao.get_by_workspace(filter_params.workspace_id, skip, limit)
        
        # Apply filters
        filtered_tasks = tasks
        
        # Filter by completion status
        if filter_params.completed is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if (task.completed_at is not None) == filter_params.completed
            ]
        
        # Filter by priority
        if filter_params.priority is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.priority == filter_params.priority
            ]
        
        # Filter by status
        if filter_params.status is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.status == filter_params.status
            ]
        
        # Filter by type
        if filter_params.type is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.type == filter_params.type
            ]
        
        # Filter by parent_id
        if filter_params.parent_id is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.parent_id == filter_params.parent_id
            ]
        
        # Filter by assignee_id
        if filter_params.assignee_id is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.assignee_id == filter_params.assignee_id
            ]
        
        # Filter by owner_id
        if filter_params.owner_id is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.owner_id == filter_params.owner_id
            ]
        
        # Filter by due date range
        if filter_params.due_before is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.due_at and task.due_at <= filter_params.due_before
            ]
        
        if filter_params.due_after is not None:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.due_at and task.due_at >= filter_params.due_after
            ]
        
        # Filter by tags
        if filter_params.tags:
            filtered_tasks = [
                task for task in filtered_tasks 
                if task.tags and any(tag in task.tags for tag in filter_params.tags)
            ]
        
        return filtered_tasks

    async def get_tasks_by_completion_status(self, workspace_id: str, completed: bool) -> List[Task]:
        """
        Get tasks by completion status in a workspace.

        Returns a list of Task objects.
        """
        return await self.task_dao.get_by_completion_status(workspace_id, completed)

    async def get_tasks_by_assignee(self, user_id: str, workspace_id: str) -> List[Task]:
        """
        Get tasks assigned to a user in a workspace.

        Returns a list of Task objects.
        """
        return await self.task_dao.get_by_assignee(user_id, workspace_id)

    async def get_upcoming_tasks(self, workspace_id: str, days: int = 7, limit: int = 10) -> List[Task]:
        """
        Get upcoming tasks in a workspace within a specified number of days.

        Returns a list of Task objects ordered by due date.
        """
        return await self.task_dao.get_upcoming_tasks(workspace_id, days, limit)

    async def get_overdue_tasks(self, workspace_id: str, limit: int = 10) -> List[Task]:
        """
        Get overdue tasks in a workspace.

        Returns a list of Task objects ordered by due date.
        """
        return await self.task_dao.get_overdue_tasks(workspace_id, limit)

    async def get_subtasks(self, parent_id: str) -> List[Task]:
        """
        Get all subtasks for a specific task.

        Returns a list of Task objects.
        """
        task = await self.task_dao.get_by_id(parent_id)
        if not task:
            raise HTTPException(status_code=404, detail="Parent task not found")
        
        # Use the DAO to get subtasks
        return await self.task_dao.get_subtasks(parent_id)

    async def create_task(self, task: Task) -> Task:
        """
        Create a new task.

        Returns the created Task object.
        """
        # If this is a subtask, verify that the parent task exists
        if task.parent_id:
            parent_task = await self.task_dao.get_by_id(task.parent_id)
            if not parent_task:
                raise HTTPException(status_code=404, detail="Parent task not found")
        
        return await self.task_dao.create_task(task)

    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Task:
        """
        Update an existing task.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # If parent_id is being updated, verify that the parent task exists
        if task_data.parent_id and task_data.parent_id != task.parent_id:
            # Check for circular reference
            if task_data.parent_id == task_id:
                raise HTTPException(status_code=400, detail="A task cannot be its own parent")
            
            parent_task = await self.task_dao.get_by_id(task_data.parent_id)
            if not parent_task:
                raise HTTPException(status_code=404, detail="Parent task not found")

        # Update task fields
        for field, value in task_data.dict(exclude_unset=True).items():
            setattr(task, field, value)

        # If status is being set to completed, update completed_at
        if task_data.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now()
        # If status is being set to something other than completed, clear completed_at
        elif task_data.status is not None and task_data.status != TaskStatus.COMPLETED and task.completed_at:
            task.completed_at = None

        return await self.task_dao.update_task(task)

    async def delete_task(self, task_id: str) -> None:
        """
        Delete a task.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get all subtasks
        subtasks = await self.task_dao.get_subtasks(task_id)
        
        # Delete all subtasks first
        for subtask in subtasks:
            await self.task_dao.delete_task(subtask)
        
        # Then delete the task itself
        await self.task_dao.delete_task(task)

    async def toggle_task_completion(self, task_id: str, completed: bool) -> Task:
        """
        Toggle the completion status of a task.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if completed:
            task.completed_at = datetime.now()
            task.status = TaskStatus.COMPLETED
        else:
            task.completed_at = None
            task.status = TaskStatus.ACTIVE

        return await self.task_dao.update_task(task)

    async def update_task_priority(self, task_id: str, priority: TaskPriority) -> Task:
        """
        Update the priority of a task.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.priority = priority
        return await self.task_dao.update_task(task)

    async def update_task_status(self, task_id: str, status: TaskStatus) -> Task:
        """
        Update the status of a task.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.status = status
        
        # Update completed_at based on status
        if status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now()
        elif status != TaskStatus.COMPLETED and task.completed_at:
            task.completed_at = None

        return await self.task_dao.update_task(task)

    async def assign_task(self, task_id: str, assignee_id: str) -> Task:
        """
        Assign a task to a user.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        task.assignee_id = assignee_id
        return await self.task_dao.update_task(task)

    async def add_tag_to_task(self, task_id: str, tag: str) -> Task:
        """
        Add a tag to a task.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if not task.tags:
            task.tags = []
        
        if tag not in task.tags:
            task.tags.append(tag)
        
        return await self.task_dao.update_task(task)

    async def remove_tag_from_task(self, task_id: str, tag: str) -> Task:
        """
        Remove a tag from a task.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.tags and tag in task.tags:
            task.tags.remove(tag)
        
        return await self.task_dao.update_task(task)
