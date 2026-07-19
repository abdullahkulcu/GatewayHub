import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.task import StatusCategory, Task, WriteState


def test_create_task_with_defaults(db_session: Session) -> None:
    task = Task(
        provider="clickup",
        provider_task_id="abc123",
        title="Write PRD",
        status="open",
    )
    db_session.add(task)
    db_session.flush()

    assert task.id is not None
    assert task.parent_id is None
    assert task.sync_version == 0
    assert task.write_state == WriteState.SYNCED


def test_subtask_references_parent_via_parent_id(db_session: Session) -> None:
    parent = Task(provider="clickup", provider_task_id="parent-1", title="Parent", status="open")
    db_session.add(parent)
    db_session.flush()

    subtask = Task(
        provider="clickup",
        provider_task_id="child-1",
        parent_id=parent.id,
        title="Subtask",
        status="open",
        status_category=StatusCategory.TODO,
    )
    db_session.add(subtask)
    db_session.flush()

    assert subtask.parent_id == parent.id


def test_provider_and_provider_task_id_are_unique_together(db_session: Session) -> None:
    db_session.add(Task(provider="clickup", provider_task_id="dup", title="A", status="open"))
    db_session.flush()
    db_session.add(Task(provider="clickup", provider_task_id="dup", title="B", status="open"))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_provider_raw_stores_arbitrary_json(db_session: Session) -> None:
    raw = {"custom_field": {"nested": [1, 2, 3]}}
    task = Task(
        provider="clickup",
        provider_task_id="raw-1",
        title="Has raw",
        status="open",
        provider_raw=raw,
        assignees=[uuid.uuid4()],
        tags=["backend", "urgent"],
    )
    db_session.add(task)
    db_session.flush()
    db_session.refresh(task)

    assert task.provider_raw == raw
    assert task.tags == ["backend", "urgent"]
