"""The complexity gate inspects real Git changes and real Complexipy scores."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def run_git(directory: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=directory, text=True).strip()


def function_source(branches: int, result: int = 1) -> str:
    return "def example(x):\n" + "".join(
        f"    if x == {index}:\n        return {result}\n" for index in range(branches)
    )


@pytest.mark.parametrize(
    ("before", "after", "status"),
    [(9, 9, 1), (10, 9, 1), (9, 8, 0), (8, 8, 0)],
)
def test_changed_functions_must_meet_absolute_limit(
    tmp_path: Path, before: int, after: int, status: int
) -> None:
    # Given an existing function in a real repository and a selected baseline.
    run_git(tmp_path, "init", "-b", "main")
    source = tmp_path / "example.py"
    source.write_text(function_source(before))
    run_git(tmp_path, "add", ".")
    run_git(
        tmp_path,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "-m",
        "base",
    )
    base = run_git(tmp_path, "rev-parse", "HEAD")
    source.write_text(function_source(after, result=2))
    # When the changed function is checked, even if its score stayed equal or decreased.
    result = subprocess.run(
        [sys.executable, "-m", "scripts.check_complexity"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "COMPLEXITY_BASE": base, "PYTHONPATH": str(ROOT)},
        check=False,
    )
    # Then the absolute limit applies and failures identify the function and line.
    assert result.returncode == status
    assert result.stdout == ""
    assert ("example.py:1: example" in result.stderr) == bool(status)


def test_unchanged_functions_are_ignored_and_new_functions_are_checked(tmp_path: Path) -> None:
    # Given an over-limit function moved down by an unrelated module-level addition.
    run_git(tmp_path, "init", "-b", "main")
    source = tmp_path / "example.py"
    source.write_text(function_source(9))
    run_git(tmp_path, "add", ".")
    run_git(
        tmp_path,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "-m",
        "base",
    )
    base = run_git(tmp_path, "rev-parse", "HEAD")
    source.write_text("VALUE = 1\n\n" + function_source(9))
    environment = {**os.environ, "COMPLEXITY_BASE": base, "PYTHONPATH": str(ROOT)}
    # When only module content changes, then an untracked function is introduced.
    unchanged = subprocess.run(
        [sys.executable, "-m", "scripts.check_complexity"],
        cwd=tmp_path,
        capture_output=True,
        env=environment,
    )
    (tmp_path / "new.py").write_text(function_source(9))
    added = subprocess.run(
        [sys.executable, "-m", "scripts.check_complexity"],
        cwd=tmp_path,
        capture_output=True,
        env=environment,
    )
    # Then existing debt is ignored but a new function above eight fails.
    assert unchanged.returncode == 0
    assert unchanged.stdout == unchanged.stderr == b""
    assert added.returncode == 1
    assert b"new.py:1: example" in added.stderr
    assert b"example.py" not in added.stderr


@pytest.mark.parametrize("kind", ["method", "async", "duplicate"])
def test_committed_branch_definitions_are_checked(tmp_path: Path, kind: str) -> None:
    # Given a feature branch with a committed complex definition and a local main baseline.
    run_git(tmp_path, "init", "-b", "main")
    run_git(
        tmp_path,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "--allow-empty",
        "-m",
        "base",
    )
    run_git(tmp_path, "checkout", "-b", "feature")
    definitions = {
        "method": "class Example:\n"
        + "".join("    " + line + "\n" for line in function_source(9).splitlines()),
        "async": "async " + function_source(9),
        "duplicate": function_source(9) + "\ndef example(x):\n    return x\n",
    }
    (tmp_path / "example.py").write_text(definitions[kind])
    run_git(tmp_path, "add", ".")
    run_git(
        tmp_path,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.org",
        "commit",
        "-m",
        "feature",
    )
    # When the default branch comparison runs with no explicit baseline.
    environment = {key: value for key, value in os.environ.items() if key != "COMPLEXITY_BASE"}
    environment["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-m", "scripts.check_complexity"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=environment,
    )
    # Then committed methods, async functions and repeated definitions cannot evade the limit.
    assert result.returncode == 1
    assert "example" in result.stderr
    assert "9 > 8" in result.stderr
