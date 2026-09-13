"""Verify the built distribution without importing the checkout or development tools."""

import os
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    InvalidTarget,
    Location,
    Violation,
    run_check,
)


def _execution_message(
    error: OSError
    | PackageNotFoundError
    | subprocess.CalledProcessError
    | subprocess.TimeoutExpired,
) -> str:
    """Include captured tool diagnostics when an external command cannot complete."""
    details = getattr(error, "stderr", None) or getattr(error, "stdout", None)
    if isinstance(details, str) and details.strip():
        return f"{error}: {details.strip()}"
    return str(error)


def _run(
    command: list[str], *, cwd: Path, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a build or installed command without leaking output on success."""
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
    )


class PackageCheck:
    """Build, install, and exercise the package from a repository target."""

    name = "Package installation"

    def evaluate(self, target: Path | None) -> CheckResult:
        """Return structured problems found while validating the package build."""
        if target is None:
            return CheckResult(
                (InvalidTarget("check_package.py", "Usage: check_package.py [repository]"),)
            )
        if not target.is_dir():
            return CheckResult(
                (InvalidTarget(str(target), "repository directory does not exist."),)
            )
        try:
            expected_version = version("agent-smith-cli")
            with TemporaryDirectory(prefix="agent-smith-package-") as directory:
                return self._evaluate_build(target, Path(directory), expected_version)
        except (
            OSError,
            PackageNotFoundError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
        ) as error:
            return CheckResult((IncompleteCheck(self.name, _execution_message(error)),))

    def _evaluate_build(self, checkout: Path, root: Path, expected_version: str) -> CheckResult:
        """Build the wheel and check both installed entry points in isolation."""
        dist = root / "dist"
        _run(["uv", "build", "--no-sources", "--out-dir", str(dist)], cwd=checkout)
        wheels = tuple(dist.glob("*.whl"))
        if len(wheels) != 1:
            return CheckResult(
                (
                    Violation(
                        f"Expected exactly one wheel, found {len(wheels)}.",
                        Location(dist),
                        rule="wheel-count",
                    ),
                )
            )
        environment = root / "venv"
        _run(["uv", "venv", "--python", sys.executable, str(environment)], cwd=root)
        binaries = environment / ("Scripts" if os.name == "nt" else "bin")
        python = binaries / ("python.exe" if os.name == "nt" else "python")
        executable = binaries / ("agent-smith.exe" if os.name == "nt" else "agent-smith")
        _run(["uv", "pip", "install", "--python", str(python), str(wheels[0])], cwd=root)
        problems = []
        for command in ([str(executable)], [str(python), "-I", "-m", "agent_smith"]):
            problems.extend(self._evaluate_entry_point(command, root, expected_version).problems)
        return CheckResult.from_problems(problems)

    def _evaluate_entry_point(
        self, command: list[str], root: Path, expected_version: str
    ) -> CheckResult:
        """Exercise one installed entry point and report unexpected output."""
        result = _run([*command, "--version"], cwd=root, timeout=10)
        if result.stdout != f"agent-smith {expected_version}\n" or result.stderr:
            return CheckResult(
                (
                    Violation(
                        f"Unexpected version output from {' '.join(command)}: "
                        f"stdout={result.stdout!r}, stderr={result.stderr!r}",
                        Location(root, symbol="--version"),
                        rule="version-output",
                    ),
                )
            )
        _run([*command, "--help"], cwd=root, timeout=10)
        (root / "README.md").write_text("# Example\n\nAn overview.\n\n## Usage\n", encoding="utf-8")
        _run(command, cwd=root, timeout=10)
        generated = (root / "AGENTS.md").read_text(encoding="utf-8")
        if "## Overview\n\nAn overview." not in generated:
            return CheckResult(
                (
                    Violation(
                        f"Unexpected generated document from {' '.join(command)}.",
                        Location(root / "AGENTS.md"),
                        rule="generated-document",
                    ),
                )
            )
        return CheckResult()


def main(arguments: list[str]) -> int:
    """Evaluate the repository target through the shared feedback runner."""
    target = Path(arguments[0]) if len(arguments) == 1 else Path.cwd() if not arguments else None
    return run_check(PackageCheck(), target)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
