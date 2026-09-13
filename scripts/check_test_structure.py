"""Check Given/When/Then comments in conventional pytest test functions."""

import ast
import io
import re
import sys
import tokenize
from pathlib import Path
from typing import TypeAlias

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    InvalidTarget,
    Location,
    Violation,
    run_check,
)

MARKER = re.compile(r"#\s*(given|when|then)\b", re.IGNORECASE)
TestFunction: TypeAlias = ast.FunctionDef | ast.AsyncFunctionDef
Target: TypeAlias = Path | tuple[Path, ...]


def test_function(node: ast.AST) -> TestFunction | None:
    """Return a conventionally named test function or method."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
        return node
    return None


def named_tests(nodes: list[ast.stmt], prefix: str = "") -> list[tuple[str, TestFunction]]:
    """Name test functions found directly in one syntax-tree body."""
    found = []
    for node in nodes:
        function = test_function(node)
        if function is not None:
            found.append((f"{prefix}{function.name}", function))
    return found


def test_functions(tree: ast.Module) -> list[tuple[str, TestFunction]]:
    """Find module tests and methods of Test classes, excluding nested helpers."""
    found = named_tests(tree.body)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            found.extend(named_tests(node.body, f"{node.name}."))
    return found


def parse_tests(path: Path) -> tuple[ast.Module, list[tokenize.TokenInfo]]:
    """Parse a test module and preserve its actual comment tokens."""
    with tokenize.open(path) as source:
        text = source.read()
    tree = ast.parse(text, filename=str(path))
    comments = [
        token
        for token in tokenize.generate_tokens(io.StringIO(text).readline)
        if token.type == tokenize.COMMENT
    ]
    return tree, comments


def structural_marker(token: tokenize.TokenInfo, function: TestFunction) -> str | None:
    """Return a body-level Given/When/Then marker when the token is structural."""
    line, column = token.start
    if not (function.lineno < line <= (function.end_lineno or function.lineno)):
        return None
    if column != function.body[0].col_offset or token.line[:column].strip():
        return None
    match = MARKER.match(token.string)
    return match.group(1).lower() if match else None


def function_markers(function: TestFunction, comments: list[tokenize.TokenInfo]) -> list[str]:
    """Collect structural markers for one test function."""
    found = []
    for token in comments:
        marker = structural_marker(token, function)
        if marker is not None:
            found.append(marker)
    return found


def file_violations(path: Path) -> list[Violation | IncompleteCheck]:
    """Recognize actual standalone comments, never text inside strings."""
    try:
        tree, comments = parse_tests(path)
    except (OSError, SyntaxError, UnicodeError, tokenize.TokenError) as error:
        return [IncompleteCheck(TestStructureCheck.name, f"{path}: cannot inspect tests: {error}")]

    violations = []
    for name, function in test_functions(tree):
        markers = function_markers(function, comments)
        if markers != ["given", "when", "then"]:
            actual = ", ".join(markers) or "none"
            violations.append(
                Violation(
                    f"{name}: expected standalone # Given, # When, # Then comments once each, "
                    f"in order, at test-body indentation; found {actual}.",
                    Location(path, line=function.lineno),
                )
            )
    return violations


def discover(path: Path) -> tuple[set[Path], list[InvalidTarget]]:
    """Discover conventional test files at one supplied path."""
    if path.is_file():
        return {path}, []
    if path.is_dir():
        return set(path.rglob("test_*.py")) | set(path.rglob("*_test.py")), []
    return set(), [InvalidTarget(str(path), "test path does not exist.")]


class TestStructureCheck:
    """Evaluate Given/When/Then structure in conventionally named test files."""

    name = "Test structure check"

    def evaluate(self, target: Target) -> CheckResult:
        """Discover test files and return typed structural problems."""
        paths = (target,) if isinstance(target, Path) else target
        files: set[Path] = set()
        problems: list[Violation | InvalidTarget | IncompleteCheck] = []
        for path in paths:
            discovered, discovery_problems = discover(path)
            files.update(discovered)
            problems.extend(discovery_problems)
        if not files:
            problems.append(
                InvalidTarget(
                    ", ".join(str(path) for path in paths) or "tests",
                    "No Python test files found; check the supplied paths.",
                )
            )
        for path in sorted(files):
            problems.extend(file_violations(path))
        return CheckResult.from_problems(problems)


def main(arguments: list[str]) -> int:
    """Adapt command-line paths to the shared feedback-check runner."""
    paths = tuple(Path(argument) for argument in arguments) or (Path("tests"),)
    return run_check(TestStructureCheck(), paths)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
