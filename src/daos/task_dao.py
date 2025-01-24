import logging
from fastapi import Depends
from typing import List
from sqlalchemy import or_
from models.task_model import Task
from db.postgres import AsyncSession, get_postgres_session
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskDAO:
    def __init__(
        self,
        db: AsyncSession = Depends(get_postgres_session),
    ):
        self.db = db

    def create_task(self, task: Task):
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def update_task(self, task: Task):
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task: Task):
        self.db.delete(task)
        self.db.commit()
        return task

    def get_by_id( self, task_id: str) -> Task:
        return self.db.query(Task).filter( Task.id == task_id ).first()

    def get_by_workspace( self, workspace_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.db.query(Task).filter( Task.workspace_id == workspace_id ).offset(skip).limit(limit).all()

    def get_todo( self, workspace_id: str ) -> List[Task]:
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.completed_at.is_(None)
        ).all()

    def get_assigned_to( self, user_id: str, workspace_id: str) -> List[Task]:
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            or_(
                Task.assignee_id == user_id,
                Task.assignee_id.is_(None)
            )
        ).all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.db.query(Task).offset(skip).limit(limit).all()

    def complete_task( self,task: Task ) -> Task:
        task.completed_at = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return task

    def reset_task( self, task: Task) -> Task:
        task.completed_at = None
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_by_completion_status( self, workspace_id: str, completed: bool) -> List[Task]:
        query = self.db.query(Task).filter(Task.workspace_id == workspace_id)
        if completed:
            query = query.filter(Task.completed_at.isnot(None))
        else:
            query = query.filter(Task.completed_at.is_(None))
        return query.all()
    
    def get_by_assignee( self, user_id: str, workspace_id: str) -> List[Task]:
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.assignee_id == user_id
        ).all()
    
    def get_upcoming_tasks( self, workspace_id: str, days: int = 7, limit: int = 10) -> List[Task]:
        future_date = datetime.now() + datetime.timedelta(days=days)
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at <= future_date,
            Task.due_at > datetime.now(),
            Task.completed_at.is_(None)
        ).order_by(Task.due_at).limit(limit).all()
    
    def get_overdue_tasks( self, workspace_id: str, limit: int = 10) -> List[Task]:
        return self.db.query(Task).filter(
            Task.workspace_id == workspace_id,
            Task.due_at.isnot(None),
            Task.due_at < datetime.now(),
            Task.completed_at.is_(None)
        ).order_by(Task.due_at).limit(limit).all()

    def complete_task( self,task: Task ) -> Task:
        task.completed_at = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def uncomplete_task( self,task: Task ) -> Task:
        task.completed_at = None
        self.db.commit()
        self.db.refresh(task)
        return task