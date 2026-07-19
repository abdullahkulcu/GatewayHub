from datetime import UTC, datetime

from providers.base import StatusCategory
from providers.clickup import clickup_task_to_provider_task


def _raw_task(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "abc123",
        "name": "Write the PRD",
        "description": "Some **markdown**.",
        "status": {"status": "in progress", "type": "custom"},
        "parent": None,
        "assignees": [{"id": 1, "email": "dev@example.com"}, {"id": 2}],
        "priority": {"priority": "high", "id": "2"},
        "due_date": "1700000000000",
        "date_updated": "1700000100000",
        "tags": [{"name": "backend"}, {"name": "urgent"}],
    }
    base.update(overrides)
    return base


def test_maps_core_fields() -> None:
    task = clickup_task_to_provider_task(_raw_task())

    assert task.provider_task_id == "abc123"
    assert task.title == "Write the PRD"
    assert task.description == "Some **markdown**."
    assert task.status == "in progress"
    assert task.priority == "high"
    assert task.tags == ["backend", "urgent"]


def test_assignees_without_email_are_skipped() -> None:
    task = clickup_task_to_provider_task(_raw_task())

    assert task.assignee_emails == ["dev@example.com"]


def test_due_date_and_updated_at_parsed_from_epoch_millis() -> None:
    task = clickup_task_to_provider_task(_raw_task())

    assert task.due_date == datetime.fromtimestamp(1700000000, tz=UTC)
    assert task.provider_updated_at == datetime.fromtimestamp(1700000100, tz=UTC)


def test_missing_due_date_is_none() -> None:
    task = clickup_task_to_provider_task(_raw_task(due_date=None))

    assert task.due_date is None


def test_parent_id_passed_through() -> None:
    task = clickup_task_to_provider_task(_raw_task(parent="parent-1"))

    assert task.parent_provider_task_id == "parent-1"


def test_status_type_open_maps_to_todo() -> None:
    task = clickup_task_to_provider_task(
        _raw_task(status={"status": "to do", "type": "open"})
    )

    assert task.status_category == StatusCategory.TODO


def test_status_type_closed_maps_to_done() -> None:
    task = clickup_task_to_provider_task(
        _raw_task(status={"status": "complete", "type": "closed"})
    )

    assert task.status_category == StatusCategory.DONE


def test_unknown_status_type_maps_to_none() -> None:
    task = clickup_task_to_provider_task(
        _raw_task(status={"status": "weird", "type": "something_new"})
    )

    assert task.status_category is None


def test_no_priority_is_none() -> None:
    task = clickup_task_to_provider_task(_raw_task(priority=None))

    assert task.priority is None


def test_raw_payload_is_preserved() -> None:
    raw = _raw_task()

    task = clickup_task_to_provider_task(raw)

    assert task.raw == raw
