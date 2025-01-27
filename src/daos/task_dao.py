import logging
from fastapi import Depends
from typing import List
from sqlalchemy import or_
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

    def create_task(self, task: Task):
        """
        Create a new task record in the database.

        Returns the created Task object.
        """
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def update_task(self, task: Task):
        """
        Update an existing task record in the database.

        Returns the updated Task object.
        """
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task: Task):
        """
        Delete a task record from the database.

        Returns the deleted Task object.
        """
        self.db.delete(task)
        self.db.commit()
        return task

    def get_by_id(self, task_id: str) -> Task:
        """
        Retrieve a task record by its ID.

        Returns the Task object if found, otherwise None.
        """
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_by_workspace(self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Retrieve task records by workspace ID with pagination.

        Returns a list of Task objects.
        """
        return self.db.query(Task).filter(Task.workspace_id == workspace_id).offset(skip).limit(limit).all()

    def get_todo(self, workspace_id: str) -> List[Task]:
        """
        Retrieve tasks that are not completed in a workspace.

        Returns a list of Task objects.
        """
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.completed_at.is_(None)
        ).all()

    def get_assigned_to(self, user_id: str, workspace_id: str) -> List[Task]:
        """
        Retrieve tasks assigned to a user in a workspace.

        Returns a list of Task objects.
        """
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            or_(
                Task.assignee_id == user_id,
                Task.assignee_id.is_(None)
            )
        ).all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """
        Retrieve multiple task records with pagination.

        Returns a list of Task objects.
        """
        return self.db.query(Task).offset(skip).limit(limit).all()

    def complete_task(self, task: Task) -> Task:
        """
        Mark a task as completed by setting its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return task

    def reset_task(self, task: Task) -> Task:
        """
        Reset a task's completion status by clearing its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = None
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_by_completion_status(self, workspace_id: str, completed: bool) -> List[Task]:
        """
        Retrieve tasks by completion status in a workspace.

        Returns a list of Task objects.
        """
        query = self.db.query(Task).filter(Task.workspace_id == workspace_id)
        if completed:
            query = query.filter(Task.completed_at.isnot(None))
        else:
            query = query.filter(Task.completed_at.is_(None))
        return query.all()
    
    def get_by_assignee(self, user_id: str, workspace_id: str) -> List[Task]:
        """
        Retrieve tasks assigned to a user in a workspace.

        Returns a list of Task objects.
        """
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.assignee_id == user_id
        ).all()
    
    def get_upcoming_tasks(self, workspace_id: str, days: int = 7, limit: int = 10) -> List[Task]:
        """
        Retrieve upcoming tasks in a workspace within a specified number of days.

        Returns a list of Task objects ordered by due date.
        """
        future_date = datetime.now() + datetime.timedelta(days=days)
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at <= future_date,
            Task.due_at > datetime.now(),
            Task.completed_at.is_(None)
        ).order_by(Task.due_at).limit(limit).all()
    
    def get_overdue_tasks(self, workspace_id: str, limit: int = 10) -> List[Task]:
        """
        Retrieve overdue tasks in a workspace.

        Returns a list of Task objects ordered by due date.
        """
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at < datetime.now(),
            Task.completed_at.is_(None)
        ).order_by(Task.due_at).limit(limit).all()

    def complete_task(self, task: Task) -> Task:
        """
        Mark a task as completed by setting its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def uncomplete_task(self, task: Task) -> Task:
        """
        Unmark a task's completion status by clearing its completed_at timestamp.

        Returns the updated Task object.
        """
        task.completed_at = None
        self.db.commit()
        self.db.refresh(task)
        return task
