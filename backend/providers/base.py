from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ProviderTask:
    """A task as normalized by a provider adapter, not yet a DB row.

    `assignee_emails` is the join key to GatewayHub `users.email` — mapping
    provider identities to GatewayHub accounts by email avoids a separate
    provider-user mapping table for Phase 0.
    """

    provider_task_id: str
    title: str
    status: str
    parent_provider_task_id: str | None = None
    description: str | None = None
    status_category: str | None = None
    assignee_emails: list[str] = field(default_factory=list)
    priority: str | None = None
    due_date: datetime | None = None
    tags: list[str] = field(default_factory=list)
    provider_updated_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderComment:
    provider_task_id: str
    provider_comment_id: str
    author: str
    body: str
    created_at: datetime


@dataclass(frozen=True)
class SyncBatch:
    tasks: list[ProviderTask] = field(default_factory=list)
    comments: list[ProviderComment] = field(default_factory=list)


@dataclass(frozen=True)
class ProviderCapabilities:
    supports_subtask_independent_status: bool = False
    supports_multiple_assignees: bool = False
    max_rate_per_minute: int | None = None


class TaskProvider(ABC):
    """Provider-agnostic adapter interface (FR-PROV-1).

    Concrete adapters (e.g. ClickUp) implement this; core code must never
    branch on which provider is in use — behavioral differences are only
    exposed through `capabilities()` (FR-PROV-2).
    """

    @abstractmethod
    def backfill(self) -> SyncBatch:
        """Full initial sync: every task, subtask, and comment in scope."""

    @abstractmethod
    def fetch_changes(self, since: datetime) -> SyncBatch:
        """Incremental sync: everything changed since `since`."""

    def parse_webhook(self, payload: dict[str, Any]) -> SyncBatch:
        raise NotImplementedError("Webhook support is planned for Phase 2+")

    def push_change(self, change: Any) -> Any:
        raise NotImplementedError("Write-back is planned for Phase 1")

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Declare what this provider supports so core/UI can gate features."""
