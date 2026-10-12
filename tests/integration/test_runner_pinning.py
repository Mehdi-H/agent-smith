"""Run the runner pinning checker as a process against the repository's workflows."""

import subprocess
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
CHECKER = "scripts.checks.runner_pinning"


def run_checker(*targets: Path) -> subprocess.CompletedProcess[str]:
    """Run the checker module from the repository root in a separate process."""
    return subprocess.run(
        [sys.executable, "-m", CHECKER, *map(str, targets)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=REPOSITORY,
    )


def test_real_workflows_are_pinned_by_default() -> None:
    # Given the repository's own checked-in workflows as the default target.
    # When the checker runs without arguments.
    result = run_checker()
    # Then every job runs on an explicitly versioned label and the check is silent.
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""


def test_floating_runners_are_rendered_on_stderr(tmp_path: Path) -> None:
    # Given a workflow whose job runs on a floating latest label.
    workflow = tmp_path / "floating.yml"
    workflow.write_text("jobs:\n  build:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    # When the checker runs against it.
    result = run_checker(workflow)
    # Then the process fails with a diagnostic located at the workflow line and job.
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith(f"{workflow}:3:build: [floating-runner] ")
