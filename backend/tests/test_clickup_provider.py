from datetime import UTC, datetime

import httpx
import pytest
import respx

from providers.clickup import CLICKUP_API_BASE, ClickUpClient, ClickUpProvider


def test_backfill_aggregates_tasks_across_lists() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(
                200,
                json={
                    "tasks": [
                        {
                            "id": "t1",
                            "name": "Task 1",
                            "status": {"status": "open", "type": "open"},
                        }
                    ],
                    "last_page": True,
                },
            )
        )
        mock.get("/list/l2/task", params={"page": "0"}).mock(
            return_value=httpx.Response(
                200,
                json={
                    "tasks": [
                        {
                            "id": "t2",
                            "name": "Task 2",
                            "status": {"status": "done", "type": "closed"},
                        }
                    ],
                    "last_page": True,
                },
            )
        )

        with ClickUpClient("pk_token") as client:
            provider = ClickUpProvider(client, ["l1", "l2"])
            batch = provider.backfill()

        assert {t.provider_task_id for t in batch.tasks} == {"t1", "t2"}
        assert batch.comments == []


def test_fetch_changes_not_implemented_yet() -> None:
    with ClickUpClient("pk_token") as client:
        provider = ClickUpProvider(client, [])

        with pytest.raises(NotImplementedError):
            provider.fetch_changes(datetime.now(UTC))


def test_capabilities_declares_independent_subtasks_and_multi_assignee() -> None:
    with ClickUpClient("pk_token") as client:
        provider = ClickUpProvider(client, [])

        caps = provider.capabilities()

        assert caps.supports_subtask_independent_status is True
        assert caps.supports_multiple_assignees is True
