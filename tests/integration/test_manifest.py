"""Validate feedback against real just syntax and its native parser."""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check_manifest import ManifestCheck
from scripts.checks.core import InvalidTarget, Violation

REPOSITORY = Path(__file__).resolve().parents[2]
CHECKER = "scripts.check_manifest"


@pytest.mark.parametrize(
    ("prefix", "missing"),
    [
        ('# Explain usage.\n[group("Quality")]\n', []),
        ('[group("Quality")]\n', ["documentation"]),
        ("# Explain usage.\n", ["group"]),
        ("", ["documentation", "group"]),
        ('#   \n[group("Quality")]\n', ["documentation"]),
        ('# Explain usage.\n[group(" ")]\n', ["group"]),
    ],
)
def test_manifest_requires_documentation_and_group(
    prefix: str, missing: list[str], tmp_path: Path
) -> None:
    # Given a justfile with a complete or incomplete recipe declaration.
    manifest = tmp_path / "justfile"
    manifest.write_text(prefix + "sample:\n    exit 99\n")
    # When the checker inspects the manifest without running its recipe.
    result = subprocess.run(
        [sys.executable, "-m", CHECKER, str(manifest)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=REPOSITORY,
    )
    # Then only the complete declaration succeeds, with specific failure guidance.
    assert result.returncode == (1 if missing else 0)
    assert result.stdout == ""
    if missing:
        assert "recipe sample" in result.stderr
        for requirement in missing:
            assert requirement in result.stderr
    else:
        assert result.stderr == ""


def test_manifest_checks_imported_private_recipes(tmp_path: Path) -> None:
    # Given an imported private helper lacking both required declarations.
    manifest = tmp_path / "justfile"
    manifest.write_text('import "helpers.just"\n')
    (tmp_path / "helpers.just").write_text("_helper:\n    exit 99\n")
    # When just parses the import and the checker inspects its recipes.
    result = subprocess.run(
        [sys.executable, "-m", CHECKER, str(manifest)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=REPOSITORY,
    )
    # Then the private helper cannot evade the manifest contract.
    assert result.returncode == 1
    assert "_helper" in result.stderr
    assert "documentation" in result.stderr
    assert "group" in result.stderr


def test_manifest_evaluation_returns_typed_violations(tmp_path: Path) -> None:
    # Given a justfile recipe missing both parts of the manifest contract.
    manifest = tmp_path / "justfile"
    manifest.write_text("sample:\n    exit 99\n")
    # When the domain evaluator inspects the manifest directly.
    result = ManifestCheck().evaluate(manifest)
    # Then each finding has a discriminating type, rule and source location.
    assert [type(problem) for problem in result.problems] == [Violation, Violation]
    for problem, rule in zip(result.problems, ("documentation", "group"), strict=True):
        assert isinstance(problem, Violation)
        assert problem.rule == rule
        assert problem.location is not None
        assert problem.location.path == manifest


def test_manifest_evaluation_rejects_a_missing_target(tmp_path: Path) -> None:
    # Given a path that does not identify a justfile.
    target = tmp_path / "missing.just"
    # When the domain evaluator receives that target.
    result = ManifestCheck().evaluate(target)
    # Then it reports an invalid target instead of claiming a successful check.
    assert result.exit_code == 1
    assert isinstance(result.problems[0], InvalidTarget)
