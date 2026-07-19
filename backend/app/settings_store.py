import json
from typing import Any

from sqlalchemy.orm import Session

from app.crypto import decrypt_value, encrypt_value
from app.models.setting import Setting

CLICKUP_TOKEN_KEY = "clickup_api_token"
POLL_INTERVAL_KEY = "poll_interval_seconds"
SYNC_SCOPE_KEY = "sync_scope"

DEFAULT_POLL_INTERVAL_SECONDS = 60


def _get_or_create(db: Session, key: str) -> Setting:
    row = db.get(Setting, key)
    if row is None:
        row = Setting(key=key)
        db.add(row)
    return row


def get_clickup_token(db: Session) -> str | None:
    row = db.get(Setting, CLICKUP_TOKEN_KEY)
    if row is None or row.encrypted_value is None:
        return None
    return decrypt_value(row.encrypted_value)


def set_clickup_token(db: Session, token: str) -> None:
    row = _get_or_create(db, CLICKUP_TOKEN_KEY)
    row.encrypted_value = encrypt_value(token)
    db.commit()


def clear_clickup_token(db: Session) -> None:
    row = db.get(Setting, CLICKUP_TOKEN_KEY)
    if row is not None:
        db.delete(row)
        db.commit()


def get_poll_interval_seconds(db: Session) -> int:
    row = db.get(Setting, POLL_INTERVAL_KEY)
    if row is None or row.value is None:
        return DEFAULT_POLL_INTERVAL_SECONDS
    return int(row.value)


def set_poll_interval_seconds(db: Session, seconds: int) -> None:
    row = _get_or_create(db, POLL_INTERVAL_KEY)
    row.value = str(seconds)
    db.commit()


def get_sync_scope(db: Session) -> dict[str, Any] | None:
    row = db.get(Setting, SYNC_SCOPE_KEY)
    if row is None or row.value is None:
        return None
    scope: dict[str, Any] = json.loads(row.value)
    return scope


def set_sync_scope(db: Session, workspace_id: str, list_ids: list[str]) -> None:
    row = _get_or_create(db, SYNC_SCOPE_KEY)
    row.value = json.dumps({"workspace_id": workspace_id, "list_ids": list_ids})
    db.commit()
