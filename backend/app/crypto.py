import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import get_settings


def _derive_fernet_key(secret_key: str) -> bytes:
    digest = hashlib.sha256(secret_key.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    return Fernet(_derive_fernet_key(get_settings().secret_key))


def encrypt_value(plaintext: str) -> str:
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(token: str) -> str:
    return get_fernet().decrypt(token.encode()).decode()


def mask_secret(value: str) -> str:
    """Mask a secret for API responses, e.g. 'pk_abc123' -> 'pk_****'."""
    if not value:
        return value
    prefix = value.split("_", 1)[0] + "_" if "_" in value else value[:3]
    return f"{prefix}****"
