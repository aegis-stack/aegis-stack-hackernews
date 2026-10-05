"""PluginSpec for ``aegis-stack-hackernews``: Hacker News as a source for
the research service.

The plugin only talks to Hacker News (Algolia's public API, no key) and
maps what it returns onto research items. Storing, refreshing, the tools
an agent reads them with, the API and the CLI are the research service's,
which ``aegis add hackernews`` brings in when a project lacks it. Aegis
discovers this spec through the ``aegis.plugins`` entry point.
"""

from aegis.core.file_manifest import FileManifest
from aegis.core.plugins.spec import PluginKind, PluginSpec


def get_spec() -> PluginSpec:
    """Return the plugin spec."""
    return PluginSpec(
        name="hackernews",
        kind=PluginKind.SERVICE,
        description="Hacker News as a source for the Aegis Stack research service",
        version="0.1.0",
        verified=False,
        # The source registers in ``app/services/hackernews/sources.py``,
        # which the research service finds on disk: nothing to wire.
        required_services=["research"],
        files=FileManifest(
            primary=[
                "app/services/hackernews",
                "tests/services/test_hackernews_source.py",
                "tests/fixtures/hackernews",
            ]
        ),
    )
