"""Reject textual uses of patching APIs anywhere in Python test sources."""

import re
import sys
from pathlib import Path

from scripts.checks.core import CheckResult, InvalidTarget, Location, Violation, run_check

FORBIDDEN = re.compile(r"\b(?:monkey[ _-]?patch\w*|patch(?:\b|_\w*))", re.IGNORECASE)


class TestDoublesCheck:
    """Reject textual uses of patching APIs in Python test sources."""

    name = "Test doubles"

    def evaluate(self, target: Path | None) -> CheckResult:
        """Inspect a test directory and return one typed problem per forbidden line."""
        if target is None:
            return CheckResult(
                (
                    InvalidTarget(
                        "check_test_doubles.py",
                        "Usage: check_test_doubles.py [test-directory]",
                    ),
                )
            )
        if not target.is_dir():
            return CheckResult.from_problems(
                [InvalidTarget(str(target), "Test directory does not exist.")]
            )

        problems: list[Violation] = []
        for path in sorted(target.rglob("*.py")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                # A literal semantic-version CLI flag is not a replacement API.
                inspected = re.sub(r"([\"'])--patch\1", "", line)
                if FORBIDDEN.search(inspected):
                    problems.append(
                        Violation(
                            message=f"forbidden test replacement: {line.strip()}",
                            location=Location(path, line=number),
                        )
                    )
        return CheckResult.from_problems(problems)


def main(arguments: list[str]) -> int:
    """Adapt command-line arguments to the shared feedback-check runner."""
    directory = (
        Path(arguments[0]) if len(arguments) == 1 else Path("tests") if not arguments else None
    )
    return run_check(TestDoublesCheck(), directory)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
