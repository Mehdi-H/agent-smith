"""Configuration loading against real TOML files and invocation directories."""

from pathlib import Path

import pytest

from agent_smith.adapters.configuration import TomlConfiguration
from agent_smith.application.ports import (
    CommandSection,
    GenerationError,
    GenerationRequest,
    OverviewSection,
)


def test_missing_default_configuration_uses_convention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given an invocation directory with no configuration file.
    monkeypatch.chdir(tmp_path)
    # When the default configuration is loaded.
    request = TomlConfiguration().load(None, output=None, no_overview=False)
    # Then the built-in overview and AGENTS.md output are selected.
    assert request == GenerationRequest()


def test_configuration_loads_sections_and_cli_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given a default configuration that enables overview and custom sections.
    monkeypatch.chdir(tmp_path)
    Path("agent-smith.toml").write_text(
        'output = "configured.md"\n[overview]\nsource = "intro.md"\ntitle = "Introduction"\n'
        '[[sections]]\ntitle = "Custom"\ncommand = "./custom.sh"\n',
        encoding="utf-8",
    )
    # When CLI output and overview overrides are applied.
    request = TomlConfiguration().load(None, output="chosen.md", no_overview=True)
    # Then explicit CLI settings take precedence and custom commands are preserved.
    assert request == GenerationRequest("chosen.md", (CommandSection("Custom", "./custom.sh"),))


def test_explicit_configuration_customizes_builtin(tmp_path: Path) -> None:
    # Given a named configuration with a customized built-in source and title.
    config = tmp_path / "custom.toml"
    config.write_text('[overview]\nsource = "intro.md"\ntitle = "Introduction"\n', encoding="utf-8")
    # When that configuration is selected.
    request = TomlConfiguration().load(str(config), output=None, no_overview=False)
    # Then the built-in extractor remains enabled with the configured values.
    assert request.sections == (OverviewSection("Introduction", "intro.md"),)


@pytest.mark.parametrize(
    "content",
    [
        None,
        "[broken",
        "unknown = true",
        'overview = "bad"',
        '[overview]\nenabled = "false"',
        'sections = "bad"',
        "sections = [1]",
        '[[sections]]\ntitle = "Custom"',
        '[[sections]]\ntitle = "Custom"\ncommand = 1',
        'output = "README.md"',
        'output = ""',
    ],
)
def test_invalid_configuration_fails_with_diagnostic(content: str | None, tmp_path: Path) -> None:
    # Given a missing, malformed or unsupported configuration.
    config = tmp_path / "bad.toml"
    if content is not None:
        config.write_text(content, encoding="utf-8")
    # When loading is attempted.
    with pytest.raises(GenerationError) as failure:
        TomlConfiguration().load(str(config), output=None, no_overview=False)
    # Then an actionable application error is available to the CLI.
    assert str(failure.value)
