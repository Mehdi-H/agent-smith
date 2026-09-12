"""Verify the built distribution without importing the checkout or development tools."""

import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory


def verify() -> None:
    """Build through uv, install the resulting wheel, and exercise both entry points."""
    expected_version = version("agent-smith")
    with TemporaryDirectory(prefix="agent-smith-package-") as directory:
        root = Path(directory)
        dist = root / "dist"
        subprocess.run(["uv", "build", "--no-sources", "--out-dir", str(dist)], check=True)
        (wheel,) = dist.glob("*.whl")
        environment = root / "venv"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(environment)], check=True, cwd=root
        )
        binaries = environment / ("Scripts" if os.name == "nt" else "bin")
        python = binaries / ("python.exe" if os.name == "nt" else "python")
        executable = binaries / ("agent-smith.exe" if os.name == "nt" else "agent-smith")
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), str(wheel)],
            check=True,
            cwd=root,
        )
        for command in ([str(executable)], [str(python), "-I", "-m", "agent_smith"]):
            result = subprocess.run(
                [*command, "--version"],
                check=True,
                capture_output=True,
                text=True,
                cwd=root,
                timeout=10,
            )
            if result.stdout != f"agent-smith {expected_version}\n" or result.stderr:
                raise RuntimeError(f"Unexpected version output: {result}")
            subprocess.run([*command, "--help"], check=True, cwd=root, timeout=10)
            (root / "README.md").write_text(
                "# Example\n\nAn overview.\n\n## Usage\n", encoding="utf-8"
            )
            subprocess.run(command, check=True, cwd=root, timeout=10)
            generated = (root / "AGENTS.md").read_text(encoding="utf-8")
            if "## Overview\n\nAn overview." not in generated:
                raise RuntimeError(f"Unexpected generated document: {generated}")
    print("Wheel installation and both entry points verified.")


if __name__ == "__main__":
    verify()
