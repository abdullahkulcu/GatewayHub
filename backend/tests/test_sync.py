from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User
from app.sync import upsert_sync_batch
from providers.base import ProviderComment, ProviderTask, StatusCategory, SyncBatch


def test_inserts_new_task(db_session: Session) -> None:
    batch = SyncBatch(
        tasks=[
            ProviderTask(
                provider_task_id="t1",
                title="Write PRD",
                status="open",
                status_category=StatusCategory.TODO,
                list_id="list-1",
            )
        ]
    )

    upsert_sync_batch(db_session, "clickup", batch)

    task = db_session.query(Task).filter_by(provider_task_id="t1").one()
    assert task.title == "Write PRD"
    assert task.status_category == StatusCategory.TODO
    assert task.provider_list_id == "list-1"
    assert task.sync_version == 1


def test_upsert_is_idempotent_and_updates_existing_row(db_session: Session) -> None:
    batch_v1 = SyncBatch(
        tasks=[ProviderTask(provider_task_id="t1", title="Draft", status="open")]
    )
    upsert_sync_batch(db_session, "clickup", batch_v1)

    batch_v2 = SyncBatch(
        tasks=[ProviderTask(provider_task_id="t1", title="Final", status="closed")]
    )
    upsert_sync_batch(db_session, "clickup", batch_v2)

    tasks = db_session.query(Task).filter_by(provider_task_id="t1").all()
    assert len(tasks) == 1
    assert tasks[0].title == "Final"
    assert tasks[0].sync_version == 2


def test_resolves_known_assignee_email_and_skips_unknown(db_session: Session) -> None:
    user = User(email="dev@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()

    batch = SyncBatch(
        tasks=[
            ProviderTask(
                provider_task_id="t1",
                title="Task",
                status="open",
                assignee_emails=["dev@example.com", "ghost@example.com"],
            )
        ]
    )

    upsert_sync_batch(db_session, "clickup", batch)

    task = db_session.query(Task).filter_by(provider_task_id="t1").one()
    assert task.assignees == [user.id]


def test_resolves_parent_id_when_parent_appears_after_child_in_batch(
    db_session: Session,
) -> None:
    batch = SyncBatch(
        tasks=[
            ProviderTask(
                provider_task_id="child-1",
                parent_provider_task_id="parent-1",
                title="Child",
                status="open",
            ),
            ProviderTask(provider_task_id="parent-1", title="Parent", status="open"),
        ]
    )

    upsert_sync_batch(db_session, "clickup", batch)

    parent = db_session.query(Task).filter_by(provider_task_id="parent-1").one()
    child = db_session.query(Task).filter_by(provider_task_id="child-1").one()
    assert child.parent_id == parent.id


def test_parent_outside_batch_scope_leaves_parent_id_null(db_session: Session) -> None:
    batch = SyncBatch(
        tasks=[
            ProviderTask(
                provider_task_id="child-1",
                parent_provider_task_id="not-in-this-list",
                title="Child",
                status="open",
            )
        ]
    )

    upsert_sync_batch(db_session, "clickup", batch)

    child = db_session.query(Task).filter_by(provider_task_id="child-1").one()
    assert child.parent_id is None


def test_upserts_comments_for_their_task(db_session: Session) -> None:
    batch = SyncBatch(
        tasks=[ProviderTask(provider_task_id="t1", title="Task", status="open")],
        comments=[
            ProviderComment(
                provider_task_id="t1",
                provider_comment_id="c1",
                author="jane",
                body="LGTM",
                created_at=datetime.now(UTC),
            )
        ],
    )

    upsert_sync_batch(db_session, "clickup", batch)

    task = db_session.query(Task).filter_by(provider_task_id="t1").one()
    comment = db_session.query(Comment).filter_by(provider_comment_id="c1").one()
    assert comment.task_id == task.id
    assert comment.author == "jane"
    assert comment.body == "LGTM"


def test_comment_upsert_is_idempotent(db_session: Session) -> None:
    batch = SyncBatch(
        tasks=[ProviderTask(provider_task_id="t1", title="Task", status="open")],
        comments=[
            ProviderComment(
                provider_task_id="t1",
                provider_comment_id="c1",
                author="jane",
                body="First edit",
                created_at=datetime.now(UTC),
            )
        ],
    )
    upsert_sync_batch(db_session, "clickup", batch)

    batch_v2 = SyncBatch(
        tasks=[ProviderTask(provider_task_id="t1", title="Task", status="open")],
        comments=[
            ProviderComment(
                provider_task_id="t1",
                provider_comment_id="c1",
                author="jane",
                body="Edited",
                created_at=datetime.now(UTC),
            )
        ],
    )
    upsert_sync_batch(db_session, "clickup", batch_v2)

    comments = db_session.query(Comment).filter_by(provider_comment_id="c1").all()
    assert len(comments) == 1
    assert comments[0].body == "Edited"


def test_comment_for_task_outside_batch_scope_is_skipped(db_session: Session) -> None:
    batch = SyncBatch(
        comments=[
            ProviderComment(
                provider_task_id="not-in-batch",
                provider_comment_id="c1",
                author="jane",
                body="orphaned",
                created_at=datetime.now(UTC),
            )
        ]
    )

    upsert_sync_batch(db_session, "clickup", batch)

    assert db_session.query(Comment).count() == 0
