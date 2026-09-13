"""Typed results and the single process boundary for Python feedback checks."""

import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TextIO, TypeAlias, TypeVar

Target = TypeVar("Target", contravariant=True)


@dataclass(frozen=True, slots=True)
class Location:
    """A source location, optionally narrowed to a line and symbol."""

    path: Path
    line: int | None = None
    symbol: str | None = None


@dataclass(frozen=True, slots=True)
class Violation:
    """A completed check found content that violates a named rule."""

    message: str
    location: Location | None = None
    rule: str | None = None


@dataclass(frozen=True, slots=True)
class InvalidTarget:
    """The caller supplied a target that the check cannot evaluate."""

    target: str
    message: str


@dataclass(frozen=True, slots=True)
class IncompleteCheck:
    """The check could not complete, so success must not be reported."""

    check: str
    message: str


Problem: TypeAlias = Violation | InvalidTarget | IncompleteCheck


@dataclass(frozen=True, slots=True)
class CheckResult:
    """The problems produced by one complete check evaluation."""

    problems: tuple[Problem, ...] = ()

    @classmethod
    def from_problems(cls, problems: Iterable[Problem]) -> "CheckResult":
        """Materialize problems once so rendering and status always agree."""
        return cls(tuple(problems))

    @property
    def exit_code(self) -> Literal[0, 1]:
        """Map an empty or nonempty problem set to the feedback contract."""
        return 1 if self.problems else 0


class Check(Protocol[Target]):
    """Evaluate a typed target without printing or choosing a process status."""

    name: str

    def evaluate(self, target: Target) -> CheckResult: ...


def render(problem: Problem) -> str:
    """Render one typed problem as a concise actionable diagnostic."""
    if isinstance(problem, InvalidTarget):
        return f"{problem.target}: {problem.message}"
    if isinstance(problem, IncompleteCheck):
        return f"{problem.check} could not complete: {problem.message}"
    prefix = ""
    if problem.location is not None:
        parts = [str(problem.location.path)]
        if problem.location.line is not None:
            parts.append(str(problem.location.line))
        if problem.location.symbol is not None:
            parts.append(problem.location.symbol)
        prefix = f"{':'.join(parts)}: "
    rule = f"[{problem.rule}] " if problem.rule else ""
    return f"{prefix}{rule}{problem.message}"


def run_check(check: Check[Target], target: Target, stderr: TextIO | None = None) -> Literal[0, 1]:
    """Evaluate, render only failures, and return exactly zero or one."""
    destination = stderr if stderr is not None else sys.stderr
    try:
        result = check.evaluate(target)
    except Exception as error:  # A crashed check must fail closed at the process boundary.
        result = CheckResult((IncompleteCheck(check.name, str(error)),))
    for problem in result.problems:
        print(render(problem), file=destination)
    return result.exit_code
