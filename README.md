# aegis-stack-hackernews

Hacker News as a source for the [Aegis Stack](https://github.com/lbedner/aegis-stack) research service: saved searches over Hacker News stories and comments, refreshed nightly, kept in your project's database, and read by your agents, MCP clients, API and CLI.

The plugin only talks to Hacker News, through [Algolia's public API](https://hn.algolia.com/api) (free, no key). Storing, refreshing, the read tools, the API and the CLI are the research service's, which `aegis add hackernews` brings in if your project does not have it.

## Install

```bash
pip install aegis-stack-hackernews   # or: pip install -e . from a checkout
cd my-app
aegis add hackernews
```

## Use

```bash
# Show HN posts about FastAPI with 50+ points, and their comment threads
my-app research add hn "FastAPI launches" '{"q": "fastapi", "tags": "show_hn", "min_points": 50}' --threads
my-app research refresh
my-app research search "template"
```

A watch's query:

| Field | What it does |
|---|---|
| `q` | The words to search for (required) |
| `tags` | `story`, `comment`, `show_hn` or `ask_hn` |
| `min_points` | Only items with at least this many points |
| `since` | Only items posted on or after this date |
| `sort` | `relevance` (default) or `newest` |
| `limit` | How many hits a refresh keeps (default 50, at most 500) |

With `--threads` (`with_threads` over the API), each found story's whole discussion is stored under it, one request per thread. A comment found by search is read with the thread it belongs to.

Agents and MCP clients read the results through the research service's `research_search` and `research_thread` tools; the API is under `/api/v1/research`.

## What it stores

Each story or comment is a research item with source `hn`: title, url, text (as plain text), author, posted time, points as `score`, comment count, and in `data` Algolia's tags (`show_hn`, `ask_hn`, ...) and, for a comment, the title of its story.

## Develop

```bash
make install     # uv sync
make test        # the spec's tests
make check       # lint + test
```

The template's own tests (`templates/{{ project_slug }}/tests/services/test_hackernews_source.py`, against recorded Algolia responses) run inside a generated project:

```bash
aegis init demo -s auth && cd demo && aegis add hackernews
uv run pytest tests/services/test_hackernews_source.py
```

## License

MIT
