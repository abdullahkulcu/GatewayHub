import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def test_create_user_defaults_to_member_and_must_change_password(
    db_session: Session,
) -> None:
    user = User(email="dev@example.com", password_hash="hashed")
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert user.role == UserRole.MEMBER
    assert user.must_change_password is True


def test_role_enum_stores_lowercase_value_in_db(db_session: Session) -> None:
    user = User(email="admin@example.com", password_hash="hashed", role=UserRole.ADMIN)
    db_session.add(user)
    db_session.flush()

    stored_role = db_session.execute(
        text("SELECT role FROM users WHERE id = :id"), {"id": user.id}
    ).scalar_one()

    assert stored_role == "admin"


def test_email_uniqueness_is_enforced(db_session: Session) -> None:
    db_session.add(User(email="dup@example.com", password_hash="a"))
    db_session.flush()
    db_session.add(User(email="dup@example.com", password_hash="b"))

    with pytest.raises(IntegrityError):
        db_session.flush()
