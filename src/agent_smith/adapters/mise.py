"""Render the declared mise tools without running mise or resolving versions."""

import tomllib

from agent_smith.application.generation import inline_code
from agent_smith.application.ports import GenerationError


def literal(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise GenerationError(f"{name} must be a nonempty, single-line string.")
    return inline_code(value)


def version_label(value: object, name: str) -> str:
    if isinstance(value, dict):
        value = value.get("version")
    return literal(value, f"tools.{name}.version")


def tool_versions(value: object, name: str) -> str:
    versions = value if isinstance(value, list) else [value]
    if not versions:
        raise GenerationError(f"tools.{name} must declare at least one version.")
    return ", ".join(version_label(version, name) for version in versions)


class MiseTechStackParser:
    def render(self, content: str) -> str:
        try:
            tools = tomllib.loads(content).get("tools", {})
        except ValueError as error:
            raise GenerationError(f"Invalid mise TOML: {error}") from error
        if not isinstance(tools, dict) or not tools:
            raise GenerationError("Expected a nonempty [tools] table in mise.toml.")
        return "\n".join(
            f"- {literal(name, 'Tool name')} — {tool_versions(value, name)}"
            for name, value in tools.items()
        )
