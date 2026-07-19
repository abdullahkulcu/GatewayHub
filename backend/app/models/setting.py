from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Setting(Base):
    """Generic key/value store for runtime configuration (FR-SET-1).

    Sensitive values (provider tokens) go in `encrypted_value` (Fernet
    ciphertext); non-sensitive values (poll interval, sync scope) go in
    the plaintext `value` column. Never both at once.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str | None] = mapped_column(String, nullable=True)
    encrypted_value: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
