from sqlalchemy.orm import Session

from app.bootstrap import ensure_bootstrap_admin
from app.models.user import User, UserRole
from app.security import verify_password


def test_creates_admin_when_no_users_exist(db_session: Session) -> None:
    ensure_bootstrap_admin(db_session)

    admin = db_session.query(User).one()
    assert admin.role == UserRole.ADMIN
    assert admin.must_change_password is True
    assert verify_password("changeme", admin.password_hash)


def test_is_a_no_op_when_a_user_already_exists(db_session: Session) -> None:
    db_session.add(User(email="someone@example.com", password_hash="x"))
    db_session.flush()

    ensure_bootstrap_admin(db_session)

    assert db_session.query(User).count() == 1
