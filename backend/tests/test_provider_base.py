from datetime import UTC, datetime

import pytest

from providers.base import ProviderCapabilities, SyncBatch, TaskProvider


class _FakeProvider(TaskProvider):
    def backfill(self) -> SyncBatch:
        return SyncBatch()

    def fetch_changes(self, since: datetime) -> SyncBatch:
        return SyncBatch()

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(supports_multiple_assignees=True)


def test_task_provider_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        TaskProvider()  # type: ignore[abstract]


def test_concrete_provider_reports_capabilities() -> None:
    provider = _FakeProvider()

    caps = provider.capabilities()

    assert caps.supports_multiple_assignees is True
    assert caps.supports_subtask_independent_status is False


def test_parse_webhook_not_implemented_in_phase_0() -> None:
    provider = _FakeProvider()

    with pytest.raises(NotImplementedError):
        provider.parse_webhook({})


def test_push_change_not_implemented_in_phase_0() -> None:
    provider = _FakeProvider()

    with pytest.raises(NotImplementedError):
        provider.push_change(None)


def test_backfill_returns_sync_batch() -> None:
    provider = _FakeProvider()

    result = provider.backfill()

    assert result.tasks == []
    assert result.comments == []


def test_fetch_changes_returns_sync_batch() -> None:
    provider = _FakeProvider()

    result = provider.fetch_changes(datetime.now(UTC))

    assert isinstance(result, SyncBatch)
