"""Check Given/When/Then comments in conventional pytest test functions."""

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

MARKER = re.compile(r"#\s*(given|when|then)\b", re.IGNORECASE)


def test_functions(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Find module tests and methods of Test classes, excluding nested helpers."""
    found = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                found.append((node.name, node))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for method in node.body:
                if isinstance(
                    method, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and method.name.startswith("test_"):
                    found.append((f"{node.name}.{method.name}", method))
    return found


def check_file(path: Path) -> list[str]:
    """Recognize actual standalone comments, never text inside strings."""
    try:
        with tokenize.open(path) as source:
            text = source.read()
        tree = ast.parse(text, filename=str(path))
        comments = [
            token
            for token in tokenize.generate_tokens(io.StringIO(text).readline)
            if token.type == tokenize.COMMENT
        ]
    except (OSError, SyntaxError, UnicodeError, tokenize.TokenError) as error:
        return [f"{path}: cannot inspect tests: {error}"]

    errors = []
    for name, function in test_functions(tree):
        markers = []
        for token in comments:
            line, column = token.start
            if not (function.lineno < line <= (function.end_lineno or function.lineno)):
                continue
            if column != function.body[0].col_offset or token.line[:column].strip():
                continue
            match = MARKER.match(token.string)
            if match:
                markers.append(match.group(1).lower())
        if markers != ["given", "when", "then"]:
            actual = ", ".join(markers) or "none"
            errors.append(
                f"{path}:{function.lineno}: {name}: expected standalone # Given, # When, "
                f"# Then comments once each, in order, at test-body indentation; found {actual}."
            )
    return errors


def main(arguments: list[str]) -> int:
    """Inspect paths, returning a silent 0 or diagnostics and 1."""
    files: set[Path] = set()
    errors = []
    for argument in arguments or ["tests"]:
        path = Path(argument)
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            files.update(path.rglob("test_*.py"))
            files.update(path.rglob("*_test.py"))
        else:
            errors.append(f"{path}: test path does not exist.")
    if not files:
        errors.append("No Python test files found; check the supplied paths.")
    for path in sorted(files):
        errors.extend(check_file(path))
    for error in errors:
        print(error, file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
