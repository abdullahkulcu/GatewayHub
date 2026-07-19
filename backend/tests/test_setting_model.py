from sqlalchemy.orm import Session

from app.crypto import decrypt_value, encrypt_value
from app.models.setting import Setting


def test_plain_setting_roundtrip(db_session: Session) -> None:
    db_session.add(Setting(key="poll_interval_seconds", value="60"))
    db_session.flush()

    stored = db_session.get(Setting, "poll_interval_seconds")

    assert stored is not None
    assert stored.value == "60"
    assert stored.encrypted_value is None


def test_encrypted_setting_stores_ciphertext_not_plaintext(db_session: Session) -> None:
    token = "pk_supersecrettoken"
    db_session.add(Setting(key="clickup_api_token", encrypted_value=encrypt_value(token)))
    db_session.flush()

    stored = db_session.get(Setting, "clickup_api_token")

    assert stored is not None
    assert stored.encrypted_value is not None
    assert stored.encrypted_value != token
    assert decrypt_value(stored.encrypted_value) == token
