import httpx
import respx
from sqlalchemy.orm import Session

from app import settings_store
from app.models.task import Task
from app.poller import run_forever, run_poll_once
from providers.clickup import CLICKUP_API_BASE


def test_noop_without_configured_token_or_scope(db_session: Session) -> None:
    run_poll_once(db_session)

    assert settings_store.get_last_synced_at(db_session) is None
    assert db_session.query(Task).count() == 0


def _configure(db_session: Session) -> None:
    settings_store.set_clickup_token(db_session, "pk_token")
    settings_store.set_sync_scope(db_session, "ws1", ["l1"])


def test_first_run_backfills_and_records_success(db_session: Session) -> None:
    _configure(db_session)

    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        route = mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(
                200,
                json={
                    "tasks": [{"id": "t1", "name": "Task", "status": {"status": "open"}}],
                    "last_page": True,
                },
            )
        )
        mock.get("/task/t1/comment").mock(
            return_value=httpx.Response(200, json={"comments": []})
        )

        run_poll_once(db_session)

    assert "date_updated_gt" not in route.calls.last.request.url.params
    assert db_session.query(Task).filter_by(provider_task_id="t1").count() == 1
    assert settings_store.get_last_synced_at(db_session) is not None
    assert settings_store.get_last_sync_error(db_session) is None


def test_second_run_uses_incremental_fetch_changes(db_session: Session) -> None:
    _configure(db_session)

    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(200, json={"tasks": [], "last_page": True})
        )
        run_poll_once(db_session)

    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        route = mock.get("/list/l1/task").mock(
            return_value=httpx.Response(200, json={"tasks": [], "last_page": True})
        )

        run_poll_once(db_session)

    assert "date_updated_gt" in route.calls.last.request.url.params


def test_sync_failure_is_recorded_and_never_raises(db_session: Session) -> None:
    _configure(db_session)

    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(500, json={"err": "boom"})
        )

        run_poll_once(db_session)  # must not raise

    assert settings_store.get_last_sync_error(db_session) is not None
    assert settings_store.get_last_synced_at(db_session) is None


def test_error_is_cleared_after_a_subsequent_success(db_session: Session) -> None:
    _configure(db_session)
    settings_store.set_last_sync_error(db_session, "previous failure")

    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(200, json={"tasks": [], "last_page": True})
        )

        run_poll_once(db_session)

    assert settings_store.get_last_sync_error(db_session) is None


def test_run_forever_rereads_poll_interval_every_iteration(db_session: Session) -> None:
    settings_store.set_poll_interval_seconds(db_session, 5)
    intervals: list[float] = []

    def fake_sleep(seconds: float) -> None:
        intervals.append(seconds)
        if len(intervals) == 1:
            settings_store.set_poll_interval_seconds(db_session, 30)

    run_forever(db_session, sleep=fake_sleep, max_iterations=2)

    assert intervals == [5, 30]
