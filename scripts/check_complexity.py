"""Apply Complexipy only to functions whose source differs from a Git baseline."""

import ast
import os
import subprocess
import sys
import textwrap
import tokenize
from dataclasses import dataclass
from pathlib import Path

from complexipy import code_complexity

from scripts.checks.core import CheckResult, InvalidTarget, Location, Violation, run_check

LIMIT = 8


def git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], text=True)


def baseline() -> str:
    explicit = os.environ.get("COMPLEXITY_BASE")
    if explicit:
        return git("merge-base", explicit, "HEAD").strip()
    branch = git("branch", "--show-current").strip()
    if branch == "main":
        return git("rev-parse", "HEAD^").strip()
    return git("merge-base", "main", "HEAD").strip()


@dataclass(frozen=True)
class Function:
    name: str
    line: int
    source: str


class Functions(ast.NodeVisitor):
    def __init__(self, source: str) -> None:
        self.lines = source.splitlines(keepends=True)
        self.scope: list[str] = []
        self.found: dict[str, Function] = {}
        self.occurrences: dict[str, int] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        name = ".".join(self.scope)
        start = min([node.lineno, *(item.lineno for item in node.decorator_list)])
        source = textwrap.dedent("".join(self.lines[start - 1 : node.end_lineno]))
        occurrence = self.occurrences.get(name, 0)
        self.occurrences[name] = occurrence + 1
        self.found[f"{name}:{occurrence}"] = Function(name, node.lineno, source)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef


def functions(source: str) -> dict[str, Function]:
    visitor = Functions(source)
    visitor.visit(ast.parse(source))
    return visitor.found


def changed_functions(before: str, after: str) -> list[Function]:
    old = functions(before)
    return [
        function
        for name, function in functions(after).items()
        if name not in old or function.source != old[name].source
    ]


def changed_paths(base: str) -> list[str]:
    tracked = git("diff", "--name-only", "--diff-filter=AMRT", "-z", base, "--", "*.py")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", "--", "*.py")
    return sorted(set((tracked + untracked).split("\0")) - {""})


def original_source(base: str, path: str) -> str:
    existing = git("ls-tree", "--name-only", base, "--", path).strip()
    if not existing:
        return ""
    return git("show", f"{base}:{path}")


def violations(path: str, before: str, after: str) -> list[Violation]:
    reports: list[Violation] = []
    for function in changed_functions(before, after):
        result = code_complexity(function.source, no_ignore=True)
        # The first function is the selected definition, before any nested functions.
        score = result.functions[0].complexity
        if score > LIMIT:
            reports.append(
                Violation(
                    message=(
                        f"{function.name}: cognitive complexity {score} > {LIMIT}; "
                        f"refactor this function to a score of {LIMIT} or less."
                    ),
                    location=Location(Path(path), line=function.line),
                )
            )
    return reports


class ChangedComplexityCheck:
    """Check changed Python functions against the absolute complexity limit."""

    name = "Changed function complexity"

    def evaluate(self, target: Path | None) -> CheckResult:
        """Evaluate changed Python files relative to the selected Git baseline."""
        if target is None:
            return CheckResult(
                (InvalidTarget("check_complexity.py", "Usage: check_complexity.py"),)
            )
        if not target.is_dir():
            return CheckResult(
                (InvalidTarget(str(target), "repository directory does not exist."),)
            )
        os.chdir(target)
        os.chdir(git("rev-parse", "--show-toplevel").strip())
        base = baseline()
        reports: list[Violation] = []
        for path in changed_paths(base):
            with tokenize.open(Path(path)) as stream:
                after = stream.read()
            reports.extend(violations(path, original_source(base, path), after))
        return CheckResult.from_problems(reports)


def main(arguments: list[str]) -> int:
    """Adapt command-line arguments to the shared feedback-check runner."""
    target = Path.cwd() if not arguments else None
    return run_check(ChangedComplexityCheck(), target)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
