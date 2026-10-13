"""The feedback collector runs every check and summarizes the failures."""

import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
COLLECTOR = SCRIPTS / "collect-feedback.sh"
WRAPPER = SCRIPTS / "feedback.sh"


def collect(script: str) -> subprocess.CompletedProcess[str]:
    """Run a shell script under the collector; $1 is the feedback wrapper."""
    return subprocess.run(
        ["sh", str(COLLECTOR), "sh", "-c", script, "checks", str(WRAPPER)],
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_every_failing_check_is_reported_with_a_summary() -> None:
    # Given a sequence where the first and last of three checks fail.
    script = (
        'sh "$1" First "Fix first" sh -c "echo first-diagnostic; exit 2"; '
        'sh "$1" Second "Fix second" true; '
        'sh "$1" Third "Fix third" sh -c "echo third-diagnostic >&2; exit 1"'
    )
    # When the collector runs the sequence.
    result = collect(script)
    # Then both failures keep their feedback and the summary names them.
    assert result.returncode == 1
    assert result.stdout == ""
    assert "First failed (native exit 2)" in result.stderr
    assert "first-diagnostic" in result.stderr
    assert "Fix first" in result.stderr
    assert "Third failed (native exit 1)" in result.stderr
    assert "third-diagnostic" in result.stderr
    assert "Fix third" in result.stderr
    assert result.stderr.endswith("Check summary: 2 of 3 checks failed.\n- First\n- Third\n")


def test_passing_checks_are_silent() -> None:
    # Given a sequence of passing checks.
    script = 'sh "$1" First "Fix first" true; sh "$1" Second "Fix second" true'
    # When the collector runs the sequence.
    result = collect(script)
    # Then success keeps the silent zero contract.
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


def test_failing_prerequisite_stops_the_run_once() -> None:
    # Given a step outside the checks that fails before any check runs.
    script = 'echo "environment missing" >&2; exit 3; sh "$1" First "Fix first" false'
    # When the collector runs the sequence.
    result = collect(script)
    # Then the prerequisite is reported once without a cascade of check failures.
    assert result.returncode == 1
    assert result.stderr.startswith("environment missing\n")
    assert "Check run stopped before completion (native exit 3)" in result.stderr
    assert "First" not in result.stderr
    assert "Check summary" not in result.stderr


def test_stopped_run_still_summarizes_checks_that_ran() -> None:
    # Given a failing check followed by a failing step outside the checks.
    script = 'sh "$1" First "Fix first" false; exit 4'
    # When the collector runs the sequence.
    result = collect(script)
    # Then the stop and the earlier failure are both reported.
    assert result.returncode == 1
    assert "Check run stopped before completion (native exit 4)" in result.stderr
    assert result.stderr.endswith("Check summary: 1 of 1 checks failed.\n- First\n")


def test_nested_checks_keep_their_failing_status() -> None:
    # Given a check whose own command runs a failing feedback check.
    script = 'sh "$1" Outer "Fix outer" sh "$1" Inner "Fix inner" false'
    # When the collector runs the sequence.
    result = collect(script)
    # Then the inner failure fails the outer check instead of being collected.
    assert result.returncode == 1
    assert "Outer failed (native exit 1)" in result.stderr
    assert result.stderr.endswith("Check summary: 1 of 1 checks failed.\n- Outer\n")
