"""Hacker News as a research source: Algolia's hits and threads mapped onto
the items every source shares (``app.services.research.registry``)."""

from collections.abc import Iterator
from datetime import datetime
import html
import re
from typing import Any

from app.services.hackernews import client
from app.services.hackernews.schemas import HNData, HNQuery
from app.services.research.registry import Source, SourceItem, register_source

_PARAGRAPH = re.compile(r"<p>|<br\s*/?>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")


def plain(text: str | None) -> str | None:
    """Hacker News text is HTML; stored as the words it says."""
    if not text:
        return None
    return html.unescape(_TAG.sub("", _PARAGRAPH.sub("\n\n", text))).strip() or None


def _when(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def from_hit(hit: dict[str, Any]) -> SourceItem:
    """One search hit: a story, or a comment with the story it is under."""
    tags = [t for t in hit.get("_tags", []) if not t.startswith(("author_", "story_"))]
    is_comment = "comment" in tags
    story_id = hit.get("story_id")
    return SourceItem(
        external_id=str(hit["objectID"]),
        kind="comment" if is_comment else "story",
        parent_external_id=str(hit["parent_id"]) if hit.get("parent_id") else None,
        root_external_id=str(story_id) if is_comment and story_id else None,
        title=hit.get("title"),
        url=hit.get("url"),
        text=plain(hit.get("comment_text") or hit.get("story_text")),
        author=hit.get("author"),
        published_at=_when(hit.get("created_at")),
        score=hit.get("points"),
        comment_count=hit.get("num_comments"),
        data=HNData(tags=tags, story_title=hit.get("story_title")).model_dump(),
    )


def _replies(node: dict[str, Any]) -> int:
    return sum(1 + _replies(child) for child in node.get("children", []))


def from_tree(node: dict[str, Any]) -> Iterator[SourceItem]:
    """One item of ``items/{id}`` and every reply under it, top first. The
    tree carries no comment count, so the top counts what is under it."""
    yield SourceItem(
        external_id=str(node["id"]),
        kind=node.get("type") or "comment",
        parent_external_id=str(node["parent_id"]) if node.get("parent_id") else None,
        root_external_id=str(node["story_id"]) if node.get("story_id") else None,
        title=node.get("title"),
        url=node.get("url"),
        text=plain(node.get("text")),
        author=node.get("author"),
        published_at=_when(node.get("created_at")),
        score=node.get("points"),
        comment_count=_replies(node) if node.get("type") == "story" else None,
        data=HNData().model_dump(),
    )
    for child in node.get("children", []):
        yield from from_tree(child)


async def search(query: HNQuery) -> list[SourceItem]:
    return [from_hit(hit) for hit in await client.search(query)]


async def thread(external_id: str) -> list[SourceItem]:
    return list(from_tree(await client.item(external_id)))


register_source(
    Source(
        name="hn",
        title="Hacker News",
        query=HNQuery,
        search=search,
        thread=thread,
        data=HNData,
    )
)
