from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.security import hash_password


def _create_member(db_session: Session, email: str) -> User:
    user = User(email=email, password_hash=hash_password("hunter2"), must_change_password=False)
    db_session.add(user)
    db_session.flush()
    return user


def _auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": "hunter2"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_any_active_member_can_read_the_directory(client: TestClient, db_session: Session) -> None:
    _create_member(db_session, "a@example.com")
    _create_member(db_session, "b@example.com")
    headers = _auth_headers(client, "a@example.com")

    response = client.get("/api/users/directory", headers=headers)

    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert emails == {"a@example.com", "b@example.com"}


def test_directory_entries_have_no_sensitive_fields(
    client: TestClient, db_session: Session
) -> None:
    _create_member(db_session, "a@example.com")
    headers = _auth_headers(client, "a@example.com")

    response = client.get("/api/users/directory", headers=headers)

    entry = response.json()[0]
    assert set(entry.keys()) == {"id", "email"}
