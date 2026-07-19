from datetime import UTC, datetime

from providers.base import StatusCategory
from providers.clickup import clickup_comment_to_provider_comment, clickup_task_to_provider_task


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
    task = clickup_task_to_provider_task(_raw_task(), "l1")

    assert task.provider_task_id == "abc123"
    assert task.title == "Write the PRD"
    assert task.description == "Some **markdown**."
    assert task.status == "in progress"
    assert task.priority == "high"
    assert task.tags == ["backend", "urgent"]


def test_assignees_without_email_are_skipped() -> None:
    task = clickup_task_to_provider_task(_raw_task(), "l1")

    assert task.assignee_emails == ["dev@example.com"]


def test_due_date_and_updated_at_parsed_from_epoch_millis() -> None:
    task = clickup_task_to_provider_task(_raw_task(), "l1")

    assert task.due_date == datetime.fromtimestamp(1700000000, tz=UTC)
    assert task.provider_updated_at == datetime.fromtimestamp(1700000100, tz=UTC)


def test_missing_due_date_is_none() -> None:
    task = clickup_task_to_provider_task(_raw_task(due_date=None), "l1")

    assert task.due_date is None


def test_list_id_is_the_list_the_task_was_fetched_from() -> None:
    task = clickup_task_to_provider_task(_raw_task(), "list-42")

    assert task.list_id == "list-42"


def test_parent_id_passed_through() -> None:
    task = clickup_task_to_provider_task(_raw_task(parent="parent-1"), "l1")

    assert task.parent_provider_task_id == "parent-1"


def test_status_type_open_maps_to_todo() -> None:
    task = clickup_task_to_provider_task(
        _raw_task(status={"status": "to do", "type": "open"}), "l1"
    )

    assert task.status_category == StatusCategory.TODO


def test_status_type_closed_maps_to_done() -> None:
    task = clickup_task_to_provider_task(
        _raw_task(status={"status": "complete", "type": "closed"}), "l1"
    )

    assert task.status_category == StatusCategory.DONE


def test_unknown_status_type_maps_to_none() -> None:
    task = clickup_task_to_provider_task(
        _raw_task(status={"status": "weird", "type": "something_new"}), "l1"
    )

    assert task.status_category is None


def test_no_priority_is_none() -> None:
    task = clickup_task_to_provider_task(_raw_task(priority=None), "l1")

    assert task.priority is None


def test_raw_payload_is_preserved() -> None:
    raw = _raw_task()

    task = clickup_task_to_provider_task(raw, "l1")

    assert task.raw == raw


def test_comment_maps_username_and_comment_text() -> None:
    comment = clickup_comment_to_provider_comment(
        "t1",
        {
            "id": "c1",
            "comment_text": "Looks good",
            "user": {"username": "jane", "email": "jane@example.com"},
            "date": "1700000000000",
        },
    )

    assert comment.provider_task_id == "t1"
    assert comment.provider_comment_id == "c1"
    assert comment.author == "jane"
    assert comment.body == "Looks good"
    assert comment.created_at == datetime.fromtimestamp(1700000000, tz=UTC)


def test_comment_falls_back_to_email_when_no_username() -> None:
    comment = clickup_comment_to_provider_comment(
        "t1", {"id": "c1", "comment_text": "hi", "user": {"email": "jane@example.com"}}
    )

    assert comment.author == "jane@example.com"


def test_comment_falls_back_to_unknown_author_when_no_user() -> None:
    comment = clickup_comment_to_provider_comment("t1", {"id": "c1", "comment_text": "hi"})

    assert comment.author == "unknown"


def test_comment_body_falls_back_to_comment_parts_when_no_comment_text() -> None:
    comment = clickup_comment_to_provider_comment(
        "t1", {"id": "c1", "comment": [{"text": "Hello "}, {"text": "world"}]}
    )

    assert comment.body == "Hello world"
