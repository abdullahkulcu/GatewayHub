from types import TracebackType
from typing import Any

import httpx

CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


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
