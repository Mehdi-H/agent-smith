"""Exercise the workflow SHA pinning checker with real and misleading YAML."""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.checks.core import InvalidTarget, render
from scripts.checks.sha_pinning import ShaPinningCheck

REPOSITORY = Path(__file__).resolve().parents[2]
CHECKER = "scripts.checks.sha_pinning"
FULL_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"


def run_checker(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the checker module against one path in a separate process."""
    return subprocess.run(
        [sys.executable, "-m", CHECKER, str(target)],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=REPOSITORY,
    )


@pytest.mark.parametrize(
    ("uses", "valid"),
    [
        (f"uses: actions/checkout@{FULL_SHA}", True),
        (f"- uses: jdx/mise-action@{FULL_SHA} # v4", True),
        ('uses: "codecov/codecov-action@' + FULL_SHA + '"', True),
        ("uses: ./.github/workflows/ci.yml", True),
        ("uses: $/.github/workflows/ci.yml", True),
        ("uses: docker://alpine:3.19", True),
        ("uses: actions/checkout@v6", False),
        ("uses: codecov/codecov-action@main", False),
        ("uses: jdx/mise-action", False),
        ("uses: actions/checkout@043fb46d1a93c77aae656e7c1c64a875d1fc6a", False),
    ],
)
def test_pinning_recognizes_only_fully_pinned_externals(
    uses: str, valid: bool, tmp_path: Path
) -> None:
    # Given a workflow whose uses reference is pinned, local, container or mutable.
    workflow = tmp_path / "example.yml"
    workflow.write_text(f"jobs:\n  build:\n    steps:\n      - {uses}\n")
    # When the checker inspects the workflow without executing or fetching anything.
    result = run_checker(workflow)
    # Then only the fully pinned external reference succeeds silently.
    assert result.returncode == (0 if valid else 1)
    assert result.stdout == ""
    if valid:
        assert result.stderr == ""
    else:
        assert f"{workflow}:4:" in result.stderr
        assert "[unpinned-action]" in result.stderr or "[short-sha]" in result.stderr


def test_short_shas_report_a_dedicated_rule(tmp_path: Path) -> None:
    # Given a workflow pinning an Action to a truncated commit SHA.
    workflow = tmp_path / "short.yml"
    workflow.write_text(f"steps:\n  - uses: actions/checkout@{FULL_SHA[:12]}\n")
    # When the checker inspects the workflow.
    result = run_checker(workflow)
    # Then the diagnostic names the short-SHA rule and demands the full length.
    assert result.returncode == 1
    assert f"{workflow}:2: [short-sha]" in result.stderr


def test_run_lines_containing_uses_are_ignored(tmp_path: Path) -> None:
    # Given a workflow mentioning uses only inside a run script.
    workflow = tmp_path / "run.yml"
    workflow.write_text('steps:\n  - run: echo "uses: actions/checkout@v4"\n')
    # When the checker inspects the workflow.
    result = run_checker(workflow)
    # Then no reference is inferred from the script text and the check passes.
    assert result.returncode == 0
    assert result.stderr == ""


def test_multi_line_uses_fail_closed(tmp_path: Path) -> None:
    # Given a workflow whose uses value is a block scalar the checker cannot inspect.
    workflow = tmp_path / "block.yml"
    workflow.write_text("steps:\n  - uses:\n      actions/checkout@v4\n")
    # When the checker inspects the workflow.
    result = run_checker(workflow)
    # Then the check fails with an incomplete-check diagnostic instead of passing.
    assert result.returncode == 1
    assert "cannot inspect this empty or multi-line uses value" in result.stderr


def test_real_workflows_are_fully_pinned() -> None:
    # Given the repository's own checked-in workflows.
    workflows = REPOSITORY / ".github" / "workflows"
    # When the checker evaluates the directory offline.
    result = run_checker(workflows)
    # Then every external Action is already pinned to a full-length commit SHA.
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""


def test_missing_paths_are_invalid_targets(tmp_path: Path) -> None:
    # Given a path that holds no workflow files.
    missing = tmp_path / "nowhere"
    # When the checker evaluates the path through the shared runner.
    result = ShaPinningCheck().evaluate((missing,))
    # Then the runner reports an invalid target instead of silent success.
    assert result.exit_code == 1
    assert len(result.problems) == 1
    assert isinstance(result.problems[0], InvalidTarget)
    assert render(result.problems[0]) == f"{missing}: workflow path does not exist."
