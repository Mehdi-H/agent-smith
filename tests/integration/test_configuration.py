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


def test_missing_default_configuration_uses_convention(tmp_path: Path) -> None:
    # Given an invocation directory with no configuration file.
    configuration = TomlConfiguration(directory=tmp_path)
    # When the default configuration is loaded.
    request = configuration.load(None, output=None, no_overview=False)
    # Then the built-in overview and AGENTS.md output are selected.
    assert request == GenerationRequest()


def test_configuration_loads_sections_and_cli_overrides(tmp_path: Path) -> None:
    # Given a default configuration that enables overview and custom sections.
    (tmp_path / "agent-smith.toml").write_text(
        'output = "configured.md"\n[overview]\nsource = "intro.md"\ntitle = "Introduction"\n'
        '[[sections]]\ntitle = "Custom"\ncommand = "./custom.sh"\n',
        encoding="utf-8",
    )
    # When CLI output and overview overrides are applied.
    request = TomlConfiguration(directory=tmp_path).load(None, output="chosen.md", no_overview=True)
    # Then explicit CLI settings take precedence and custom commands are preserved.
    assert request == GenerationRequest("chosen.md", (CommandSection("Custom", "./custom.sh"),))


def test_explicit_configuration_customizes_builtin(tmp_path: Path) -> None:
    # Given a named configuration with a customized built-in source and title.
    config = tmp_path / "custom.toml"
    config.write_text('[overview]\nsource = "intro.md"\ntitle = "Introduction"\n', encoding="utf-8")
    # When that configuration is selected.
    request = TomlConfiguration(directory=tmp_path).load(
        str(config), output=None, no_overview=False
    )
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
        TomlConfiguration(directory=tmp_path).load(str(config), output=None, no_overview=False)
    # Then an actionable application error is available to the CLI.
    assert str(failure.value)


@pytest.mark.parametrize("filename", ["justfile", "Justfile", ".justfile"])
def test_justfile_enables_available_commands_by_convention(tmp_path: Path, filename: str) -> None:
    # Given a project containing a conventional justfile name.
    from agent_smith.application.ports import AvailableCommandsSection

    (tmp_path / filename).write_text("help:\n    just --list\n")
    # When configuration is loaded without a custom file.
    request = TomlConfiguration(tmp_path).load(None, output=None, no_overview=False)
    # Then available commands follows the overview without requiring user scripts.
    assert request.sections == (OverviewSection(), AvailableCommandsSection())


@pytest.mark.parametrize("disabled_by", ["config", "cli"])
def test_available_commands_can_be_disabled(tmp_path: Path, disabled_by: str) -> None:
    # Given a justfile whose help must not be executed.
    (tmp_path / "justfile").write_text("help:\n    exit 99\n")
    (tmp_path / "agent-smith.toml").write_text(
        "[available_commands]\nenabled = " + ("false" if disabled_by == "config" else "true")
    )
    # When the user disables the section by either supported mechanism.
    request = TomlConfiguration(tmp_path).load(
        None, output=None, no_overview=False, no_available_commands=disabled_by == "cli"
    )
    # Then the overview remains and no available-commands section is scheduled.
    assert request.sections == (OverviewSection(),)


def test_available_commands_custom_configuration(tmp_path: Path) -> None:
    # Given an explicit help source independent of justfile detection.
    from agent_smith.application.ports import AvailableCommandsSection

    (tmp_path / "agent-smith.toml").write_text(
        '[available_commands]\nenabled = true\ntitle = "Usage"\ncommand = "just --list"\n'
    )
    # When configuration enables and customizes the built-in.
    request = TomlConfiguration(tmp_path).load(None, output=None, no_overview=True)
    # Then the configured title and exact source command reach the application.
    assert request.sections == (AvailableCommandsSection("Usage", "just --list"),)


@pytest.mark.parametrize("value", ['enabled = "yes"', 'title = ""\nenabled = true', "unknown = 1"])
def test_invalid_available_commands_configuration(tmp_path: Path, value: str) -> None:
    # Given invalid settings for the new built-in.
    (tmp_path / "agent-smith.toml").write_text("[available_commands]\n" + value)
    # When the configuration is read.
    with pytest.raises(GenerationError) as error:
        TomlConfiguration(tmp_path).load(None, output=None, no_overview=False)
    # Then a diagnostic identifies the invalid configuration.
    assert str(error.value)
