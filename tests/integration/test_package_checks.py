"""Exercise package and distribution feedback checks through their CLI modules."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_check(module: str, target: Path) -> subprocess.CompletedProcess[str]:
    """Run a repository check module from the repository root."""
    return subprocess.run(
        [sys.executable, "-m", module, str(target)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_package_check_reports_unbuildable_target(tmp_path: Path) -> None:
    # Given an empty directory that cannot be built as a Python project.
    result = run_check("scripts.check_package", tmp_path)
    # When the package check attempts to build and install its target.
    # Then execution failure is reported on stderr with the normalized status one.
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Package installation could not complete" in result.stderr


def test_package_check_rejects_a_missing_repository() -> None:
    # Given a repository target that does not exist.
    target = ROOT / "missing-package-target"
    result = run_check("scripts.check_package", target)
    # When the package check evaluates its target through the shared runner.
    # Then the invalid target is reported without writing to stdout.
    assert result.returncode == 1
    assert result.stdout == ""
    assert f"{target}: repository directory does not exist." in result.stderr


def test_distributions_check_reports_missing_artifacts(tmp_path: Path) -> None:
    # Given an empty distribution directory.
    result = run_check("scripts.check_distributions", tmp_path)
    # When the distribution check looks for the exact publication artifacts.
    # Then both missing artifact classes are actionable and status is one.
    assert result.returncode == 1
    assert result.stdout == ""
    assert "[wheel-count] Expected exactly one wheel, found 0." in result.stderr
    assert "[source-count] Expected exactly one source archive, found 0." in result.stderr


def test_distributions_check_rejects_duplicate_artifacts(tmp_path: Path) -> None:
    # Given duplicate wheel and source archive candidates in a distribution directory.
    for filename in ("one.whl", "two.whl", "one.tar.gz", "two.tar.gz"):
        (tmp_path / filename).write_text("placeholder", encoding="utf-8")
    # When the distribution check validates artifact cardinality.
    result = run_check("scripts.check_distributions", tmp_path)
    # Then stale duplicate artifacts fail closed without attempting installation.
    assert result.returncode == 1
    assert result.stdout == ""
    assert "[wheel-count] Expected exactly one wheel, found 2." in result.stderr
    assert "[source-count] Expected exactly one source archive, found 2." in result.stderr
