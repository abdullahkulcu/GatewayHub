from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.security import hash_password


def _create_user(
    db_session: Session,
    email: str,
    password: str = "hunter2",
    role: UserRole = UserRole.MEMBER,
    must_change_password: bool = False,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        must_change_password=must_change_password,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_users(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "admin@example.com", role=UserRole.ADMIN)
    _create_user(db_session, "member@example.com")
    headers = _auth_headers(client, "admin@example.com", "hunter2")

    response = client.get("/api/users", headers=headers)

    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert emails == {"admin@example.com", "member@example.com"}
    assert "password_hash" not in response.json()[0]


def test_member_cannot_list_users(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "member@example.com")
    headers = _auth_headers(client, "member@example.com", "hunter2")

    response = client.get("/api/users", headers=headers)

    assert response.status_code == 403


def test_admin_can_create_user_with_forced_password_change(
    client: TestClient, db_session: Session
) -> None:
    _create_user(db_session, "admin@example.com", role=UserRole.ADMIN)
    headers = _auth_headers(client, "admin@example.com", "hunter2")

    response = client.post(
        "/api/users",
        json={"email": "newbie@example.com", "password": "welcome1"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "member"
    assert body["must_change_password"] is True


def test_create_user_rejects_duplicate_email(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "admin@example.com", role=UserRole.ADMIN)
    _create_user(db_session, "existing@example.com")
    headers = _auth_headers(client, "admin@example.com", "hunter2")

    response = client.post(
        "/api/users",
        json={"email": "existing@example.com", "password": "welcome1"},
        headers=headers,
    )

    assert response.status_code == 409


def test_admin_can_delete_member(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "admin@example.com", role=UserRole.ADMIN)
    member = _create_user(db_session, "member@example.com")
    headers = _auth_headers(client, "admin@example.com", "hunter2")

    response = client.delete(f"/api/users/{member.id}", headers=headers)

    assert response.status_code == 204
    assert db_session.get(User, member.id) is None


def test_cannot_delete_last_remaining_admin(client: TestClient, db_session: Session) -> None:
    admin = _create_user(db_session, "admin@example.com", role=UserRole.ADMIN)
    headers = _auth_headers(client, "admin@example.com", "hunter2")

    response = client.delete(f"/api/users/{admin.id}", headers=headers)

    assert response.status_code == 409


def test_admin_can_reset_member_password(client: TestClient, db_session: Session) -> None:
    _create_user(db_session, "admin@example.com", role=UserRole.ADMIN)
    member = _create_user(db_session, "member@example.com", must_change_password=False)
    headers = _auth_headers(client, "admin@example.com", "hunter2")

    response = client.post(
        f"/api/users/{member.id}/reset-password",
        json={"new_password": "brandnew1"},
        headers=headers,
    )

    assert response.status_code == 204
    db_session.refresh(member)
    assert member.must_change_password is True

    relogin = client.post(
        "/api/auth/login", json={"email": "member@example.com", "password": "brandnew1"}
    )
    assert relogin.status_code == 200
