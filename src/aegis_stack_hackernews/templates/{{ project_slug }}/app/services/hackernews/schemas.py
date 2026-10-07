"""What a Hacker News watch can ask for, and what an item keeps beyond the
columns every research source shares."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HNQuery(BaseModel):
    """A watch's search: Algolia's, narrowed."""

    model_config = ConfigDict(extra="forbid")

    # ``title`` labels each field in a form and ``description`` says what
    # goes in it: the research page builds its new-watch form from these.
    q: str = Field(
        min_length=1,
        title="Search for",
        description="The words a post must match, e.g. open source personal finance.",
    )
    tags: Literal["story", "comment", "show_hn", "ask_hn"] | None = Field(
        default=None,
        title="Type",
        description="Usually story; Any also returns single comments with the words.",
    )
    min_points: int | None = Field(
        default=None, ge=0, title="Min points", description="Skip posts below this."
    )
    since: date | None = Field(
        default=None, title="Posted since", description="Only posts from this day on."
    )
    sort: Literal["relevance", "newest"] = Field(
        default="relevance",
        title="Sort",
        description="Relevance: best matches first. Newest: latest first.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        title="Results",
        description="How many to keep each refresh, up to 500.",
    )


class HNData(BaseModel):
    """Extras an item keeps: Algolia's tags (show_hn, ask_hn, ...) and, for
    a comment found by search, the title of the story it is under."""

    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(default_factory=list)
    story_title: str | None = None
