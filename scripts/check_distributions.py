"""Smoke-test the exact artifacts that will be uploaded, outside the checkout."""

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


def check_artifact(artifact: Path, root: Path) -> None:
    """Install one artifact and exercise the installed CLI without local imports."""
    environment = root / "venv"
    subprocess.run(["uv", "venv", str(environment)], check=True)
    binaries = environment / ("Scripts" if os.name == "nt" else "bin")
    python = binaries / ("python.exe" if os.name == "nt" else "python")
    cli = binaries / ("agent-smith.exe" if os.name == "nt" else "agent-smith")
    subprocess.run(["uv", "pip", "install", "--python", str(python), str(artifact)], check=True)
    subprocess.run([str(cli), "--help"], check=True, cwd=root, capture_output=True)
    subprocess.run([str(cli), "--version"], check=True, cwd=root)
    (root / "README.md").write_text("# Example\n\nAn overview.\n\n## Usage\n", encoding="utf-8")
    subprocess.run([str(cli)], check=True, cwd=root)
    if "## Overview\n\nAn overview." not in (root / "AGENTS.md").read_text(encoding="utf-8"):
        raise RuntimeError(f"Generation failed for {artifact.name}")


def verify() -> None:
    """Require exactly one wheel and source archive; never silently test old builds."""
    (wheel,) = Path("dist").glob("*.whl")
    (source,) = Path("dist").glob("*.tar.gz")
    for artifact in (wheel, source):
        with TemporaryDirectory(prefix="smith-distribution-") as directory:
            check_artifact(artifact.resolve(), Path(directory))
    print("Wheel and source distribution verified.")


if __name__ == "__main__":
    verify()
