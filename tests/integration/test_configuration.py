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


def test_mise_file_enables_tech_stack_before_available_commands(tmp_path: Path) -> None:
    # Given root mise and just files and a trailing custom section.
    from agent_smith.application.ports import AvailableCommandsSection, TechStackSection

    (tmp_path / "mise.toml").write_text('[tools]\npython = "3.14"')
    (tmp_path / "justfile").write_text("help:\n    just --list\n")
    (tmp_path / "agent-smith.toml").write_text('[[sections]]\ntitle="Extra"\ncommand="echo extra"')
    # When defaults are detected from the filesystem.
    request = TomlConfiguration(tmp_path).load(None, output=None, no_overview=False)
    # Then the tech stack follows overview and precedes available commands and custom sections.
    assert request.sections == (
        OverviewSection(),
        TechStackSection(),
        AvailableCommandsSection(),
        CommandSection("Extra", "echo extra"),
    )


@pytest.mark.parametrize("disabled_by", ["cli", "config"])
def test_tech_stack_can_be_disabled(tmp_path: Path, disabled_by: str) -> None:
    # Given a mise file and an explicit setting overridable from the CLI.
    (tmp_path / "mise.toml").write_text("[broken")
    (tmp_path / "agent-smith.toml").write_text(
        "[tech_stack]\nenabled = " + ("false" if disabled_by == "config" else "true")
    )
    # When the built-in is disabled.
    request = TomlConfiguration(tmp_path).load(
        None, output=None, no_overview=False, no_tech_stack=disabled_by == "cli"
    )
    # Then it is omitted without reading the malformed source.
    assert request.sections == (OverviewSection(),)


def test_tech_stack_custom_source_and_title(tmp_path: Path) -> None:
    # Given a custom source filename and section title.
    from agent_smith.application.ports import TechStackSection

    (tmp_path / "tools.toml").write_text('[tools]\nuv = "latest"')
    (tmp_path / "agent-smith.toml").write_text('[tech_stack]\nsource="tools.toml"\ntitle="Stack"')
    # When the selected file is detected.
    request = TomlConfiguration(tmp_path).load(None, output=None, no_overview=True)
    # Then the custom source and title reach the generation service.
    assert request.sections == (TechStackSection("Stack", "tools.toml"),)


@pytest.mark.parametrize(
    "settings", ['enabled="yes"', 'source=""', 'enabled=true\ntitle=""', "unknown=1"]
)
def test_invalid_tech_stack_configuration(tmp_path: Path, settings: str) -> None:
    # Given invalid extractor settings.
    (tmp_path / "agent-smith.toml").write_text("[tech_stack]\n" + settings)
    # When loading configuration.
    with pytest.raises(GenerationError, match="tech_stack"):
        TomlConfiguration(tmp_path).load(None, output=None, no_overview=False)
    # Then no generated file exists.
    assert not (tmp_path / "AGENTS.md").exists()


def test_output_cannot_overwrite_tech_stack_source(tmp_path: Path) -> None:
    # Given a mise file selected as both input and output.
    (tmp_path / "mise.toml").write_text('[tools]\nuv="latest"')
    # When loading this unsafe output choice.
    with pytest.raises(GenerationError, match="overwrite the tech stack source"):
        TomlConfiguration(tmp_path).load(None, output="mise.toml", no_overview=True)
    # Then the source remains unchanged.
    assert (tmp_path / "mise.toml").read_text() == '[tools]\nuv="latest"'


def test_adr_metadata_enables_architecture_decisions(tmp_path: Path) -> None:
    # Given a root .adr-dir and a custom trailing section.
    from agent_smith.application.ports import ArchitectureDecisionsSection

    (tmp_path / ".adr-dir").write_text("docs/adr\n")
    (tmp_path / "agent-smith.toml").write_text('[[sections]]\ntitle="Extra"\ncommand="echo extra"')
    # When convention-based configuration is loaded.
    request = TomlConfiguration(tmp_path).load(None, output=None, no_overview=False)
    # Then the ADR section follows the overview and precedes custom sections.
    assert request.sections == (
        OverviewSection(),
        ArchitectureDecisionsSection(),
        CommandSection("Extra", "echo extra"),
    )


@pytest.mark.parametrize("disabled_by", ["cli", "config"])
def test_architecture_decisions_can_be_disabled(tmp_path: Path, disabled_by: str) -> None:
    # Given a detected ADR configuration and an explicit enable setting.
    (tmp_path / ".adr-dir").write_text("missing")
    (tmp_path / "agent-smith.toml").write_text(
        "[architecture_decisions]\nenabled=" + ("false" if disabled_by == "config" else "true")
    )
    # When a supported override disables the built-in.
    request = TomlConfiguration(tmp_path).load(
        None, output=None, no_overview=False, no_architecture_decisions=disabled_by == "cli"
    )
    # Then no ADR command is scheduled.
    assert request.sections == (OverviewSection(),)


def test_architecture_decisions_can_be_explicitly_enabled_and_renamed(tmp_path: Path) -> None:
    # Given an explicit enable setting even though .adr-dir is not yet present.
    from agent_smith.application.ports import ArchitectureDecisionsSection

    (tmp_path / "agent-smith.toml").write_text(
        '[architecture_decisions]\nenabled=true\ntitle="Decisions"'
    )
    # When the configuration is loaded.
    request = TomlConfiguration(tmp_path).load(None, output=None, no_overview=True)
    # Then generation must attempt the renamed built-in rather than silently omitting it.
    assert request.sections == (ArchitectureDecisionsSection("Decisions"),)


@pytest.mark.parametrize("settings", ['enabled="yes"', 'enabled=true\ntitle=""', "unknown=true"])
def test_invalid_architecture_decisions_settings(tmp_path: Path, settings: str) -> None:
    # Given malformed extractor configuration.
    (tmp_path / "agent-smith.toml").write_text("[architecture_decisions]\n" + settings)
    # When loading these settings.
    with pytest.raises(GenerationError, match="architecture_decisions"):
        TomlConfiguration(tmp_path).load(None, output=None, no_overview=False)
    # Then no generated file exists.
    assert not (tmp_path / "AGENTS.md").exists()


def test_adr_metadata_cannot_be_overwritten(tmp_path: Path) -> None:
    # Given the source metadata selected as the output path.
    (tmp_path / ".adr-dir").write_text("docs/adr\n")
    # When configuration is loaded.
    with pytest.raises(GenerationError, match="overwrite"):
        TomlConfiguration(tmp_path).load(None, output=".adr-dir", no_overview=True)
    # Then the input metadata remains intact.
    assert (tmp_path / ".adr-dir").read_text() == "docs/adr\n"
