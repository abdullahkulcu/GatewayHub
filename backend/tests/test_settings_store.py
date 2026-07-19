from sqlalchemy.orm import Session

from app import settings_store
from app.models.setting import Setting


def test_clickup_token_roundtrip_is_encrypted_at_rest(db_session: Session) -> None:
    assert settings_store.get_clickup_token(db_session) is None

    settings_store.set_clickup_token(db_session, "pk_secrettoken")

    assert settings_store.get_clickup_token(db_session) == "pk_secrettoken"
    row = db_session.get(Setting, settings_store.CLICKUP_TOKEN_KEY)
    assert row is not None
    assert row.encrypted_value != "pk_secrettoken"


def test_clear_clickup_token_removes_it(db_session: Session) -> None:
    settings_store.set_clickup_token(db_session, "pk_secrettoken")

    settings_store.clear_clickup_token(db_session)

    assert settings_store.get_clickup_token(db_session) is None


def test_poll_interval_defaults_to_sixty_seconds(db_session: Session) -> None:
    assert settings_store.get_poll_interval_seconds(db_session) == 60


def test_poll_interval_roundtrip(db_session: Session) -> None:
    settings_store.set_poll_interval_seconds(db_session, 120)

    assert settings_store.get_poll_interval_seconds(db_session) == 120


def test_sync_scope_defaults_to_none(db_session: Session) -> None:
    assert settings_store.get_sync_scope(db_session) is None


def test_sync_scope_roundtrip(db_session: Session) -> None:
    settings_store.set_sync_scope(db_session, "ws1", ["l1", "l2"])

    scope = settings_store.get_sync_scope(db_session)

    assert scope == {"workspace_id": "ws1", "list_ids": ["l1", "l2"]}
