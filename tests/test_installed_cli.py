"""Exercise the composition root from outside the checkout."""

import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.parametrize("module", [False, True])
def test_installed_entry_points(module: bool, tmp_path: Path) -> None:
    executable = Path(sys.executable).parent / (
        "agent-smith.exe" if os.name == "nt" else "agent-smith"
    )
    command = [sys.executable, "-m", "agent_smith"] if module else [str(executable)]
    result = subprocess.run(
        [*command, "--version"], cwd=tmp_path, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"agent-smith {version('agent-smith')}\n"
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []
