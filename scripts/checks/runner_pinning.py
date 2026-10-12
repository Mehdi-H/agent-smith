"""Check that GitHub Actions jobs run on explicitly versioned runner labels."""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    Location,
    Problem,
    Violation,
    run_check,
)
from scripts.checks.sha_pinning import discover_files

KEY = re.compile(r"^( *)([^\s#\-][^:]*):(?:\s|$)")
RUNS_ON = re.compile(r"^\s*runs-on:(.*)$")
COMMENT = re.compile(r"\s+#.*$")
FLOATING = re.compile(r"-latest$", re.IGNORECASE)
Target: TypeAlias = Path | tuple[Path, ...]


@dataclass(slots=True)
class JobCursor:
    """Follow which job of a workflow's top-level jobs mapping a line belongs to."""

    in_jobs: bool = False
    job_indent: int | None = None
    job: str | None = None

    def advance(self, line: str) -> str | None:
        """Consume one line and return the id of the job containing it."""
        match = KEY.match(line)
        if match is not None:
            self._enter(len(match.group(1)), match.group(2).strip().strip("\"'"))
        return self.job

    def _enter(self, indent: int, key: str) -> None:
        """Track top-level sections and the job keys nested directly under jobs."""
        if indent == 0:
            self.in_jobs, self.job_indent, self.job = key == "jobs", None, None
        elif self.in_jobs and indent == (self.job_indent or indent):
            self.job_indent, self.job = indent, key


def runner_labels(value: str) -> tuple[str, ...] | None:
    """Return the literal labels of one inline runs-on value, or None if not inspectable."""
    text = COMMENT.sub("", value).strip()
    if not text or "${{" in text or text.startswith(("|", ">", "{")):
        return None
    if text.startswith("["):
        if not text.endswith("]"):
            return None
        text = text[1:-1]
    labels = tuple(item.strip().strip("\"'") for item in text.split(","))
    return labels if all(labels) else None


def runs_on_problems(path: Path, number: int, value: str, job: str | None) -> list[Problem]:
    """Return typed problems for one runs-on value of a workflow job."""
    location = Location(path, line=number, symbol=job)
    labels = runner_labels(value)
    if labels is None:
        return [
            IncompleteCheck(
                RunnerPinningCheck.name,
                f"{path}:{number}:{job}: cannot inspect this runs-on value; "
                "write the runner label inline, e.g. runs-on: ubuntu-24.04.",
            )
        ]
    return [
        Violation(
            f"job runs on the floating runner label '{label}'; pin an explicit image "
            "version such as ubuntu-24.04 so label migrations cannot change the runner.",
            location,
            rule="floating-runner",
        )
        for label in labels
        if FLOATING.search(label)
    ]


def file_problems(path: Path) -> list[Problem]:
    """Inspect the runs-on lines of one workflow file without executing anything."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        message = f"{path}: cannot inspect workflow: {error}"
        return [IncompleteCheck(RunnerPinningCheck.name, message)]
    cursor = JobCursor()
    problems: list[Problem] = []
    for number, line in enumerate(text.splitlines(), start=1):
        job = cursor.advance(line)
        if (match := RUNS_ON.match(line)) is not None:
            problems.extend(runs_on_problems(path, number, match.group(1), job))
    return problems


class RunnerPinningCheck:
    """Evaluate runner label pinning across GitHub Actions workflow files."""

    name = "Runner pinning check"

    def evaluate(self, target: Target) -> CheckResult:
        """Discover workflow files and return typed runner pinning problems."""
        paths = (target,) if isinstance(target, Path) else target
        files, problems = discover_files(paths)
        for path in sorted(files):
            problems.extend(file_problems(path))
        return CheckResult.from_problems(problems)


def main(arguments: list[str]) -> int:
    """Adapt command-line paths to the shared feedback-check runner."""
    paths = tuple(Path(argument) for argument in arguments) or (Path(".github/workflows"),)
    return run_check(RunnerPinningCheck(), paths)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
