from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User, UserRole
from app.security import hash_password


def ensure_bootstrap_admin(db: Session) -> None:
    """Create the first admin user from ADMIN_EMAIL/ADMIN_PASSWORD (FR-SET-0).

    Only runs when no user exists yet; afterwards users are managed
    exclusively through the panel (FR-SET-3).
    """
    if db.query(User).first() is not None:
        return

    settings = get_settings()
    admin = User(
        email=settings.admin_email,
        password_hash=hash_password(settings.admin_password),
        role=UserRole.ADMIN,
        must_change_password=True,
    )
    db.add(admin)
    db.commit()
