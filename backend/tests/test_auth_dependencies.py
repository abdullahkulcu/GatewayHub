import pytest
from fastapi import HTTPException

from app.api.auth import require_active_user
from app.models.user import User


def test_require_active_user_rejects_pending_password_change() -> None:
    user = User(email="a@example.com", password_hash="x", must_change_password=True)

    with pytest.raises(HTTPException) as exc_info:
        require_active_user(user)

    assert exc_info.value.status_code == 403


def test_require_active_user_passes_through_when_password_changed() -> None:
    user = User(email="a@example.com", password_hash="x", must_change_password=False)

    assert require_active_user(user) is user
