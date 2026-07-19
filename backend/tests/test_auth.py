from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.security import hash_password


def _create_user(
    db_session: Session, email: str = "dev@example.com", password: str = "hunter2"
) -> User:
    user = User(email=email, password_hash=hash_password(password), must_change_password=True)
    db_session.add(user)
    db_session.flush()
    return user


def test_login_success_returns_token_and_must_change_password_flag(
    client: TestClient, db_session: Session
) -> None:
    _create_user(db_session)

    response = client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": "hunter2"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["must_change_password"] is True


def test_login_wrong_password_returns_401(client: TestClient, db_session: Session) -> None:
    _create_user(db_session)

    response = client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": "wrong"}
    )

    assert response.status_code == 401


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "x"}
    )

    assert response.status_code == 401


def test_change_password_updates_hash_and_clears_flag(
    client: TestClient, db_session: Session
) -> None:
    user = _create_user(db_session)
    login = client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": "hunter2"}
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "hunter2", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    db_session.refresh(user)
    assert user.must_change_password is False

    relogin = client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": "newpass123"}
    )
    assert relogin.status_code == 200
    assert relogin.json()["must_change_password"] is False


def test_change_password_rejects_wrong_current_password(
    client: TestClient, db_session: Session
) -> None:
    _create_user(db_session)
    login = client.post(
        "/api/auth/login", json={"email": "dev@example.com", "password": "hunter2"}
    )
    token = login.json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "wrong", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_change_password_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "a", "new_password": "b"},
    )

    assert response.status_code == 401
