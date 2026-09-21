"""Verify recorded demo exports match the tape geometry and stay animated."""

import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    Location,
    Problem,
    Violation,
    run_check,
)

NAME = "Terminal demo"
TAPE = Path("docs/demo/agent-smith.tape")
# Only the GIF is versioned; the MP4 is Git-ignored and checked at record time.
DEFAULT_ARTIFACTS = (Path("docs/demo/agent-smith.gif"),)


@dataclass(frozen=True, slots=True)
class DemoTarget:
    """The tape that declares the geometry and the exports to verify."""

    tape: Path
    artifacts: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class Export:
    """One export's decoded width, height and frame count."""

    path: Path
    width: int
    height: int
    frames: int


Probe: TypeAlias = Callable[[Path], Export | IncompleteCheck]


def tape_geometry(tape: Path) -> tuple[int, int] | None:
    """Return the width and height declared by the tape, or None when unreadable."""
    try:
        lines = tape.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    width = ""
    height = ""
    for line in lines:
        if line.startswith("Set Width "):
            width = line.removeprefix("Set Width ").strip()
        elif line.startswith("Set Height "):
            height = line.removeprefix("Set Height ").strip()
    if width.isdigit() and height.isdigit():
        return int(width), int(height)
    return None


def probe_export(path: Path) -> Export | IncompleteCheck:
    """Decode one export with ffprobe without raising on tool or format failures."""
    if not path.is_file():
        return IncompleteCheck(NAME, f"{path}: export does not exist; run just demo.")
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,nb_frames",
        "-of",
        "csv=p=0",
        str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        return IncompleteCheck(NAME, f"{path}: cannot run ffprobe: {error}")
    if result.returncode != 0:
        return IncompleteCheck(NAME, f"{path}: ffprobe failed: {result.stderr.strip()}")
    fields = result.stdout.strip().split(",")
    if len(fields) != 3 or not all(field.isdigit() for field in fields):
        return IncompleteCheck(
            NAME, f"{path}: unexpected ffprobe output: {result.stdout.strip()!r}"
        )
    width, height, frames = (int(field) for field in fields)
    return Export(path, width, height, frames)


class DemoCheck:
    """Verify recorded exports carry the tape geometry and stay animated."""

    name = NAME

    def __init__(self, probe: Probe = probe_export) -> None:
        self._probe = probe

    def evaluate(self, target: DemoTarget) -> CheckResult:
        """Probe every export and report geometry, animation and mismatch problems."""
        geometry = tape_geometry(target.tape)
        if geometry is None:
            return CheckResult(
                (
                    IncompleteCheck(
                        self.name,
                        f"{target.tape}: cannot read the Set Width and Set Height lines.",
                    ),
                )
            )
        problems: list[Problem] = []
        exports: list[Export] = []
        for artifact in target.artifacts:
            probed = self._probe(artifact)
            if isinstance(probed, IncompleteCheck):
                problems.append(probed)
            else:
                exports.append(probed)
        problems.extend(render_problems(geometry, exports))
        return CheckResult.from_problems(problems)


def render_problems(geometry: tuple[int, int], exports: list[Export]) -> list[Problem]:
    """Compare probed exports against the expected geometry and each other."""
    problems: list[Problem] = []
    reference: int | None = None
    for export in exports:
        if (export.width, export.height) != geometry:
            problems.append(
                Violation(
                    f"export geometry is {export.width}x{export.height}, "
                    f"expected {geometry[0]}x{geometry[1]}; re-record with just demo.",
                    Location(export.path),
                    rule="geometry",
                )
            )
        if export.frames <= 1:
            problems.append(
                Violation(
                    f"export has {export.frames} frame(s) and is not animated; "
                    "re-record with just demo.",
                    Location(export.path),
                    rule="animation",
                )
            )
        if reference is None:
            reference = export.frames
        elif export.frames != reference:
            problems.append(
                Violation(
                    f"export has {export.frames} frames but another has {reference}; "
                    "re-record with just demo.",
                    Location(export.path),
                    rule="mismatch",
                )
            )
    return problems


def main(arguments: list[str]) -> int:
    """Adapt optional export paths to the shared feedback-check runner."""
    artifacts = tuple(Path(argument) for argument in arguments) or DEFAULT_ARTIFACTS
    return run_check(DemoCheck(), DemoTarget(TAPE, artifacts))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
