"""Check that external GitHub Actions are pinned to full-length commit SHAs."""

import re
import sys
from pathlib import Path
from typing import TypeAlias

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    InvalidTarget,
    Location,
    Problem,
    Violation,
    run_check,
)

USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(.*)$")
FULL_SHA = re.compile(r"[0-9a-fA-F]{40}")
HEX = re.compile(r"[0-9a-fA-F]+")
LOCAL_PREFIXES = ("./", "$/", "/.github/", "$.github/")
Target: TypeAlias = Path | tuple[Path, ...]


def use_reference(rest: str) -> str | None:
    """Return the single scalar reference from the text after uses:, or None."""
    stripped = rest.strip()
    if not stripped or stripped.startswith((">", "|")):
        return None
    return stripped.split()[0].strip("\"'")


def reference_kind(value: str) -> str:
    """Classify one uses reference as local, container or external."""
    if value.startswith("docker://") or "://" in value:
        return "container"
    if value.startswith(LOCAL_PREFIXES):
        return "local"
    return "external"


def pinning_problem(value: str, location: Location) -> Problem | None:
    """Return one typed problem when an external reference is not fully pinned."""
    if reference_kind(value) != "external":
        return None
    reference, separator, pin = value.rpartition("@")
    if separator and reference and FULL_SHA.fullmatch(pin):
        return None
    if separator and HEX.fullmatch(pin):
        message = (
            f"external Action '{reference}' is pinned to a {len(pin)}-character commit SHA; "
            "pin it to the full-length 40-character commit SHA."
        )
        rule = "short-sha"
    else:
        message = (
            f"external Action '{value}' is not pinned to a full-length commit SHA; "
            "replace the mutable tag or branch with a 40-character commit SHA."
        )
        rule = "unpinned-action"
    return Violation(message, location, rule=rule)


def line_problem(path: Path, number: int, line: str) -> Problem | None:
    """Return the typed problem for one workflow line, when it has one."""
    match = USES.match(line)
    if match is None:
        return None
    value = use_reference(match.group(1))
    if value is None:
        return IncompleteCheck(
            ShaPinningCheck.name,
            f"{path}:{number}: cannot inspect this empty or multi-line uses value.",
        )
    return pinning_problem(value, Location(path, line=number))


def file_problems(path: Path) -> list[Problem]:
    """Inspect the uses lines of one workflow file without executing anything."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [IncompleteCheck(ShaPinningCheck.name, f"{path}: cannot inspect workflow: {error}")]
    return [
        problem
        for number, line in enumerate(text.splitlines(), start=1)
        if (problem := line_problem(path, number, line)) is not None
    ]


def discover(path: Path) -> tuple[set[Path], list[InvalidTarget]]:
    """Discover workflow files at one supplied path."""
    if path.is_file():
        return {path}, []
    if path.is_dir():
        return set(path.rglob("*.yml")) | set(path.rglob("*.yaml")), []
    return set(), [InvalidTarget(str(path), "workflow path does not exist.")]


class ShaPinningCheck:
    """Evaluate full-length SHA pinning across GitHub Actions workflow files."""

    name = "Action SHA pinning check"

    def evaluate(self, target: Target) -> CheckResult:
        """Discover workflow files and return typed pinning problems."""
        paths = (target,) if isinstance(target, Path) else target
        files: set[Path] = set()
        problems: list[Problem] = []
        for path in paths:
            discovered, discovery_problems = discover(path)
            files.update(discovered)
            problems.extend(discovery_problems)
        if not files and not problems:
            problems.append(
                InvalidTarget(
                    ", ".join(str(path) for path in paths) or ".github/workflows",
                    "No workflow files found; check the supplied paths.",
                )
            )
        for path in sorted(files):
            problems.extend(file_problems(path))
        return CheckResult.from_problems(problems)


def main(arguments: list[str]) -> int:
    """Adapt command-line paths to the shared feedback-check runner."""
    paths = tuple(Path(argument) for argument in arguments) or (Path(".github/workflows"),)
    return run_check(ShaPinningCheck(), paths)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
