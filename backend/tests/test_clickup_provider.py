from datetime import UTC, datetime

import httpx
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
        mock.get("/task/t1/comment").mock(
            return_value=httpx.Response(200, json={"comments": []})
        )
        mock.get("/task/t2/comment").mock(
            return_value=httpx.Response(200, json={"comments": []})
        )

        with ClickUpClient("pk_token") as client:
            provider = ClickUpProvider(client, ["l1", "l2"])
            batch = provider.backfill()

        assert {t.provider_task_id for t in batch.tasks} == {"t1", "t2"}
        assert batch.comments == []


def test_backfill_includes_comments_per_task() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(
                200,
                json={
                    "tasks": [
                        {"id": "t1", "name": "Task 1", "status": {"status": "open"}}
                    ],
                    "last_page": True,
                },
            )
        )
        mock.get("/task/t1/comment").mock(
            return_value=httpx.Response(
                200,
                json={
                    "comments": [
                        {
                            "id": "c1",
                            "comment_text": "LGTM",
                            "user": {"username": "jane"},
                            "date": "1700000000000",
                        }
                    ]
                },
            )
        )

        with ClickUpClient("pk_token") as client:
            provider = ClickUpProvider(client, ["l1"])
            batch = provider.backfill()

        assert len(batch.comments) == 1
        comment = batch.comments[0]
        assert comment.provider_task_id == "t1"
        assert comment.provider_comment_id == "c1"
        assert comment.author == "jane"
        assert comment.body == "LGTM"


def test_fetch_changes_only_returns_tasks_updated_since() -> None:
    since = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        route = mock.get(
            "/list/l1/task", params={"page": "0", "date_updated_gt": "1705320000000"}
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "tasks": [
                        {"id": "t1", "name": "Changed", "status": {"status": "open"}}
                    ],
                    "last_page": True,
                },
            )
        )
        mock.get("/task/t1/comment").mock(
            return_value=httpx.Response(200, json={"comments": []})
        )

        with ClickUpClient("pk_token") as client:
            provider = ClickUpProvider(client, ["l1"])
            batch = provider.fetch_changes(since)

        assert route.called
        assert [t.provider_task_id for t in batch.tasks] == ["t1"]


def test_capabilities_declares_independent_subtasks_and_multi_assignee() -> None:
    with ClickUpClient("pk_token") as client:
        provider = ClickUpProvider(client, [])

        caps = provider.capabilities()

        assert caps.supports_subtask_independent_status is True
        assert caps.supports_multiple_assignees is True
