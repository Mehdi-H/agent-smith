"""Drive the demo export checker with injected probes and real tape files."""

from pathlib import Path

from scripts.checks.core import IncompleteCheck, Violation
from scripts.checks.demo import (
    DEFAULT_ARTIFACTS,
    DemoCheck,
    DemoTarget,
    Export,
    probe_export,
    tape_geometry,
)


class FakeProbe:
    """Return predecoded exports keyed by artifact file name."""

    def __init__(self, exports: dict[str, Export]) -> None:
        self._exports = exports

    def __call__(self, path: Path) -> Export | IncompleteCheck:
        return self._exports[path.name]


def write_tape(tmp_path: Path, width: str = "1600", height: str = "1000") -> Path:
    """Write a minimal tape declaring the given geometry."""
    path = tmp_path / "agent-smith.tape"
    path.write_text(f"Set Width {width}\nSet Height {height}\n", encoding="utf-8")
    return path


def test_tape_geometry_reads_declared_size(tmp_path: Path) -> None:
    # Given a tape declaring a width and height.
    tape = write_tape(tmp_path, "1600", "1000")
    # When the geometry is parsed from it.
    geometry = tape_geometry(tape)
    # Then the declared dimensions are returned as integers.
    assert geometry == (1600, 1000)


def test_tape_geometry_rejects_unreadable_tape(tmp_path: Path) -> None:
    # Given a tape path that does not exist.
    tape = tmp_path / "missing.tape"
    # When the geometry is parsed from it.
    geometry = tape_geometry(tape)
    # Then the parse fails closed instead of returning a default.
    assert geometry is None


def test_matching_exports_pass(tmp_path: Path) -> None:
    # Given two exports with the tape geometry and an identical frame count.
    gif = tmp_path / "agent-smith.gif"
    mp4 = tmp_path / "agent-smith.mp4"
    exports = {
        gif.name: Export(gif, 1600, 1000, 542),
        mp4.name: Export(mp4, 1600, 1000, 542),
    }
    # When the check evaluates them.
    result = DemoCheck(FakeProbe(exports)).evaluate(DemoTarget(write_tape(tmp_path), (gif, mp4)))
    # Then the contract reports success silently.
    assert result.problems == ()
    assert result.exit_code == 0


def test_wrong_geometry_is_reported(tmp_path: Path) -> None:
    # Given an export whose decoded size does not match the tape.
    gif = tmp_path / "agent-smith.gif"
    mp4 = tmp_path / "agent-smith.mp4"
    exports = {
        gif.name: Export(gif, 800, 600, 542),
        mp4.name: Export(mp4, 1600, 1000, 542),
    }
    # When the check evaluates the mismatched export.
    result = DemoCheck(FakeProbe(exports)).evaluate(DemoTarget(write_tape(tmp_path), (gif, mp4)))
    # Then one geometry violation points at the offending export.
    assert [problem.rule for problem in result.problems if isinstance(problem, Violation)] == [
        "geometry"
    ]
    location = next(p.location for p in result.problems if isinstance(p, Violation))
    assert location is not None and location.path == gif


def test_static_export_is_reported(tmp_path: Path) -> None:
    # Given an export that decoded to a single frame.
    gif = tmp_path / "agent-smith.gif"
    mp4 = tmp_path / "agent-smith.mp4"
    exports = {
        gif.name: Export(gif, 1600, 1000, 1),
        mp4.name: Export(mp4, 1600, 1000, 1),
    }
    # When the check evaluates the static exports.
    result = DemoCheck(FakeProbe(exports)).evaluate(DemoTarget(write_tape(tmp_path), (gif, mp4)))
    # Then both exports report an animation violation.
    assert [problem.rule for problem in result.problems if isinstance(problem, Violation)] == [
        "animation",
        "animation",
    ]


def test_frame_mismatch_is_reported(tmp_path: Path) -> None:
    # Given two animated exports with different frame counts.
    gif = tmp_path / "agent-smith.gif"
    mp4 = tmp_path / "agent-smith.mp4"
    exports = {
        gif.name: Export(gif, 1600, 1000, 542),
        mp4.name: Export(mp4, 1600, 1000, 200),
    }
    # When the check evaluates the exports.
    result = DemoCheck(FakeProbe(exports)).evaluate(DemoTarget(write_tape(tmp_path), (gif, mp4)))
    # Then one mismatch violation points at the divergent export.
    assert [problem.rule for problem in result.problems if isinstance(problem, Violation)] == [
        "mismatch"
    ]


def test_missing_export_is_incomplete(tmp_path: Path) -> None:
    # Given an export path that does not exist on disk.
    missing = tmp_path / "agent-smith.gif"
    # When the real ffprobe adapter inspects it.
    probed = probe_export(missing)
    # Then the check fails closed with guidance instead of probing.
    assert isinstance(probed, IncompleteCheck)
    assert "run just demo" in probed.message


def test_default_artifacts_only_require_the_versioned_gif() -> None:
    # Given the default target used by the documented demo-check recipe.
    default = DEFAULT_ARTIFACTS
    # When a fresh clone has only the committed GIF.
    # Then the Git-ignored MP4 is not part of the default contract.
    assert default == (Path("docs/demo/agent-smith.gif"),)
