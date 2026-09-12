"""The pyramid report uses real pytest collection without executing test bodies."""

import subprocess
import sys
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / "scripts" / "tests_pyramid.py"


def test_pyramid_counts_parametrized_cases_without_running_tests(tmp_path: Path) -> None:
    # Given a test tree with two parametrized unit cases and one case at each other level.
    for level in ("unit", "integration", "functional"):
        directory = tmp_path / "tests" / level
        directory.mkdir(parents=True)
        decorator = (
            'import pytest\n@pytest.mark.parametrize("value", [1, 2])\n' if level == "unit" else ""
        )
        argument = "value" if level == "unit" else ""
        (directory / f"test_{level}.py").write_text(
            decorator + f"def test_example({argument}):\n    raise RuntimeError('must not run')\n"
        )
    # When the report collects that tree in a separate process.
    result = subprocess.run(
        [sys.executable, str(REPORT)], cwd=tmp_path, capture_output=True, text=True
    )
    # Then every collected case is counted and the deliberately failing bodies never run.
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[1:] == [
        "Unit             2   50.0%",
        "Integration      1   25.0%",
        "Functional       1   25.0%",
        "Total            4  100.0%",
    ]


def test_pyramid_surfaces_collection_errors(tmp_path: Path) -> None:
    # Given a test module that cannot be imported.
    directory = tmp_path / "tests"
    directory.mkdir()
    (directory / "test_broken.py").write_text("raise RuntimeError('collection is broken')\n")
    # When the report attempts to collect it.
    result = subprocess.run(
        [sys.executable, str(REPORT)], cwd=tmp_path, capture_output=True, text=True
    )
    # Then failure is actionable rather than reporting a misleading zero count.
    assert result.returncode == 1
    assert "collection is broken" in result.stdout + result.stderr
    assert "Total" not in result.stdout


def test_pyramid_handles_an_empty_test_tree(tmp_path: Path) -> None:
    # Given an empty tests directory.
    (tmp_path / "tests").mkdir()
    # When pytest collects no cases.
    result = subprocess.run(
        [sys.executable, str(REPORT)], cwd=tmp_path, capture_output=True, text=True
    )
    # Then zero counts have zero percentages without a division error.
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[1:] == [
        "Unit             0    0.0%",
        "Integration      0    0.0%",
        "Functional       0    0.0%",
        "Total            0    0.0%",
    ]
