import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.user import User
from app.security import hash_password


def _create_member(
    db_session: Session, email: str = "dev@example.com", must_change_password: bool = False
) -> User:
    user = User(
        email=email,
        password_hash=hash_password("hunter2"),
        must_change_password=must_change_password,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _auth_headers(client: TestClient, email: str = "dev@example.com") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": "hunter2"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _make_task(**overrides: object) -> Task:
    base: dict[str, object] = {
        "provider": "clickup",
        "provider_task_id": str(uuid.uuid4()),
        "title": "Task",
        "status": "open",
    }
    base.update(overrides)
    return Task(**base)


def test_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/tasks")

    assert response.status_code == 401


def test_rejects_user_with_pending_password_change(client: TestClient, db_session: Session) -> None:
    _create_member(db_session, must_change_password=True)
    headers = _auth_headers(client)

    response = client.get("/api/tasks", headers=headers)

    assert response.status_code == 403


def test_lists_all_tasks_sorted_by_title_by_default(
    client: TestClient, db_session: Session
) -> None:
    _create_member(db_session)
    db_session.add(_make_task(title="Zebra"))
    db_session.add(_make_task(title="Apple"))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", headers=headers)

    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert titles == ["Apple", "Zebra"]


def test_filter_by_status(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    db_session.add(_make_task(title="A", status="open"))
    db_session.add(_make_task(title="B", status="closed"))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"status": "closed"}, headers=headers)

    assert [t["title"] for t in response.json()] == ["B"]


def test_filter_by_tag(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    db_session.add(_make_task(title="A", tags=["backend"]))
    db_session.add(_make_task(title="B", tags=["frontend"]))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"tag": "frontend"}, headers=headers)

    assert [t["title"] for t in response.json()] == ["B"]


def test_filter_by_list_id(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    db_session.add(_make_task(title="A", provider_list_id="l1"))
    db_session.add(_make_task(title="B", provider_list_id="l2"))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"list_id": "l2"}, headers=headers)

    assert [t["title"] for t in response.json()] == ["B"]


def test_filter_by_assignee(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    target_user_id = uuid.uuid4()
    db_session.add(_make_task(title="A", assignees=[target_user_id]))
    db_session.add(_make_task(title="B", assignees=[uuid.uuid4()]))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"assignee": str(target_user_id)}, headers=headers)

    assert [t["title"] for t in response.json()] == ["A"]


def test_filter_by_has_parent_true(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    parent = _make_task(title="Parent")
    db_session.add(parent)
    db_session.flush()
    db_session.add(_make_task(title="Child", parent_id=parent.id))
    db_session.add(_make_task(title="Orphan"))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"has_parent": "true"}, headers=headers)

    assert [t["title"] for t in response.json()] == ["Child"]


def test_filter_by_has_parent_false(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    parent = _make_task(title="Parent")
    db_session.add(parent)
    db_session.flush()
    db_session.add(_make_task(title="Child", parent_id=parent.id))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"has_parent": "false"}, headers=headers)

    titles = {t["title"] for t in response.json()}
    assert titles == {"Parent"}


def test_sort_descending(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    db_session.add(_make_task(title="Apple"))
    db_session.add(_make_task(title="Zebra"))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"sort": "-title"}, headers=headers)

    assert [t["title"] for t in response.json()] == ["Zebra", "Apple"]


def test_unknown_sort_key_falls_back_to_default(client: TestClient, db_session: Session) -> None:
    _create_member(db_session)
    db_session.add(_make_task(title="Zebra"))
    db_session.add(_make_task(title="Apple"))
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks", params={"sort": "nonsense"}, headers=headers)

    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["Apple", "Zebra"]


def test_list_options_returns_distinct_synced_lists(
    client: TestClient, db_session: Session
) -> None:
    _create_member(db_session)
    db_session.add(_make_task(provider_list_id="l1", provider_list_name="Backlog"))
    db_session.add(_make_task(provider_list_id="l1", provider_list_name="Backlog"))
    db_session.add(_make_task(provider_list_id="l2", provider_list_name="Sprint 1"))
    db_session.add(_make_task())  # no list at all — must not appear
    db_session.flush()
    headers = _auth_headers(client)

    response = client.get("/api/tasks/list-options", headers=headers)

    assert response.status_code == 200
    options = {(o["id"], o["name"]) for o in response.json()}
    assert options == {("l1", "Backlog"), ("l2", "Sprint 1")}


def test_list_options_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/tasks/list-options")

    assert response.status_code == 401
