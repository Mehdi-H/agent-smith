"""Interpret the standard just --list output produced by a project's help recipe."""

import re

from agent_smith.application.generation import heading, inline_code
from agent_smith.application.ports import GenerationError

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
DESCRIPTION = re.compile(r"""("(?:\\.|[^"\\])*"|'[^']*')|(\s+#\s?)""")
RECIPE = re.compile(r"[\w-]+(?:::[\w-]+)*(?:\s+.*)?\Z")


def split_description(line: str) -> tuple[str, str]:
    for match in DESCRIPTION.finditer(line):
        if match.group(2):
            return line[: match.start()].rstrip(), line[match.end() :]
    return line, ""


def render_recipe(line: str) -> str:
    signature, description = split_description(line)
    if not RECIPE.fullmatch(signature):
        raise GenerationError(f"Unsupported just help recipe: {line!r}.")
    suffix = f" — {description}" if description else ""
    return f"- {inline_code('just ' + signature)}{suffix}"


class JustHelpParser:
    def render(self, output: str) -> str:
        lines = ANSI.sub("", output).splitlines()
        lines = [line.rstrip() for line in lines if line.strip()]
        if not lines or lines[0].strip() != "Available recipes:":
            raise GenerationError("Expected just help to print the standard just --list output.")
        parts = [self.render_line(line) for line in lines[1:]]
        if not any(part.startswith("- ") for part in parts):
            raise GenerationError("just help did not list any available commands.")
        return "\n".join(parts).strip()

    def render_line(self, line: str) -> str:
        if not line[0].isspace():
            raise GenerationError(f"Unsupported just help output: {line!r}.")
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return f"\n### {heading(stripped[1:-1])}\n"
        return render_recipe(stripped)
