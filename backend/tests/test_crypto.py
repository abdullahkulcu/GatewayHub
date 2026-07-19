from app.crypto import decrypt_value, encrypt_value, mask_secret


def test_encrypt_decrypt_roundtrip() -> None:
    token = "pk_1234567890ABCDEF"

    ciphertext = encrypt_value(token)

    assert ciphertext != token
    assert decrypt_value(ciphertext) == token


def test_mask_secret_keeps_prefix_before_underscore() -> None:
    assert mask_secret("pk_1234567890ABCDEF") == "pk_****"


def test_mask_secret_without_underscore_keeps_first_three_chars() -> None:
    assert mask_secret("abcdefgh") == "abc****"


def test_mask_secret_empty_string_is_unchanged() -> None:
    assert mask_secret("") == ""
