import logging
from fastapi import Depends
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, select, and_, func
from models.task_model import Task, TaskPriority, TaskStatus, TaskType
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime, timedelta

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
            Task.completed_at.is_(None),
            Task.status != TaskStatus.COMPLETED
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
        future_date = datetime.now() + timedelta(days=days)
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at <= future_date,
            Task.due_at > datetime.now(),
            Task.completed_at.is_(None),
            Task.status != TaskStatus.COMPLETED
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
            Task.completed_at.is_(None),
            Task.status != TaskStatus.COMPLETED
        ).order_by(Task.due_at).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_priority(self, workspace_id: str, priority: TaskPriority) -> List[Task]:
        """
        Retrieve tasks by priority in a workspace.

        Returns a list of Task objects.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.priority == priority
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_status(self, workspace_id: str, status: TaskStatus) -> List[Task]:
        """
        Retrieve tasks by status in a workspace.

        Returns a list of Task objects.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.status == status
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_type(self, workspace_id: str, task_type: TaskType) -> List[Task]:
        """
        Retrieve tasks by type in a workspace.

        Returns a list of Task objects.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.type == task_type
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_subtasks(self, parent_id: str) -> List[Task]:
        """
        Retrieve subtasks for a given parent task.

        Returns a list of Task objects.
        """
        query = select(Task).where(Task.parent_id == parent_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_tags(self, workspace_id: str, tags: List[str]) -> List[Task]:
        """
        Retrieve tasks that have any of the specified tags.

        Returns a list of Task objects.
        """
        # This is a simplified implementation since JSONB array operations are complex in SQLAlchemy
        # For a production system, you might want to use a raw SQL query with JSONB operators
        tasks = await self.get_by_workspace(workspace_id)
        return [task for task in tasks if task.tags and any(tag in task.tags for tag in tags)]
    
    async def get_by_date_range(self, workspace_id: str, start_date: datetime, end_date: datetime) -> List[Task]:
        """
        Retrieve tasks with due dates within a specified range.

        Returns a list of Task objects.
        """
        query = select(Task).where(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at >= start_date,
            Task.due_at <= end_date
        ).order_by(Task.due_at)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_task_counts_by_status(self, workspace_id: str) -> Dict[str, int]:
        """
        Get counts of tasks grouped by status.

        Returns a dictionary with status as key and count as value.
        """
        # This would be more efficient with a direct SQL query using GROUP BY
        tasks = await self.get_by_workspace(workspace_id)
        counts = {}
        for status in TaskStatus:
            counts[status.value] = len([t for t in tasks if t.status == status])
        return counts
    
    async def get_task_counts_by_priority(self, workspace_id: str) -> Dict[str, int]:
        """
        Get counts of tasks grouped by priority.

        Returns a dictionary with priority as key and count as value.
        """
        # This would be more efficient with a direct SQL query using GROUP BY
        tasks = await self.get_by_workspace(workspace_id)
        counts = {}
        for priority in TaskPriority:
            counts[priority.value] = len([t for t in tasks if t.priority == priority])
        return counts
