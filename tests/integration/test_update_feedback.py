"""Update feedback preserves actionable changes and never suppresses future VHS releases."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


@pytest.mark.parametrize(("version", "visible"), [("0.12.0", False), ("0.12.1", True)])
def test_mise_excludes_only_the_broken_vhs_release(
    tmp_path: Path, version: str, visible: bool
) -> None:
    # Given a native mise report with a candidate VHS release.
    report = tmp_path / "mise.json"
    report.write_text(json.dumps({"vhs": {"current": "0.11.0", "bump": version}}))
    # When the inventory renders actionable updates.
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "update_report.py"), "mise", str(report)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Then the documented broken version alone is suppressed.
    assert result.returncode == 0
    assert bool(result.stdout) == visible


def test_uv_inventory_keeps_native_dry_run_changes(tmp_path: Path) -> None:
    # Given uv's real dry-run output grammar mixed with progress messages.
    report = tmp_path / "uv.txt"
    report.write_text(
        "Resolved 63 packages in 3ms\nUpdate tool v1 -> v2\nRemove old v1\nAdd new v2\n"
    )
    # When the inventory filters the report.
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "update_report.py"), "uv", str(report)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Then every planned lock change remains actionable.
    assert result.returncode == 0
    assert result.stdout == "Update tool v1 -> v2\nRemove old v1\nAdd new v2\n"


@pytest.mark.parametrize(
    ("output", "native_status", "expected"), [("", "0", 0), ("update", "0", 1), ("error", "2", 1)]
)
def test_combined_feedback_runs_both_inventories(
    tmp_path: Path,
    output: str,
    native_status: str,
    expected: int,
) -> None:
    # Given an injected just executable recording both inventory calls.
    executable = tmp_path / "just"
    executable.write_text(
        '#!/bin/sh\necho "$1" >> "$CALL_LOG"\nprintf "%s" "$REPORT"\nexit "$STATUS"\n'
    )
    executable.chmod(0o755)
    log = tmp_path / "calls"
    env = dict(
        os.environ,
        PATH=f"{tmp_path}:{os.environ['PATH']}",
        CALL_LOG=str(log),
        REPORT=output,
        STATUS=native_status,
    )
    # When the feedback executes the independent inventories.
    result = subprocess.run(
        ["sh", str(SCRIPTS / "updates-check.sh")],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Then neither inventory is skipped, and updates or errors fail the check.
    assert result.returncode == expected
    assert log.read_text().splitlines() == ["updates-mise", "updates-uv"]
    assert result.stdout == ""
    assert output in result.stderr
