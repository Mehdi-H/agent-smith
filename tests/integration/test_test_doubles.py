"""The test-double policy gives source locations without executing test code."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(("fixture", "status"), [("allowed", 0), ("forbidden", 1)])
def test_test_double_policy_reports_source_lines(tmp_path: Path, fixture: str, status: int) -> None:
    # Given representative test source copied from an inert policy fixture.
    content = (ROOT / "scripts" / "fixtures" / "test-doubles" / f"{fixture}.txt").read_text()
    source = tmp_path / "test_example.py"
    source.write_text(content)
    # When the policy inspects the source without importing it.
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_test_doubles.py"), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    # Then forbidden examples have a diagnostic for each source line; allowed ones are silent.
    assert result.returncode == status
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == (len(content.splitlines()) if status else 0)
    if status:
        assert f"{source}:1:" in result.stderr
