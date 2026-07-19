import httpx
import pytest
import respx

from providers.clickup import CLICKUP_API_BASE, ClickUpClient


def test_verify_token_true_on_success() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(return_value=httpx.Response(200, json={"teams": []}))

        with ClickUpClient("pk_valid_token") as client:
            assert client.verify_token() is True


def test_verify_token_false_on_401() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(
            return_value=httpx.Response(401, json={"err": "Invalid token"})
        )

        with ClickUpClient("pk_invalid_token") as client:
            assert client.verify_token() is False


def test_token_sent_without_bearer_prefix() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        route = mock.get("/team").mock(return_value=httpx.Response(200, json={"teams": []}))

        with ClickUpClient("pk_raw_token") as client:
            client.verify_token()

        assert route.calls.last.request.headers["Authorization"] == "pk_raw_token"


def test_list_workspaces_returns_teams() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(
            return_value=httpx.Response(200, json={"teams": [{"id": "1", "name": "Acme"}]})
        )

        with ClickUpClient("pk_token") as client:
            workspaces = client.list_workspaces()

        assert workspaces == [{"id": "1", "name": "Acme"}]


def test_list_spaces_for_workspace() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team/1/space").mock(
            return_value=httpx.Response(200, json={"spaces": [{"id": "s1", "name": "Eng"}]})
        )

        with ClickUpClient("pk_token") as client:
            spaces = client.list_spaces("1")

        assert spaces == [{"id": "s1", "name": "Eng"}]


def test_list_folders_for_space() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/space/s1/folder").mock(
            return_value=httpx.Response(200, json={"folders": [{"id": "f1", "name": "Sprint"}]})
        )

        with ClickUpClient("pk_token") as client:
            folders = client.list_folders("s1")

        assert folders == [{"id": "f1", "name": "Sprint"}]


def test_list_folderless_lists_for_space() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/space/s1/list").mock(
            return_value=httpx.Response(200, json={"lists": [{"id": "l1", "name": "Backlog"}]})
        )

        with ClickUpClient("pk_token") as client:
            lists = client.list_folderless_lists("s1")

        assert lists == [{"id": "l1", "name": "Backlog"}]


def test_list_lists_in_folder() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/folder/f1/list").mock(
            return_value=httpx.Response(200, json={"lists": [{"id": "l2", "name": "Sprint 1"}]})
        )

        with ClickUpClient("pk_token") as client:
            lists = client.list_lists_in_folder("f1")

        assert lists == [{"id": "l2", "name": "Sprint 1"}]


def test_server_error_raises() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/team").mock(return_value=httpx.Response(500, json={"err": "boom"}))

        with ClickUpClient("pk_token") as client, pytest.raises(httpx.HTTPStatusError):
            client.list_workspaces()


def test_list_tasks_stops_on_last_page_flag() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(
                200, json={"tasks": [{"id": "t1"}, {"id": "t2"}], "last_page": True}
            )
        )

        with ClickUpClient("pk_token") as client:
            tasks = client.list_tasks("l1")

        assert [t["id"] for t in tasks] == ["t1", "t2"]


def test_list_tasks_paginates_until_last_page() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(200, json={"tasks": [{"id": "t1"}], "last_page": False})
        )
        mock.get("/list/l1/task", params={"page": "1"}).mock(
            return_value=httpx.Response(200, json={"tasks": [{"id": "t2"}], "last_page": True})
        )

        with ClickUpClient("pk_token") as client:
            tasks = client.list_tasks("l1")

        assert [t["id"] for t in tasks] == ["t1", "t2"]


def test_list_tasks_stops_on_empty_page_even_if_last_page_flag_says_more() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/list/l1/task", params={"page": "0"}).mock(
            return_value=httpx.Response(200, json={"tasks": [{"id": "t1"}], "last_page": False})
        )
        mock.get("/list/l1/task", params={"page": "1"}).mock(
            return_value=httpx.Response(200, json={"tasks": [], "last_page": False})
        )

        with ClickUpClient("pk_token") as client:
            tasks = client.list_tasks("l1")

        assert [t["id"] for t in tasks] == ["t1"]


def test_list_comments_for_task() -> None:
    with respx.mock(base_url=CLICKUP_API_BASE) as mock:
        mock.get("/task/t1/comment").mock(
            return_value=httpx.Response(
                200, json={"comments": [{"id": "c1", "comment_text": "hi"}]}
            )
        )

        with ClickUpClient("pk_token") as client:
            comments = client.list_comments("t1")

        assert comments == [{"id": "c1", "comment_text": "hi"}]
