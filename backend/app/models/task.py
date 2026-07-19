import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class StatusCategory(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class WriteState(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("provider", "provider_task_id", name="uq_tasks_provider_task_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String)
    provider_task_id: Mapped[str] = mapped_column(String)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String)
    status_category: Mapped[StatusCategory | None] = mapped_column(
        SAEnum(StatusCategory, name="status_category", values_callable=_enum_values),
        nullable=True,
    )

    assignees: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    priority: Mapped[str | None] = mapped_column(String, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    provider_raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    provider_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_version: Mapped[int] = mapped_column(Integer, default=0)

    write_state: Mapped[WriteState] = mapped_column(
        SAEnum(WriteState, name="write_state", values_callable=_enum_values),
        default=WriteState.SYNCED,
    )
