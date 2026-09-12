"""Exercise the shell feedback with an injected GitHub CLI executable."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "workflow-warnings.sh"
FAKE_GH = """#!/bin/sh
printf '%s\n' "$*" >> "$REQUEST_LOG"
case "$*" in
  *'status=success'*) printf '%s' "$CANDIDATES" ;;
  'repo view '*) echo owner/repo ;;
  *annotations*) printf '%s' "$FINDINGS" ;;
  *'/jobs?'*) printf '%s' "$CHECKS" ;;
  'api '*) printf '%s' "$RUN_STATE"; exit "$API_STATUS" ;;
  *) exit 99 ;;
esac
"""


@pytest.mark.parametrize(
    ("run_id", "state", "checks", "findings", "api_status", "expected"),
    [
        ("42", "completed\tsuccess\t1", "https://api.github.com/checks/1", "", "0", 0),
        (
            "42",
            "completed\tsuccess\t1",
            "https://api.github.com/checks/1",
            "warning: deprecated",
            "0",
            1,
        ),
        ("42", "in_progress\t\t1", "", "", "0", 1),
        ("42", "completed\tfailure\t1", "https://api.github.com/checks/1", "", "0", 1),
        ("42", "completed\tsuccess\t1", "", "", "0", 1),
        ("", "", "", "", "0", 1),
        ("42", "", "", "", "1", 1),
    ],
)
def test_workflow_warning_feedback(
    tmp_path: Path,
    run_id: str,
    state: str,
    checks: str,
    findings: str,
    api_status: str,
    expected: int,
) -> None:
    # Given an injected executable serving GitHub responses without patching APIs.
    gh = tmp_path / "gh"
    gh.write_text(FAKE_GH)
    gh.chmod(0o755)
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}")
    env.update(
        CANDIDATES=f"100\t{run_id}" if run_id else "",
        REQUEST_LOG=str(tmp_path / "requests"),
        RUN_STATE=state,
        CHECKS=checks,
        FINDINGS=findings,
        API_STATUS=api_status,
    )
    # When the feedback inspects the latest main run.
    result = subprocess.run(
        ["sh", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=10
    )
    # Then only a successful run without findings returns silent success.
    assert result.returncode == expected
    assert result.stdout == ""
    assert findings in result.stderr


def test_latest_success_is_selected_for_every_workflow(tmp_path: Path) -> None:
    # Given unordered successful runs from two workflows through an injected CLI.
    gh = tmp_path / "gh"
    gh.write_text(FAKE_GH)
    gh.chmod(0o755)
    log = tmp_path / "requests"
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}")
    env.update(
        CANDIDATES="100\t42\n200\t44\n100\t41\n200\t43\n",
        REQUEST_LOG=str(log),
        RUN_STATE="completed\tsuccess\t1",
        CHECKS="https://api.github.com/checks/1",
        FINDINGS="",
        API_STATUS="0",
    )
    # When the feedback groups candidates and checks their annotations.
    result = subprocess.run(
        ["sh", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=10
    )
    # Then only the newest success per workflow is inspected, with pagination.
    requests = log.read_text()
    assert result.returncode == 0
    assert "runs/42 " in requests and "runs/44 " in requests
    assert "runs/41 " not in requests and "runs/43 " not in requests
    assert "--paginate" in requests
