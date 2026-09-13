"""Smoke-test the exact artifacts that will be uploaded, outside the checkout."""

import os
import subprocess
import sys
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
    error: OSError | subprocess.CalledProcessError | subprocess.TimeoutExpired,
) -> str:
    """Include captured tool diagnostics when an external command cannot complete."""
    details = getattr(error, "stderr", None) or getattr(error, "stdout", None)
    if isinstance(details, str) and details.strip():
        return f"{error}: {details.strip()}"
    return str(error)


def _run(
    command: list[str], *, cwd: Path, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Run an installation or CLI command without leaking output on success."""
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
    )


class DistributionsCheck:
    """Install and exercise the exact wheel and source archive in a dist target."""

    name = "Distribution artifacts"

    def evaluate(self, target: Path | None) -> CheckResult:
        """Return structured problems found while validating publication artifacts."""
        if target is None:
            return CheckResult(
                (
                    InvalidTarget(
                        "check_distributions.py",
                        "Usage: check_distributions.py [dist]",
                    ),
                )
            )
        if not target.is_dir():
            return CheckResult(
                (InvalidTarget(str(target), "distribution directory does not exist."),)
            )
        try:
            wheels = tuple(target.glob("*.whl"))
            sources = tuple(target.glob("*.tar.gz"))
            problems = self._artifact_count_problems(target, wheels, sources)
            if problems:
                return CheckResult.from_problems(problems)
            return self._evaluate_artifacts(wheels[0], sources[0])
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            return CheckResult((IncompleteCheck(self.name, _execution_message(error)),))

    @staticmethod
    def _artifact_count_problems(
        target: Path, wheels: tuple[Path, ...], sources: tuple[Path, ...]
    ) -> list[Violation]:
        """Report missing or stale duplicate artifacts instead of raising unpack errors."""
        problems = []
        if len(wheels) != 1:
            problems.append(
                Violation(
                    f"Expected exactly one wheel, found {len(wheels)}.",
                    Location(target),
                    rule="wheel-count",
                )
            )
        if len(sources) != 1:
            problems.append(
                Violation(
                    f"Expected exactly one source archive, found {len(sources)}.",
                    Location(target),
                    rule="source-count",
                )
            )
        return problems

    def _evaluate_artifacts(self, wheel: Path, source: Path) -> CheckResult:
        """Exercise each exact artifact in its own temporary environment."""
        problems = []
        for artifact in (wheel, source):
            try:
                with TemporaryDirectory(prefix="smith-distribution-") as directory:
                    problems.extend(
                        self._evaluate_artifact(artifact.resolve(), Path(directory)).problems
                    )
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                return CheckResult(
                    (IncompleteCheck(self.name, f"{artifact.name}: {_execution_message(error)}"),)
                )
        return CheckResult.from_problems(problems)

    @staticmethod
    def _evaluate_artifact(artifact: Path, root: Path) -> CheckResult:
        """Install one artifact and exercise the installed CLI without local imports."""
        environment = root / "venv"
        _run(["uv", "venv", str(environment)], cwd=root)
        binaries = environment / ("Scripts" if os.name == "nt" else "bin")
        python = binaries / ("python.exe" if os.name == "nt" else "python")
        cli = binaries / ("agent-smith.exe" if os.name == "nt" else "agent-smith")
        _run(["uv", "pip", "install", "--python", str(python), str(artifact)], cwd=root)
        _run([str(cli), "--help"], cwd=root, timeout=10)
        _run([str(cli), "--version"], cwd=root, timeout=10)
        (root / "README.md").write_text("# Example\n\nAn overview.\n\n## Usage\n", encoding="utf-8")
        _run([str(cli)], cwd=root, timeout=10)
        generated = (root / "AGENTS.md").read_text(encoding="utf-8")
        if "## Overview\n\nAn overview." not in generated:
            return CheckResult(
                (
                    Violation(
                        f"Generation failed for {artifact.name}.",
                        Location(root / "AGENTS.md"),
                        rule="generated-document",
                    ),
                )
            )
        return CheckResult()


def main(arguments: list[str]) -> int:
    """Evaluate the distribution target through the shared feedback runner."""
    target = (
        Path(arguments[0])
        if len(arguments) == 1
        else Path.cwd() / "dist"
        if not arguments
        else None
    )
    return run_check(DistributionsCheck(), target)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
