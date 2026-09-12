"""The feedback wrapper accepts arbitrary process implementations."""

import subprocess
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parents[1] / "scripts" / "feedback.sh"


@pytest.mark.integration
def test_feedback_success_is_silent() -> None:
    result = subprocess.run(
        ["sh", str(WRAPPER), "Example", "Fix it", "sh", "-c", "echo ok; echo note >&2"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


@pytest.mark.integration
@pytest.mark.parametrize("status", [1, 2, 5, 127])
def test_feedback_normalizes_failure_and_preserves_diagnostics(status: int) -> None:
    result = subprocess.run(
        [
            "sh",
            str(WRAPPER),
            "Example",
            "Fix the example",
            "sh",
            "-c",
            'echo diagnostic; echo details >&2; exit "$1"',
            "example",
            str(status),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert f"native exit {status}" in result.stderr
    assert "diagnostic" in result.stderr
    assert "details" in result.stderr
    assert "Fix the example" in result.stderr


@pytest.mark.integration
def test_feedback_missing_command_does_not_report_success() -> None:
    result = subprocess.run(
        ["sh", str(WRAPPER), "Example", "Install the tool", "agent-smith-nonexistent-tool"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert "Install the tool" in result.stderr
