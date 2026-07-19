import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.auth import require_active_user
from app.db import get_db
from app.models.user import User, UserRole
from app.security import hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Plain str, not EmailStr — see LoginRequest.email in app/api/auth.py.
    email: str
    role: UserRole
    must_change_password: bool
    created_at: datetime


class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: UserRole = UserRole.MEMBER


class ResetPasswordRequest(BaseModel):
    new_password: str


def require_admin(user: User = Depends(require_active_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db), _admin: User = Depends(require_admin)
) -> list[User]:
    return list(db.query(User).order_by(User.created_at).all())


class UserDirectoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str


@router.get("/directory", response_model=list[UserDirectoryEntry])
def list_user_directory(
    db: Session = Depends(get_db), _user: User = Depends(require_active_user)
) -> list[User]:
    """Minimal id+email lookup for any active user — not admin-gated like
    the rest of this router — so the task list/board views can resolve
    assignee UUIDs to a human-readable email for every team member."""
    return list(db.query(User).order_by(User.email).all())


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    if db.query(User).filter_by(email=payload.email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> None:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.role == UserRole.ADMIN:
        remaining_admins = db.query(User).filter_by(role=UserRole.ADMIN).count()
        if remaining_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete the last remaining admin",
            )
    db.delete(target)
    db.commit()


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: uuid.UUID,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> None:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    target.password_hash = hash_password(payload.new_password)
    target.must_change_password = True
    db.add(target)
    db.commit()
