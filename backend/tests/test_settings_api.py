import httpx
import respx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.security import hash_password
from providers.clickup import CLICKUP_API_BASE


def _create_admin(db_session: Session) -> User:
    user = User(
        email="admin@example.com",
        password_hash=hash_password("hunter2"),
        role=UserRole.ADMIN,
        must_change_password=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "hunter2"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_settings_defaults(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)

    response = client.get("/api/settings", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "clickup_token_configured": False,
        "clickup_token_masked": None,
        "poll_interval_seconds": 60,
        "sync_scope": None,
    }


def test_settings_require_admin(client: TestClient, db_session: Session) -> None:
    member = User(
        email="member@example.com",
        password_hash=hash_password("hunter2"),
        must_change_password=False,
    )
    db_session.add(member)
    db_session.flush()
    login = client.post(
        "/api/auth/login", json={"email": "member@example.com", "password": "hunter2"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get("/api/settings", headers=headers)

    assert response.status_code == 403


def test_set_clickup_token_validates_and_masks(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)

    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(return_value=httpx.Response(200, json={"teams": []}))

        response = client.put(
            "/api/settings/clickup-token", json={"token": "pk_abc123456"}, headers=headers
        )

    assert response.status_code == 200
    body = response.json()
    assert body["clickup_token_configured"] is True
    assert body["clickup_token_masked"] == "pk_****"


def test_set_clickup_token_rejects_invalid_token(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)

    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(return_value=httpx.Response(401, json={"err": "bad"}))

        response = client.put(
            "/api/settings/clickup-token", json={"token": "pk_invalid"}, headers=headers
        )

    assert response.status_code == 422


def test_delete_clickup_token(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(return_value=httpx.Response(200, json={"teams": []}))
        client.put("/api/settings/clickup-token", json={"token": "pk_abc"}, headers=headers)

    response = client.delete("/api/settings/clickup-token", headers=headers)

    assert response.status_code == 204
    assert client.get("/api/settings", headers=headers).json()["clickup_token_configured"] is False


def test_set_poll_interval(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)

    response = client.put(
        "/api/settings/poll-interval", json={"poll_interval_seconds": 300}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["poll_interval_seconds"] == 300


def test_set_poll_interval_rejects_non_positive(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)

    response = client.put(
        "/api/settings/poll-interval", json={"poll_interval_seconds": 0}, headers=headers
    )

    assert response.status_code == 422


def test_set_sync_scope(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)

    response = client.put(
        "/api/settings/sync-scope",
        json={"workspace_id": "ws1", "list_ids": ["l1", "l2"]},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["sync_scope"] == {"workspace_id": "ws1", "list_ids": ["l1", "l2"]}


def test_list_clickup_workspaces_requires_configured_token(
    client: TestClient, db_session: Session
) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)

    response = client.get("/api/settings/clickup/workspaces", headers=headers)

    assert response.status_code == 400


def test_list_clickup_workspaces(client: TestClient, db_session: Session) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(
            return_value=httpx.Response(200, json={"teams": [{"id": "ws1", "name": "Acme"}]})
        )
        client.put("/api/settings/clickup-token", json={"token": "pk_abc"}, headers=headers)

        response = client.get("/api/settings/clickup/workspaces", headers=headers)

    assert response.status_code == 200
    assert response.json() == [{"id": "ws1", "name": "Acme"}]


def test_list_clickup_lists_flattens_folders_and_folderless(
    client: TestClient, db_session: Session
) -> None:
    _create_admin(db_session)
    headers = _auth_headers(client)
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(return_value=httpx.Response(200, json={"teams": []}))
        client.put("/api/settings/clickup-token", json={"token": "pk_abc"}, headers=headers)

        mock.get("/team/ws1/space", params={"archived": "false"}).mock(
            return_value=httpx.Response(200, json={"spaces": [{"id": "s1", "name": "Eng"}]})
        )
        mock.get("/space/s1/list", params={"archived": "false"}).mock(
            return_value=httpx.Response(200, json={"lists": [{"id": "l1", "name": "Backlog"}]})
        )
        mock.get("/space/s1/folder", params={"archived": "false"}).mock(
            return_value=httpx.Response(200, json={"folders": [{"id": "f1", "name": "Sprint"}]})
        )
        mock.get("/folder/f1/list", params={"archived": "false"}).mock(
            return_value=httpx.Response(200, json={"lists": [{"id": "l2", "name": "Sprint 1"}]})
        )

        response = client.get("/api/settings/clickup/workspaces/ws1/lists", headers=headers)

    assert response.status_code == 200
    assert response.json() == [
        {"id": "l1", "name": "Backlog", "space_name": "Eng", "folder_name": None},
        {"id": "l2", "name": "Sprint 1", "space_name": "Eng", "folder_name": "Sprint"},
    ]
