"""Hacker News as a research source, against recorded Algolia responses
(``tests/fixtures/hackernews``): what a search and a thread become, and a
watch run end to end through the research service. No network."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.hackernews import client
from app.services.hackernews.schemas import HNQuery
from app.services.hackernews.sources import from_hit, from_tree, plain
from app.services.research.models import ResearchItem
from app.services.research.service import ResearchService

FIXTURES = Path(__file__).parents[1] / "fixtures" / "hackernews"

# A watch is saved, refreshed and read back: the same reads repeat across
# the steps by construction.
pytestmark = pytest.mark.queryspy(allow_n_plus_one=True)


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text())


class Algolia:
    """Algolia, answering from the fixtures and recording what was asked."""

    def __init__(self) -> None:
        self.asked: list[httpx.Request] = []

    def transport(self) -> httpx.MockTransport:
        def answer(request: httpx.Request) -> httpx.Response:
            self.asked.append(request)
            if request.url.path.startswith("/api/v1/items/"):
                return httpx.Response(200, json=_fixture("thread.json"))
            name = (
                "search_comments.json"
                if request.url.params.get("tags") == "comment"
                else "search_stories.json"
            )
            return httpx.Response(200, json=_fixture(name))

        return httpx.MockTransport(answer)


@pytest.fixture
def algolia(monkeypatch: pytest.MonkeyPatch) -> Algolia:
    fake = Algolia()
    monkeypatch.setattr(client, "_transport", fake.transport())
    return fake


def test_a_story_hit_keeps_its_numbers() -> None:
    hit = _fixture("search_stories.json")["hits"][0]

    item = from_hit(hit)

    assert item.kind == "story" and item.external_id == hit["objectID"]
    assert item.score == hit["points"] and item.comment_count == hit["num_comments"]
    assert item.title == hit["title"] and item.url == hit["url"]
    assert "show_hn" in item.data["tags"]
    assert item.published_at is not None and item.published_at.tzinfo is None


def test_a_comment_hit_names_the_story_it_is_under() -> None:
    hit = _fixture("search_comments.json")["hits"][0]

    item = from_hit(hit)

    assert item.kind == "comment"
    assert item.root_external_id == str(hit["story_id"])
    assert item.parent_external_id == str(hit["parent_id"])
    assert item.data["story_title"] == hit["story_title"]


def test_hacker_news_html_is_stored_as_plain_text() -> None:
    assert plain("I&#x27;m in.<p>Second <i>part</i>") == "I'm in.\n\nSecond part"
    assert plain(None) is None


def test_a_thread_comes_back_top_first_with_its_replies_counted() -> None:
    tree = _fixture("thread.json")

    items = list(from_tree(tree))

    assert items[0].external_id == str(tree["id"]) and items[0].kind == "story"
    assert items[0].comment_count == len(items) - 1
    assert all(i.root_external_id == str(tree["id"]) for i in items)
    replies = {i.external_id: i for i in items[1:]}
    for child in tree["children"]:
        assert replies[str(child["id"])].parent_external_id == str(tree["id"])


async def test_a_query_becomes_algolias(algolia: Algolia) -> None:
    from datetime import date

    await client.search(
        HNQuery(
            q="fastapi",
            tags="show_hn",
            min_points=50,
            since=date(2026, 1, 1),
            sort="newest",
            limit=10,
        )
    )

    (request,) = algolia.asked
    assert request.url.path == "/api/v1/search_by_date"
    assert request.url.params["query"] == "fastapi"
    assert request.url.params["tags"] == "show_hn"
    assert request.url.params["hitsPerPage"] == "10"
    assert "points>=50" in request.url.params["numericFilters"]
    assert "created_at_i>=1767225600" in request.url.params["numericFilters"]


async def test_a_watch_runs_through_the_research_service(
    async_db_session: AsyncSession, algolia: Algolia
) -> None:
    svc = ResearchService(async_db_session, owner_user_id=None)
    watch = await svc.add_watch(
        "hn", "FastAPI launches", {"q": "fastapi", "tags": "show_hn"}, with_threads=True
    )

    found = await svc.refresh_watch(watch.id)  # type: ignore[arg-type]

    tree = _fixture("thread.json")
    stored = {
        r.external_id for r in (await async_db_session.exec(select(ResearchItem))).all()
    }
    assert found == len(_fixture("search_stories.json")["hits"])
    assert {str(c["id"]) for c in tree["children"]} <= stored
    assert [i.external_id for i in await svc.search("fastapi", kind="story")]


def test_every_query_field_says_what_it_is_and_what_goes_in_it() -> None:
    """A form built from the query (the research page's new-watch form)
    labels each field by its title and explains it by its description."""
    from app.services.hackernews.schemas import HNQuery

    for name, info in HNQuery.model_fields.items():
        assert info.title and info.description, name
