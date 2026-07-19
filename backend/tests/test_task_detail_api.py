import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User
from app.security import hash_password


def _create_member(db_session: Session) -> User:
    user = User(
        email="dev@example.com", password_hash=hash_password("hunter2"), must_change_password=False
    )
    db_session.add(user)
    db_session.flush()
    return user


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": "hunter2"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _make_task(**overrides: object) -> Task:
    base: dict[str, object] = {
        "provider": "clickup",
        "provider_task_id": str(uuid.uuid4()),
        "title": "Task",
        "status": "open",
        "description": "Some **markdown**.",
    }
    base.update(overrides)
    return Task(**base)


def test_requires_authentication(client: TestClient, db_session: Session) -> None:
    task = _make_task()
    db_session.add(task)
    db_session.flush()

    response = client.get(f"/api/tasks/{task.id}")

    assert response.status_code == 401


def test_returns_404_for_unknown_task(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    headers = _auth_headers(client)

    response = client.get(f"/api/tasks/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


def test_returns_description_comments_and_subtasks(
    client: TestClient, db_session: Session
) -> None:
    _create_member(db_session)
    headers = _auth_headers(client)

    parent = _make_task(title="Parent task")
    db_session.add(parent)
    db_session.flush()

    child = _make_task(title="Subtask", parent_id=parent.id)
    db_session.add(child)
    db_session.add(
        Comment(
            task_id=parent.id,
            provider_comment_id="c1",
            author="jane",
            body="LGTM",
            created_at=datetime.now(UTC),
        )
    )
    db_session.flush()

    response = client.get(f"/api/tasks/{parent.id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Some **markdown**."
    assert [c["body"] for c in body["comments"]] == ["LGTM"]
    assert [s["title"] for s in body["subtasks"]] == ["Subtask"]


def test_task_without_comments_or_subtasks_returns_empty_lists(
    client: TestClient, db_session: Session
) -> None:
    _create_member(db_session)
    headers = _auth_headers(client)
    task = _make_task()
    db_session.add(task)
    db_session.flush()

    response = client.get(f"/api/tasks/{task.id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["comments"] == []
    assert body["subtasks"] == []


def test_activity_metadata_reflects_sync_state(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    headers = _auth_headers(client)
    task = _make_task(sync_version=3)
    db_session.add(task)
    db_session.flush()

    response = client.get(f"/api/tasks/{task.id}", headers=headers)

    body = response.json()
    assert body["write_state"] == "synced"
    assert body["last_synced_at"] is None
    assert body["sync_version"] == 3
