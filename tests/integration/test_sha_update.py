"""Exercise the Action SHA update checker with injected release doubles."""

import os
import subprocess
import sys
from pathlib import Path

from scripts.checks.core import CheckResult, IncompleteCheck, InvalidTarget, render
from scripts.checks.sha_update import Release, ReleaseLookupError, ShaUpdateCheck

REPOSITORY = Path(__file__).resolve().parents[2]
MODULE = "scripts.checks.sha_update"
OLD_SHA = "c2a87611a18de5b3828c5652fe268e992400cb5c"
NEW_SHA = "1486a78c17be7d1c4bcdc78e107a5b87a21cabcd"


class FakeReleases:
    """Return the injected release, or the injected lookup error, once per repository."""

    def __init__(self, release: Release | None, error: ReleaseLookupError | None = None) -> None:
        self.release = release
        self.error = error
        self.requested: list[str] = []

    def latest(self, repository: str) -> Release:
        self.requested.append(repository)
        if self.error is not None:
            raise self.error
        assert self.release is not None
        return self.release


def write_workflow(tmp_path: Path, uses: str) -> Path:
    """Write one minimal workflow containing the supplied uses line."""
    workflow = tmp_path / "example.yml"
    workflow.write_text(f"jobs:\n  build:\n    steps:\n      - {uses}\n")
    return workflow


def run_cli(target: Path, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run the checker module against one path with the supplied environment."""
    return subprocess.run(
        [sys.executable, "-m", MODULE, str(target)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=REPOSITORY,
        env=environment,
    )


def test_outdated_pin_reports_line_version_and_sha(tmp_path: Path) -> None:
    # Given a workflow pinning an Action to a commit SHA older than the latest release.
    workflow = write_workflow(tmp_path, f"uses: jdx/mise-action@{OLD_SHA} # v4")
    releases = FakeReleases(Release(tag="v5", sha=NEW_SHA))
    # When the check evaluates the workflow through the injected releases.
    result = ShaUpdateCheck(releases).evaluate(workflow)
    # Then the violation carries the line, the latest version and the SHA to write.
    assert result.exit_code == 1
    assert releases.requested == ["jdx/mise-action"]
    rendered = render(result.problems[0])
    assert f"{workflow}:4:" in rendered
    assert "[outdated-pin]" in rendered
    assert f"uses: jdx/mise-action@{OLD_SHA} # v4" in rendered
    assert "v5" in rendered
    assert NEW_SHA in rendered


def test_current_pin_is_silent(tmp_path: Path) -> None:
    # Given a workflow pinned exactly to the latest release commit.
    workflow = write_workflow(tmp_path, f"uses: jdx/mise-action@{NEW_SHA} # v5")
    releases = FakeReleases(Release(tag="v5", sha=NEW_SHA))
    # When the check evaluates the workflow.
    result = ShaUpdateCheck(releases).evaluate(workflow)
    # Then the check succeeds silently.
    assert result == CheckResult()


def test_unpinned_local_and_container_references_need_no_release(tmp_path: Path) -> None:
    # Given a workflow whose references are mutable, local or container images.
    workflow = tmp_path / "example.yml"
    workflow.write_text(
        "steps:\n"
        "  - uses: jdx/mise-action@v4\n"
        "  - uses: ./.github/workflows/ci.yml\n"
        "  - uses: docker://alpine:3.19\n"
    )
    releases = FakeReleases(Release(tag="v5", sha=NEW_SHA))
    # When the check evaluates the workflow.
    result = ShaUpdateCheck(releases).evaluate(workflow)
    # Then no release lookup runs and the check leaves pinning to the pinning check.
    assert result == CheckResult()
    assert releases.requested == []


def test_lookup_failure_fails_closed(tmp_path: Path) -> None:
    # Given a release lookup that cannot complete for the Action repository.
    workflow = write_workflow(tmp_path, f"uses: jdx/mise-action@{OLD_SHA}")
    releases = FakeReleases(release=None, error=ReleaseLookupError("gh api failed: rate limited"))
    # When the check evaluates the workflow.
    result = ShaUpdateCheck(releases).evaluate(workflow)
    # Then the check reports an incomplete evaluation instead of passing.
    assert result.exit_code == 1
    problem = result.problems[0]
    assert isinstance(problem, IncompleteCheck)
    assert "rate limited" in problem.message


def test_missing_paths_are_invalid_targets(tmp_path: Path) -> None:
    # Given a path that holds no workflow files.
    missing = tmp_path / "nowhere"
    releases = FakeReleases(Release(tag="v5", sha=NEW_SHA))
    # When the check evaluates the path through the shared runner.
    result = ShaUpdateCheck(releases).evaluate((missing,))
    # Then the runner reports an invalid target instead of silent success.
    assert result.exit_code == 1
    assert isinstance(result.problems[0], InvalidTarget)
    assert render(result.problems[0]) == f"{missing}: workflow path does not exist."


def test_cli_reports_outdated_pin_through_shared_runner(tmp_path: Path) -> None:
    # Given a workflow whose pinned Action has a newer release served by a fake gh.
    workflow = write_workflow(tmp_path, f"uses: jdx/mise-action@{OLD_SHA} # v4")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        "  *releases/latest*) printf '%s\\n' v5 ;;\n"
        f"  *commits/*) printf '%s\\n' {NEW_SHA} ;;\n"
        "  *) exit 99 ;;\n"
        "esac\n"
    )
    fake_gh.chmod(0o755)
    environment = dict(os.environ, PATH=f"{bin_dir}:{os.environ.get('PATH', '')}")
    # When the checker module runs in a separate process with the fake gh on PATH.
    result = run_cli(workflow, environment)
    # Then the process exits one with the actionable pin diagnostic on stderr.
    assert result.returncode == 1
    assert f"{workflow}:4:" in result.stderr
    assert f"{NEW_SHA} # v5" in result.stderr


def test_cli_passes_silently_when_pins_are_current(tmp_path: Path) -> None:
    # Given a workflow pinned to the latest release served by a fake gh.
    workflow = write_workflow(tmp_path, f"uses: jdx/mise-action@{NEW_SHA} # v5")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        "  *releases/latest*) printf '%s\\n' v5 ;;\n"
        f"  *commits/*) printf '%s\\n' {NEW_SHA} ;;\n"
        "  *) exit 99 ;;\n"
        "esac\n"
    )
    fake_gh.chmod(0o755)
    environment = dict(os.environ, PATH=f"{bin_dir}:{os.environ.get('PATH', '')}")
    # When the checker module runs in a separate process with the fake gh on PATH.
    result = run_cli(workflow, environment)
    # Then the process exits zero silently.
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
