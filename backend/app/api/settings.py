from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import settings_store
from app.api.users import require_admin
from app.crypto import mask_secret
from app.db import get_db
from app.models.user import User
from providers.clickup import ClickUpClient

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SyncScope(BaseModel):
    workspace_id: str
    list_ids: list[str]


class SettingsOut(BaseModel):
    clickup_token_configured: bool
    clickup_token_masked: str | None
    poll_interval_seconds: int
    sync_scope: SyncScope | None


class SetClickUpTokenRequest(BaseModel):
    token: str


class SetPollIntervalRequest(BaseModel):
    poll_interval_seconds: int = Field(ge=1)


def _settings_view(db: Session) -> SettingsOut:
    token = settings_store.get_clickup_token(db)
    scope = settings_store.get_sync_scope(db)
    return SettingsOut(
        clickup_token_configured=token is not None,
        clickup_token_masked=mask_secret(token) if token else None,
        poll_interval_seconds=settings_store.get_poll_interval_seconds(db),
        sync_scope=SyncScope(**scope) if scope else None,
    )


def _flatten_lists_for_workspace(
    client: ClickUpClient, workspace_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for space in client.list_spaces(workspace_id):
        space_name = space.get("name")
        for lst in client.list_folderless_lists(space["id"]):
            result.append(
                {
                    "id": lst["id"],
                    "name": lst["name"],
                    "space_name": space_name,
                    "folder_name": None,
                }
            )
        for folder in client.list_folders(space["id"]):
            folder_name = folder.get("name")
            for lst in client.list_lists_in_folder(folder["id"]):
                result.append(
                    {
                        "id": lst["id"],
                        "name": lst["name"],
                        "space_name": space_name,
                        "folder_name": folder_name,
                    }
                )
    return result


def _require_configured_token(db: Session) -> str:
    token = settings_store.get_clickup_token(db)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="ClickUp token not configured"
        )
    return token


@router.get("", response_model=SettingsOut)
def get_settings(
    db: Session = Depends(get_db), _admin: User = Depends(require_admin)
) -> SettingsOut:
    return _settings_view(db)


@router.put("/clickup-token", response_model=SettingsOut)
def set_clickup_token(
    payload: SetClickUpTokenRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SettingsOut:
    with ClickUpClient(payload.token) as client:
        if not client.verify_token():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ClickUp rejected the provided token",
            )
    settings_store.set_clickup_token(db, payload.token)
    return _settings_view(db)


@router.delete("/clickup-token", status_code=status.HTTP_204_NO_CONTENT)
def delete_clickup_token(
    db: Session = Depends(get_db), _admin: User = Depends(require_admin)
) -> None:
    settings_store.clear_clickup_token(db)


@router.put("/poll-interval", response_model=SettingsOut)
def set_poll_interval(
    payload: SetPollIntervalRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SettingsOut:
    settings_store.set_poll_interval_seconds(db, payload.poll_interval_seconds)
    return _settings_view(db)


@router.put("/sync-scope", response_model=SettingsOut)
def set_sync_scope(
    payload: SyncScope, db: Session = Depends(get_db), _admin: User = Depends(require_admin)
) -> SettingsOut:
    settings_store.set_sync_scope(db, payload.workspace_id, payload.list_ids)
    return _settings_view(db)


@router.get("/clickup/workspaces")
def list_clickup_workspaces(
    db: Session = Depends(get_db), _admin: User = Depends(require_admin)
) -> list[dict[str, Any]]:
    token = _require_configured_token(db)
    with ClickUpClient(token) as client:
        return client.list_workspaces()


@router.get("/clickup/workspaces/{workspace_id}/lists")
def list_clickup_lists(
    workspace_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[dict[str, Any]]:
    token = _require_configured_token(db)
    with ClickUpClient(token) as client:
        return _flatten_lists_for_workspace(client, workspace_id)
