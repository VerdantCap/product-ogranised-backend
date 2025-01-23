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