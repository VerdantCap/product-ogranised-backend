import logging
from typing import List, Optional
from fastapi import Depends, HTTPException
from datetime import datetime

from models.task_model import Task
from daos.task_dao import TaskDAO
from schemas import TaskCreate, TaskUpdate

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

    async def create_task(self, task: Task) -> Task:
        """
        Create a new task.

        Returns the created Task object.
        """
        return await self.task_dao.create_task(task)

    async def update_task(self, task_id: str, task_data: TaskUpdate) -> Task:
        """
        Update an existing task.

        Returns the updated Task object.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Update task fields
        for field, value in task_data.dict(exclude_unset=True).items():
            setattr(task, field, value)

        return await self.task_dao.update_task(task)

    async def delete_task(self, task_id: str) -> None:
        """
        Delete a task.
        """
        task = await self.task_dao.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

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
        else:
            task.completed_at = None

        return await self.task_dao.update_task(task)
