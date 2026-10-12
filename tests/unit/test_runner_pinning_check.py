"""Evaluate the runner pinning checker against real and misleading workflow files."""

from pathlib import Path

import pytest

from scripts.checks.core import IncompleteCheck, InvalidTarget, Location, Violation, render
from scripts.checks.runner_pinning import RunnerPinningCheck


def write_workflow(tmp_path: Path, runs_on: str) -> Path:
    """Write a two-job workflow whose second job uses the given runs-on value."""
    workflow = tmp_path / "example.yml"
    workflow.write_text(
        "name: Example\n"
        "on: push\n"
        "jobs:\n"
        "  checks:\n"
        "    uses: ./.github/workflows/ci.yml\n"
        "  build:\n"
        f"    runs-on: {runs_on}\n"
        "    steps:\n"
        "      - run: echo build\n",
        encoding="utf-8",
    )
    return workflow


@pytest.mark.parametrize(
    "runs_on",
    [
        "ubuntu-24.04",
        "ubuntu-24.04 # pinned until the Ubuntu 26 migration settles",
        '"macos-15"',
        "windows-2025",
        "[self-hosted, linux, x64]",
    ],
)
def test_explicitly_versioned_runners_pass(runs_on: str, tmp_path: Path) -> None:
    # Given a workflow whose job runs on explicitly versioned or self-hosted labels.
    workflow = write_workflow(tmp_path, runs_on)
    # When the checker evaluates the workflow.
    result = RunnerPinningCheck().evaluate(workflow)
    # Then no problem is reported.
    assert result.problems == ()
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("runs_on", "label"),
    [
        ("ubuntu-latest", "ubuntu-latest"),
        ("'macos-latest'", "macos-latest"),
        ("windows-latest # floats", "windows-latest"),
        ("[self-hosted, Ubuntu-Latest]", "Ubuntu-Latest"),
    ],
)
def test_floating_runner_labels_are_located_at_their_job(
    runs_on: str, label: str, tmp_path: Path
) -> None:
    # Given a workflow whose build job runs on a floating latest label.
    workflow = write_workflow(tmp_path, runs_on)
    # When the checker evaluates the workflow.
    result = RunnerPinningCheck().evaluate(workflow)
    # Then one violation names the label and points at the workflow line and job.
    assert result.exit_code == 1
    assert len(result.problems) == 1
    violation = result.problems[0]
    assert isinstance(violation, Violation)
    assert violation.rule == "floating-runner"
    assert violation.location == Location(workflow, line=7, symbol="build")
    assert f"'{label}'" in violation.message
    assert render(violation).startswith(f"{workflow}:7:build: [floating-runner] ")


def test_every_floating_job_is_reported_with_its_own_id(tmp_path: Path) -> None:
    # Given a workflow with two jobs on floating labels around a pinned one.
    workflow = tmp_path / "jobs.yml"
    workflow.write_text(
        "jobs:\n"
        "  lint:\n"
        "    runs-on: ubuntu-latest\n"
        "  test:\n"
        "    runs-on: ubuntu-24.04\n"
        "    steps:\n"
        "      - name: Show config\n"
        "        run: |\n"
        "          echo 'runner: x'\n"
        "  'release':\n"
        "    runs-on: macos-latest\n",
        encoding="utf-8",
    )
    # When the checker evaluates the workflow.
    result = RunnerPinningCheck().evaluate(workflow)
    # Then each floating job is reported at its own line under its own id.
    locations = [problem.location for problem in result.problems if isinstance(problem, Violation)]
    assert locations == [
        Location(workflow, line=3, symbol="lint"),
        Location(workflow, line=11, symbol="release"),
    ]


def test_runs_on_text_inside_run_scripts_is_ignored(tmp_path: Path) -> None:
    # Given a pinned job whose script only mentions a floating label as text.
    workflow = tmp_path / "script.yml"
    workflow.write_text(
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-24.04\n"
        "    steps:\n"
        '      - run: echo "runs-on: ubuntu-latest"\n',
        encoding="utf-8",
    )
    # When the checker evaluates the workflow.
    result = RunnerPinningCheck().evaluate(workflow)
    # Then no label is inferred from the script text.
    assert result.problems == ()


@pytest.mark.parametrize(
    "runs_on",
    [
        "${{ matrix.os }}",
        "",
        "{ group: large-runners }",
        "[ubuntu-24.04",
        "|",
    ],
)
def test_uninspectable_runs_on_values_fail_closed(runs_on: str, tmp_path: Path) -> None:
    # Given a job whose runs-on value is an expression, block or mapping form.
    workflow = write_workflow(tmp_path, runs_on)
    # When the checker evaluates the workflow.
    result = RunnerPinningCheck().evaluate(workflow)
    # Then the check reports an incomplete evaluation located at the job instead of passing.
    assert result.exit_code == 1
    assert len(result.problems) == 1
    problem = result.problems[0]
    assert isinstance(problem, IncompleteCheck)
    assert problem.message.startswith(f"{workflow}:7:build: cannot inspect this runs-on value")


def test_missing_paths_are_invalid_targets(tmp_path: Path) -> None:
    # Given a path that holds no workflow files.
    missing = tmp_path / "nowhere"
    # When the checker evaluates the path.
    result = RunnerPinningCheck().evaluate((missing,))
    # Then an invalid target is reported instead of silent success.
    assert result.exit_code == 1
    assert len(result.problems) == 1
    assert isinstance(result.problems[0], InvalidTarget)
    assert render(result.problems[0]) == f"{missing}: workflow path does not exist."


def test_unreadable_workflows_fail_closed(tmp_path: Path) -> None:
    # Given a workflow file that is not valid UTF-8.
    workflow = tmp_path / "binary.yml"
    workflow.write_bytes(b"jobs:\n  build:\n    runs-on: \xff\n")
    # When the checker evaluates the file.
    result = RunnerPinningCheck().evaluate(workflow)
    # Then the check reports that it could not inspect the workflow.
    assert len(result.problems) == 1
    problem = result.problems[0]
    assert isinstance(problem, IncompleteCheck)
    assert "cannot inspect workflow" in problem.message
