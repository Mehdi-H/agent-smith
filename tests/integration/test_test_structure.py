"""Exercise the structural checker with valid and misleading source text."""

import subprocess
import sys
from pathlib import Path
from textwrap import indent

import pytest

from scripts.check_test_structure import TestStructureCheck
from scripts.checks.core import IncompleteCheck, Location, Violation

REPOSITORY = Path(__file__).resolve().parents[2]
CHECKER = "scripts.check_test_structure"


@pytest.mark.parametrize(
    ("body", "valid"),
    [
        ("# Given input\nx = 1\n# When acting\nx += 1\n# Then verify\nassert x == 2", True),
        ("# given\nx = 1\n# WHEN\nx += 1\n# then\nassert x == 2", True),
        ("# Given\nx = 1\n# Then\nassert x == 1", False),
        ("# When\nx = 1\n# Given\nx += 1\n# Then\nassert x == 2", False),
        ("# Given\n# Given\nx = 1\n# When\nx += 1\n# Then\nassert x == 2", False),
        ('text = """\n# Given\n# When\n# Then\n"""\nassert text', False),
        ("x = 1  # Given\nx += 1  # When\nassert x == 2  # Then", False),
        ("def helper():\n    # Given\n    # When\n    # Then\n    pass\nhelper()", False),
    ],
)
def test_structure_recognizes_only_ordered_standalone_markers(
    body: str, valid: bool, tmp_path: Path
) -> None:
    # Given a source file with genuine or misleading structural markers.
    source = tmp_path / "test_example.py"
    source.write_text("def test_example():\n" + indent(body, "    ") + "\n")
    # When the checker inspects the source without executing it.
    result = subprocess.run(
        [sys.executable, "-m", CHECKER, str(source)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=REPOSITORY,
    )
    # Then only the valid structure succeeds silently; failures locate the test.
    assert result.returncode == (0 if valid else 1)
    assert result.stdout == ""
    if valid:
        assert result.stderr == ""
    else:
        assert f"{source}:1: test_example:" in result.stderr


def test_structure_supports_async_methods(tmp_path: Path) -> None:
    # Given a test class containing an asynchronous test method.
    source = tmp_path / "example_test.py"
    source.write_text(
        "class TestExample:\n"
        "    async def test_result(self):\n"
        "        # Given\n        value = 1\n"
        "        # When\n        result = value + 1\n"
        "        # Then\n        assert result == 2\n"
    )
    # When the checker discovers files in the directory.
    result = subprocess.run(
        [sys.executable, "-m", CHECKER, str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=REPOSITORY,
    )
    # Then the valid asynchronous method passes silently.
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


@pytest.mark.parametrize("content", [None, "def broken(:\n"])
def test_structure_invalid_inputs_fail(content: str | None, tmp_path: Path) -> None:
    # Given a missing or syntactically invalid test file.
    source = tmp_path / "test_broken.py"
    if content is not None:
        source.write_text(content)
    # When the checker tries to inspect it.
    result = subprocess.run(
        [sys.executable, "-m", CHECKER, str(source)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=REPOSITORY,
    )
    # Then the check fails with the offending path instead of silently passing.
    assert result.returncode == 1
    assert str(source) in result.stderr


def test_structure_evaluation_returns_typed_violations(tmp_path: Path) -> None:
    # Given a test file whose structural markers are incomplete.
    source = tmp_path / "test_example.py"
    source.write_text("def test_example():\n    # Given\n    assert True\n")
    # When the domain evaluator inspects the file directly.
    result = TestStructureCheck().evaluate(source)
    # Then it returns a located violation without printing from the domain layer.
    assert len(result.problems) == 1
    problem = result.problems[0]
    assert isinstance(problem, Violation)
    assert problem.location == Location(source, line=1)
    assert "test_example" in problem.message


def test_structure_evaluation_reports_unreadable_source(tmp_path: Path) -> None:
    # Given a test path containing invalid Python source.
    source = tmp_path / "test_broken.py"
    source.write_text("def broken(:\n")
    # When the domain evaluator parses the source directly.
    result = TestStructureCheck().evaluate(source)
    # Then incomplete evaluation is represented explicitly and fails closed.
    assert result.exit_code == 1
    assert isinstance(result.problems[0], IncompleteCheck)
