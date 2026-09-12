"""Count pytest-collected cases by test-pyramid directory without running tests."""

import subprocess
import sys


def print_row(label: str, count: int, total: int) -> None:
    percentage = 100 * count / max(total, 1)
    print(f"{label:12} {count:>5}  {percentage:5.1f}%")


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-cov", "tests"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 5):
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return 1
    cases = [
        line for line in result.stdout.splitlines() if "::" in line and line.startswith("tests/")
    ]
    print("Test pyramid (collected cases; tests are not executed)")
    for directory, label in (
        ("unit", "Unit"),
        ("integration", "Integration"),
        ("functional", "Functional"),
    ):
        count = sum(case.startswith(f"tests/{directory}/") for case in cases)
        print_row(label, count, len(cases))
    print_row("Total", len(cases), len(cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
