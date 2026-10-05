"""Pin the contract of ``get_spec()``: anything that changes what
``aegis add hackernews`` installs is a deliberate test update here."""

from pathlib import Path

from aegis.core.plugins.spec import PluginKind

from aegis_stack_hackernews.plugin import get_spec

TEMPLATE = (
    Path(__file__).resolve().parents[1]
    / "src/aegis_stack_hackernews/templates/{{ project_slug }}"
)


def test_the_plugin_is_a_research_source() -> None:
    spec = get_spec()

    assert spec.name == "hackernews"
    assert spec.kind == PluginKind.SERVICE
    assert spec.required_services == ["research"]
    assert not spec.migrations, "a source stores nothing of its own"


def test_every_owned_path_ships_in_the_template() -> None:
    for path in get_spec().files.primary:
        assert (TEMPLATE / path).exists(), path


def test_the_source_registers_where_research_looks() -> None:
    sources = (TEMPLATE / "app/services/hackernews/sources.py").read_text()

    assert "register_source(" in sources and 'name="hn"' in sources
