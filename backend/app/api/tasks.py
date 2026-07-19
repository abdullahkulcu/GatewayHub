import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import require_active_user
from app.db import get_db
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
    last_synced_at: datetime | None


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
