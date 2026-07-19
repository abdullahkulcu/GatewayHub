import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import settings_store
from app.sync import upsert_sync_batch
from providers.clickup import ClickUpClient, ClickUpProvider
from providers.rate_limit import TokenBucket

logger = logging.getLogger(__name__)

CLICKUP_RATE_PER_MINUTE = 100


def run_poll_once(db: Session) -> None:
    """One sync iteration: reads settings fresh from the DB every time
    (FR-SET-2 hot reload), then backfills (first run) or incrementally
    syncs (fetch_changes) ClickUp, recording sync status either way
    (FR-SYNC-5). A sync failure is recorded, never raised — the next poll
    just tries again (FR-SYNC-4/NFR-2).
    """
    token = settings_store.get_clickup_token(db)
    scope = settings_store.get_sync_scope(db)
    if token is None or scope is None:
        return

    try:
        rate_limiter = TokenBucket(rate_per_minute=CLICKUP_RATE_PER_MINUTE)
        with ClickUpClient(token, rate_limiter=rate_limiter) as client:
            provider = ClickUpProvider(client, scope["list_ids"])
            since = settings_store.get_last_synced_at(db)
            batch = provider.backfill() if since is None else provider.fetch_changes(since)
            upsert_sync_batch(db, "clickup", batch)
        settings_store.set_last_synced_at(db, datetime.now(UTC))
        settings_store.set_last_sync_error(db, None)
    except Exception as exc:
        logger.exception("ClickUp sync failed")
        settings_store.set_last_sync_error(db, str(exc))


def run_forever(
    db: Session,
    *,
    sleep: Callable[[float], None] = time.sleep,
    max_iterations: int | None = None,
) -> None:
    """The poll scheduler loop. `max_iterations` is for tests; production
    callers leave it unset to run forever."""
    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        run_poll_once(db)
        interval = settings_store.get_poll_interval_seconds(db)
        sleep(interval)
        iterations += 1
