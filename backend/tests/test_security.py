from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_password_does_not_store_plaintext() -> None:
    hashed = hash_password("s3cret!")

    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("s3cret!")

    assert verify_password("wrong", hashed) is False


def test_access_token_roundtrip() -> None:
    token = create_access_token("user-123")

    assert decode_access_token(token) == "user-123"
