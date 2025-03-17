import logging
from fastapi import Depends
from typing import List, Optional
from sqlalchemy import or_, select
from models.task_model import Task
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime

# Set up a logger for the TaskDAO
logger = logging.getLogger(__name__)

class TaskDAO:
    """
    Data Access Object for Task.

    This class provides methods to perform CRUD operations on Task objects in the database.
    """

    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        # Initialize the DAO with a database session
        self.db = db

    async def create_task(self, task: Task):
        """
        Create a new task record in the database.

        Returns the created Task object.
        """
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def update_task(self, task: Task):
        """
        Update an existing task record in the database.

        Returns the updated Task object.
        """
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task: Task):
        """
        Delete a task record from the database.

        Returns the deleted Task object.
        """
        self.db.delete(task)
        await self.db.commit()
        return task

    async def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a task record by its ID.

        Returns the Task object if found, otherwise None.
        """
        query = select(Task).where(Task.id == task_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Retrieve task records by workspace ID with pagination.

        Returns a list of Task objects.
        """
        query = select(Task).where(Task.workspace_id == workspace_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_todo(self, workspace_id: str) -> List[Task]:
        """
        Retrieve tasks that are not completed in a workspace.

        Returns a list of Task objects.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.completed_at.is_(None)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assigned_to(self, user_id: str, workspace_id: str) -> List[Task]:
        """
        Retrieve tasks assigned to a user in a workspace.

        Returns a list of Task objects.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            or_(
                Task.assignee_id == user_id,
                Task.assignee_id.is_(None)
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Retrieve multiple task records with pagination.

        Returns a list of Task objects.
        """
        query = select(Task).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def complete_task(self, task: Task) -> Task:
        """
        Mark a task as completed by setting its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def reset_task(self, task: Task) -> Task:
        """
        Reset a task's completion status by clearing its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = None
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def get_by_completion_status(self, workspace_id: str, completed: bool) -> List[Task]:
        """
        Retrieve tasks by completion status in a workspace.

        Returns a list of Task objects.
        """
        conditions = [Task.workspace_id == workspace_id]
        if completed:
            conditions.append(Task.completed_at.isnot(None))
        else:
            conditions.append(Task.completed_at.is_(None))
            
        query = select(Task).where(*conditions)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_assignee(self, user_id: str, workspace_id: str) -> List[Task]:
        """
        Retrieve tasks assigned to a user in a workspace.

        Returns a list of Task objects.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.assignee_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_upcoming_tasks(self, workspace_id: str, days: int = 7, limit: int = 10) -> List[Task]:
        """
        Retrieve upcoming tasks in a workspace within a specified number of days.

        Returns a list of Task objects ordered by due date.
        """
        from datetime import timedelta
        future_date = datetime.now() + timedelta(days=days)
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at <= future_date,
            Task.due_at > datetime.now(),
            Task.completed_at.is_(None)
        ).order_by(Task.due_at).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_overdue_tasks(self, workspace_id: str, limit: int = 10) -> List[Task]:
        """
        Retrieve overdue tasks in a workspace.

        Returns a list of Task objects ordered by due date.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at < datetime.now(),
            Task.completed_at.is_(None)
        ).order_by(Task.due_at).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def complete_task(self, task: Task) -> Task:
        """
        Mark a task as completed by setting its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def uncomplete_task(self, task: Task) -> Task:
        """
        Unmark a task's completion status by clearing its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = None
        await self.db.commit()
        await self.db.refresh(task)
        return task
