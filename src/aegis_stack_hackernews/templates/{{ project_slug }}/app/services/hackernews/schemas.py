"""What a Hacker News watch can ask for, and what an item keeps beyond the
columns every research source shares."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HNQuery(BaseModel):
    """A watch's search: Algolia's, narrowed."""

    model_config = ConfigDict(extra="forbid")

    q: str = Field(min_length=1, description="The words to search for.")
    tags: Literal["story", "comment", "show_hn", "ask_hn"] | None = Field(
        default=None, description="Only stories, comments, Show HN or Ask HN."
    )
    min_points: int | None = Field(default=None, ge=0)
    since: date | None = Field(default=None, description="Posted on or after.")
    sort: Literal["relevance", "newest"] = "relevance"
    limit: int = Field(default=50, ge=1, le=500)


class HNData(BaseModel):
    """Extras an item keeps: Algolia's tags (show_hn, ask_hn, ...) and, for
    a comment found by search, the title of the story it is under."""

    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(default_factory=list)
    story_title: str | None = None
