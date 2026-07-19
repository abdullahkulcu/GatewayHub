import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import require_active_user
from app.db import get_db
from app.models.comment import Comment
from app.models.task import StatusCategory, Task, WriteState
from app.models.user import User

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_SORTABLE_COLUMNS = {
    "title": Task.title,
    "due_date": Task.due_date,
    "priority": Task.priority,
    "status": Task.status,
    "provider_updated_at": Task.provider_updated_at,
}
_DEFAULT_SORT = "title"


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    provider_task_id: str
    provider_list_id: str | None
    provider_list_name: str | None
    parent_id: uuid.UUID | None
    title: str
    description: str | None
    status: str
    status_category: StatusCategory | None
    assignees: list[uuid.UUID] | None
    priority: str | None
    due_date: datetime | None
    tags: list[str] | None
    write_state: WriteState
    provider_updated_at: datetime | None
    last_synced_at: datetime | None
    sync_version: int


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author: str
    body: str
    created_at: datetime


class TaskDetailOut(TaskOut):
    comments: list[CommentOut]
    subtasks: list[TaskOut]


@router.get("", response_model=list[TaskOut])
def list_tasks(
    assignee: uuid.UUID | None = None,
    status: str | None = None,
    tag: str | None = None,
    list_id: str | None = None,
    has_parent: bool | None = None,
    sort: str = _DEFAULT_SORT,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
) -> list[Task]:
    query = select(Task)

    if assignee is not None:
        query = query.where(Task.assignees.contains([assignee]))
    if status is not None:
        query = query.where(Task.status == status)
    if tag is not None:
        query = query.where(Task.tags.contains([tag]))
    if list_id is not None:
        query = query.where(Task.provider_list_id == list_id)
    if has_parent is not None:
        parent_filter = Task.parent_id.is_not(None) if has_parent else Task.parent_id.is_(None)
        query = query.where(parent_filter)

    descending = sort.startswith("-")
    column = _SORTABLE_COLUMNS.get(sort.removeprefix("-"), _SORTABLE_COLUMNS[_DEFAULT_SORT])
    query = query.order_by(column.desc() if descending else column.asc())

    return list(db.execute(query).scalars().all())


class ListOptionOut(BaseModel):
    id: str
    name: str | None


@router.get("/list-options", response_model=list[ListOptionOut])
def list_list_options(
    db: Session = Depends(get_db), _user: User = Depends(require_active_user)
) -> list[ListOptionOut]:
    """Distinct provider lists actually present in synced tasks, for the
    list view's "liste" filter. Purely a local DB query — never calls the
    provider live (Principle 4: the UI never waits on the source system)."""
    rows = db.execute(
        select(Task.provider_list_id, Task.provider_list_name)
        .where(Task.provider_list_id.is_not(None))
        .distinct()
    ).all()
    return [ListOptionOut(id=row.provider_list_id, name=row.provider_list_name) for row in rows]


@router.get("/{task_id}", response_model=TaskDetailOut)
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_active_user),
) -> TaskDetailOut:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    comments = db.execute(
        select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
    ).scalars().all()
    subtasks = db.execute(
        select(Task).where(Task.parent_id == task_id).order_by(Task.title)
    ).scalars().all()

    base = TaskOut.model_validate(task)
    return TaskDetailOut(
        **base.model_dump(),
        comments=[CommentOut.model_validate(c) for c in comments],
        subtasks=[TaskOut.model_validate(s) for s in subtasks],
    )
