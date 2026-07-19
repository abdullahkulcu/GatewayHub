import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.user import User
from providers.base import SyncBatch


def _resolve_assignee_ids(db: Session, emails: list[str]) -> list[uuid.UUID]:
    if not emails:
        return []
    rows = db.execute(select(User.id).where(User.email.in_(emails))).scalars().all()
    return list(rows)


def upsert_sync_batch(db: Session, provider: str, batch: SyncBatch) -> None:
    """Idempotently upsert a provider-agnostic SyncBatch into the canonical
    tasks table, keyed on (provider, provider_task_id) (FR-SYNC-1/FR-MODEL-2).

    Parent/child links are resolved in a second pass so task order within
    the batch never matters (a subtask may arrive before its parent).
    """
    now = datetime.now(UTC)

    for provider_task in batch.tasks:
        existing = db.execute(
            select(Task).where(
                Task.provider == provider,
                Task.provider_task_id == provider_task.provider_task_id,
            )
        ).scalar_one_or_none()

        if existing is None:
            existing = Task(provider=provider, provider_task_id=provider_task.provider_task_id)
            db.add(existing)

        existing.title = provider_task.title
        existing.description = provider_task.description
        existing.status = provider_task.status
        existing.status_category = provider_task.status_category
        existing.assignees = _resolve_assignee_ids(db, provider_task.assignee_emails)
        existing.priority = provider_task.priority
        existing.due_date = provider_task.due_date
        existing.tags = provider_task.tags
        existing.provider_raw = provider_task.raw
        existing.provider_updated_at = provider_task.provider_updated_at
        existing.last_synced_at = now
        existing.sync_version = (existing.sync_version or 0) + 1

    db.flush()

    id_by_provider_task_id: dict[str, uuid.UUID] = dict(
        db.execute(
            select(Task.provider_task_id, Task.id).where(Task.provider == provider)
        )
        .tuples()
        .all()
    )
    for provider_task in batch.tasks:
        if provider_task.parent_provider_task_id is None:
            continue
        parent_id = id_by_provider_task_id.get(provider_task.parent_provider_task_id)
        if parent_id is None:
            continue
        db.execute(
            update(Task)
            .where(Task.id == id_by_provider_task_id[provider_task.provider_task_id])
            .values(parent_id=parent_id)
        )

    db.commit()
