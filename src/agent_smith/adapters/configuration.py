"""Load optional TOML configuration and apply explicit CLI overrides."""

import tomllib
from pathlib import Path
from typing import cast

from agent_smith.application.ports import (
    ArchitectureDecisionsSection,
    AvailableCommandsSection,
    CommandSection,
    GenerationError,
    GenerationRequest,
    OverviewSection,
    Section,
    TechStackSection,
)


def table(value: object, allowed: set[str], name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise GenerationError(f"{name} must be a TOML table.")
    result = cast(dict[str, object], value)
    unknown = result.keys() - allowed
    if unknown:
        raise GenerationError(f"Unknown {name} settings: {', '.join(sorted(unknown))}.")
    return result


def text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(c in value for c in "\r\n\0"):
        raise GenerationError(f"{name} must be a nonempty string on one line.")
    return value


def overview_sections(
    value: object, destination: str, no_overview: bool, directory: Path
) -> list[Section]:
    overview = table(value, {"enabled", "source", "title"}, "overview")
    enabled = overview.get("enabled", True)
    if not isinstance(enabled, bool):
        raise GenerationError("overview.enabled must be a boolean.")
    sections: list[Section] = []
    if enabled and not no_overview:
        readme = text(overview.get("source", "README.md"), "overview.source")
        if (directory / readme).resolve() == (directory / destination).resolve():
            raise GenerationError("The output must not overwrite the overview source.")
        sections.append(
            OverviewSection(text(overview.get("title", "Overview"), "overview.title"), readme)
        )
    return sections


class TomlConfiguration:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory if directory is not None else Path.cwd()

    def load(
        self,
        path: str | None,
        *,
        output: str | None,
        no_overview: bool,
        no_available_commands: bool = False,
        no_tech_stack: bool = False,
        no_architecture_decisions: bool = False,
    ) -> GenerationRequest:
        source = self.directory / (path or "agent-smith.toml")
        data: dict[str, object] = {}
        try:
            if path is not None or source.exists():
                with source.open("rb") as stream:
                    data = tomllib.load(stream)
        except (OSError, ValueError) as error:
            raise GenerationError(f"Cannot load configuration {str(source)!r}: {error}") from error
        data = table(
            data,
            {
                "output",
                "overview",
                "available_commands",
                "tech_stack",
                "architecture_decisions",
                "sections",
            },
            "configuration",
        )
        destination = text(
            output if output is not None else data.get("output", "AGENTS.md"), "output"
        )
        sections = overview_sections(
            data.get("overview", {}), destination, no_overview, self.directory
        )
        sections.extend(
            tech_stack_sections(
                data.get("tech_stack", {}), self.directory, destination, no_tech_stack
            )
        )
        sections.extend(
            available_commands_sections(
                data.get("available_commands", {}), self.directory, no_available_commands
            )
        )
        sections.extend(
            architecture_decisions_sections(
                data.get("architecture_decisions", {}),
                self.directory,
                destination,
                no_architecture_decisions,
            )
        )
        sections.extend(custom_sections(data.get("sections", [])))
        return GenerationRequest(destination, tuple(sections))


def custom_sections(custom: object) -> list[Section]:
    sections: list[Section] = []
    if not isinstance(custom, list):
        raise GenerationError("sections must be an array of TOML tables.")
    for index, item in enumerate(custom):
        section = table(item, {"title", "command"}, f"sections[{index}]")
        sections.append(
            CommandSection(
                text(section.get("title"), "section.title"),
                text(section.get("command"), "section.command"),
            )
        )
    return sections


def available_commands_sections(value: object, directory: Path, disabled: bool) -> list[Section]:
    settings = table(value, {"enabled", "title", "command"}, "available_commands")
    detected = any(
        path.is_file() and path.name.lower() in {"justfile", ".justfile"}
        for path in directory.iterdir()
    )
    enabled = settings.get("enabled", detected)
    if not isinstance(enabled, bool):
        raise GenerationError("available_commands.enabled must be a boolean.")
    if disabled or not enabled:
        return []
    return [
        AvailableCommandsSection(
            text(settings.get("title", "Available commands"), "available_commands.title"),
            text(settings.get("command", "just help"), "available_commands.command"),
        )
    ]


def tech_stack_sections(
    value: object, directory: Path, destination: str, disabled: bool
) -> list[Section]:
    settings = table(value, {"enabled", "title", "source"}, "tech_stack")
    source = text(settings.get("source", "mise.toml"), "tech_stack.source")
    enabled = settings.get("enabled", (directory / source).is_file())
    if not isinstance(enabled, bool):
        raise GenerationError("tech_stack.enabled must be a boolean.")
    if disabled or not enabled:
        return []
    if (directory / source).resolve() == (directory / destination).resolve():
        raise GenerationError("The output must not overwrite the tech stack source.")
    return [
        TechStackSection(text(settings.get("title", "Main tech stack"), "tech_stack.title"), source)
    ]


def architecture_decisions_sections(
    value: object, directory: Path, destination: str, disabled: bool
) -> list[Section]:
    settings = table(value, {"enabled", "title"}, "architecture_decisions")
    enabled = settings.get("enabled", (directory / ".adr-dir").is_file())
    if not isinstance(enabled, bool):
        raise GenerationError("architecture_decisions.enabled must be a boolean.")
    if disabled or not enabled:
        return []
    if (directory / ".adr-dir").resolve() == (directory / destination).resolve():
        raise GenerationError("The output must not overwrite .adr-dir.")
    return [
        ArchitectureDecisionsSection(
            text(settings.get("title", "Architecture decisions"), "architecture_decisions.title")
        )
    ]
