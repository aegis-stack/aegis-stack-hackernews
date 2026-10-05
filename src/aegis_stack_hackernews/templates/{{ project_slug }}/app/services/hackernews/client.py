"""Algolia's Hacker News API: search, and one item with its whole thread.

Public and keyless. ``items/{id}`` returns a story and every reply nested in
one response, so a thread is one request however long it is.
"""

from datetime import UTC, datetime, time
from typing import Any

import httpx

from app.services.hackernews.schemas import HNQuery

API = "https://hn.algolia.com/api/v1"
TIMEOUT = 20.0
# Algolia's page size ceiling.
PAGE = 1000

# Swapped for a mock transport in tests; None is the real network.
_transport: httpx.AsyncBaseTransport | None = None


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=API, timeout=TIMEOUT, transport=_transport)


async def search(query: HNQuery) -> list[dict[str, Any]]:
    """The hits ``query`` asks for, at most ``query.limit``."""
    filters = []
    if query.min_points is not None:
        filters.append(f"points>={query.min_points}")
    if query.since is not None:
        start = datetime.combine(query.since, time(), tzinfo=UTC)
        filters.append(f"created_at_i>={int(start.timestamp())}")
    params: dict[str, Any] = {"query": query.q, "hitsPerPage": min(query.limit, PAGE)}
    if query.tags:
        params["tags"] = query.tags
    if filters:
        params["numericFilters"] = ",".join(filters)
    path = "/search_by_date" if query.sort == "newest" else "/search"
    async with _client() as client:
        response = await client.get(path, params=params)
        response.raise_for_status()
    return response.json()["hits"][: query.limit]


async def item(item_id: str) -> dict[str, Any]:
    """One item and everything under it, nested as ``children``."""
    async with _client() as client:
        response = await client.get(f"/items/{item_id}")
        response.raise_for_status()
    return response.json()
