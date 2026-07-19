from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.task import Task


def _make_task(db_session: Session, provider_task_id: str = "task-1") -> Task:
    task = Task(provider="clickup", provider_task_id=provider_task_id, title="T", status="open")
    db_session.add(task)
    db_session.flush()
    return task


def test_comment_belongs_to_task(db_session: Session) -> None:
    task = _make_task(db_session)
    comment = Comment(
        task_id=task.id,
        provider_comment_id="c-1",
        author="jane@example.com",
        body="Looks good to me.",
        created_at=datetime.now(UTC),
    )
    db_session.add(comment)
    db_session.flush()

    assert comment.id is not None
    assert comment.task_id == task.id


def test_comment_provider_id_unique_per_task(db_session: Session) -> None:
    task = _make_task(db_session)
    db_session.add(
        Comment(
            task_id=task.id,
            provider_comment_id="dup",
            author="a",
            body="one",
            created_at=datetime.now(UTC),
        )
    )
    db_session.flush()
    db_session.add(
        Comment(
            task_id=task.id,
            provider_comment_id="dup",
            author="b",
            body="two",
            created_at=datetime.now(UTC),
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_deleting_task_cascades_to_comments(db_session: Session) -> None:
    task = _make_task(db_session, provider_task_id="task-cascade")
    db_session.add(
        Comment(
            task_id=task.id,
            provider_comment_id="c-1",
            author="a",
            body="bye",
            created_at=datetime.now(UTC),
        )
    )
    db_session.flush()

    db_session.delete(task)
    db_session.flush()

    remaining = db_session.query(Comment).filter_by(task_id=task.id).count()
    assert remaining == 0
