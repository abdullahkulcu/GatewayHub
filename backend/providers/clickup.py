from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType
from typing import Any

import httpx

from providers.base import (
    ProviderCapabilities,
    ProviderComment,
    ProviderTask,
    StatusCategory,
    SyncBatch,
    TaskProvider,
)

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"

# ClickUp status "type" values map onto our fixed status vocabulary
# (FR-MODEL-4). ClickUp has no distinct native type for "cancelled" — a
# cancelled workflow is just a custom status of type "closed" — so that
# category is never inferred automatically here.
_STATUS_TYPE_TO_CATEGORY = {
    "open": StatusCategory.TODO,
    "custom": StatusCategory.IN_PROGRESS,
    "closed": StatusCategory.DONE,
    "done": StatusCategory.DONE,
}


def _map_status_category(status_type: str | None) -> StatusCategory | None:
    if status_type is None:
        return None
    return _STATUS_TYPE_TO_CATEGORY.get(status_type)


def _parse_epoch_millis(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=UTC)


def clickup_task_to_provider_task(raw: dict[str, Any]) -> ProviderTask:
    status = raw.get("status") or {}
    priority = raw.get("priority") or None
    return ProviderTask(
        provider_task_id=raw["id"],
        title=raw["name"],
        status=status.get("status", "unknown"),
        parent_provider_task_id=raw.get("parent"),
        description=raw.get("description") or None,
        status_category=_map_status_category(status.get("type")),
        assignee_emails=[a["email"] for a in raw.get("assignees", []) if a.get("email")],
        priority=priority.get("priority") if priority else None,
        due_date=_parse_epoch_millis(raw.get("due_date")),
        tags=[t["name"] for t in raw.get("tags", []) if t.get("name")],
        provider_updated_at=_parse_epoch_millis(raw.get("date_updated")),
        raw=raw,
    )


def clickup_comment_to_provider_comment(
    provider_task_id: str, raw: dict[str, Any]
) -> ProviderComment:
    user = raw.get("user") or {}
    author = user.get("username") or user.get("email") or "unknown"
    body = raw.get("comment_text") or "".join(
        part.get("text", "") for part in raw.get("comment", [])
    )
    created_at = _parse_epoch_millis(raw.get("date")) or datetime.now(UTC)
    return ProviderComment(
        provider_task_id=provider_task_id,
        provider_comment_id=raw["id"],
        author=author,
        body=body,
        created_at=created_at,
    )


class ClickUpAuthError(Exception):
    """Raised when the ClickUp API rejects the configured token."""


class ClickUpClient:
    """Thin wrapper around the ClickUp REST API (auth + workspace discovery).

    ClickUp expects the raw personal API token in the `Authorization` header
    with no `Bearer` prefix.
    """

    def __init__(
        self, api_token: str, base_url: str = CLICKUP_API_BASE, timeout: float = 10.0
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url, headers={"Authorization": api_token}, timeout=timeout
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ClickUpClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self._client.get(path, params=params)
        if response.status_code == 401:
            raise ClickUpAuthError("ClickUp rejected the configured API token")
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def verify_token(self) -> bool:
        try:
            self._get("/team")
        except ClickUpAuthError:
            return False
        return True

    def list_workspaces(self) -> list[dict[str, Any]]:
        data = self._get("/team")
        teams: list[dict[str, Any]] = data.get("teams", [])
        return teams

    def list_spaces(self, workspace_id: str) -> list[dict[str, Any]]:
        data = self._get(f"/team/{workspace_id}/space", params={"archived": "false"})
        spaces: list[dict[str, Any]] = data.get("spaces", [])
        return spaces

    def list_folders(self, space_id: str) -> list[dict[str, Any]]:
        data = self._get(f"/space/{space_id}/folder", params={"archived": "false"})
        folders: list[dict[str, Any]] = data.get("folders", [])
        return folders

    def list_folderless_lists(self, space_id: str) -> list[dict[str, Any]]:
        data = self._get(f"/space/{space_id}/list", params={"archived": "false"})
        lists: list[dict[str, Any]] = data.get("lists", [])
        return lists

    def list_lists_in_folder(self, folder_id: str) -> list[dict[str, Any]]:
        data = self._get(f"/folder/{folder_id}/list", params={"archived": "false"})
        lists: list[dict[str, Any]] = data.get("lists", [])
        return lists

    def list_tasks(self, list_id: str) -> list[dict[str, Any]]:
        """All tasks in a list, including subtasks and closed tasks, across pages."""
        tasks: list[dict[str, Any]] = []
        page = 0
        while True:
            data = self._get(
                f"/list/{list_id}/task",
                params={"subtasks": "true", "include_closed": "true", "page": page},
            )
            page_tasks: list[dict[str, Any]] = data.get("tasks", [])
            if not page_tasks:
                break
            tasks.extend(page_tasks)
            if data.get("last_page", True):
                break
            page += 1
        return tasks

    def list_comments(self, task_id: str) -> list[dict[str, Any]]:
        data = self._get(f"/task/{task_id}/comment")
        comments: list[dict[str, Any]] = data.get("comments", [])
        return comments


class ClickUpProvider(TaskProvider):
    def __init__(self, client: ClickUpClient, list_ids: Sequence[str]) -> None:
        self._client = client
        self._list_ids = list(list_ids)

    def backfill(self) -> SyncBatch:
        raw_tasks = [
            raw_task
            for list_id in self._list_ids
            for raw_task in self._client.list_tasks(list_id)
        ]
        tasks = [clickup_task_to_provider_task(raw_task) for raw_task in raw_tasks]
        comments = [
            clickup_comment_to_provider_comment(raw_task["id"], raw_comment)
            for raw_task in raw_tasks
            for raw_comment in self._client.list_comments(raw_task["id"])
        ]
        return SyncBatch(tasks=tasks, comments=comments)

    def fetch_changes(self, since: datetime) -> SyncBatch:
        raise NotImplementedError("Incremental ClickUp sync lands in T13")

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_subtask_independent_status=True,
            supports_multiple_assignees=True,
            max_rate_per_minute=100,
        )
