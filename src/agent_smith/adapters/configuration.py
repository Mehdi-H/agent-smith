"""Load optional TOML configuration and apply explicit CLI overrides."""

import sys
from pathlib import Path
from typing import cast

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from agent_smith.application.ports import (
    CommandSection,
    GenerationError,
    GenerationRequest,
    OverviewSection,
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


class TomlConfiguration:
    def load(self, path: str | None, *, output: str | None, no_overview: bool) -> GenerationRequest:
        source = Path(path or "agent-smith.toml")
        data: dict[str, object] = {}
        try:
            if path is not None or source.exists():
                with source.open("rb") as stream:
                    data = tomllib.load(stream)
        except (OSError, ValueError) as error:
            raise GenerationError(f"Cannot load configuration {str(source)!r}: {error}") from error
        data = table(data, {"output", "overview", "sections"}, "configuration")
        destination = text(
            output if output is not None else data.get("output", "AGENTS.md"), "output"
        )
        overview = table(data.get("overview", {}), {"enabled", "source", "title"}, "overview")
        enabled = overview.get("enabled", True)
        if not isinstance(enabled, bool):
            raise GenerationError("overview.enabled must be a boolean.")
        sections: list[OverviewSection | CommandSection] = []
        if enabled and not no_overview:
            readme = text(overview.get("source", "README.md"), "overview.source")
            if Path(readme).resolve() == Path(destination).resolve():
                raise GenerationError("The output must not overwrite the overview source.")
            sections.append(
                OverviewSection(text(overview.get("title", "Overview"), "overview.title"), readme)
            )
        custom = data.get("sections", [])
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
        return GenerationRequest(destination, tuple(sections))
