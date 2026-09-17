"""Exercise the distribution content audit against real built artifacts."""

import base64
import hashlib
import io
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.check_dist_audit import audit_sdist, audit_wheel, load_expectation
from scripts.checks.core import Violation

ROOT = Path(__file__).resolve().parents[2]

# The release contract the audits verify comes from the real project metadata.
EXPECTATION = load_expectation(ROOT / "pyproject.toml")


def _sha256_urlsafe(payload: bytes) -> str:
    """Return the RECORD style url-safe base64 digest without padding."""
    digest = hashlib.sha256(payload).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _record_bytes(members: dict[str, bytes], record_name: str) -> bytes:
    """Regenerate a RECORD from sorted member rows plus the conventional self row."""
    lines = [
        f"{name},sha256={_sha256_urlsafe(payload)},{len(payload)}"
        for name, payload in sorted(members.items())
        if name != record_name
    ]
    lines.append(f"{record_name},,")
    return ("\n".join(lines) + "\n").encode()


def _read_wheel(wheel: Path) -> dict[str, bytes]:
    """Return the file members of a wheel as name-to-payload mappings."""
    with zipfile.ZipFile(wheel) as archive:
        return {
            info.filename: archive.read(info.filename)
            for info in archive.infolist()
            if not info.is_dir()
        }


def _write_wheel(
    members: dict[str, bytes], destination: Path, *, recompute_record: bool = True
) -> None:
    """Write wheel members, optionally regenerating the RECORD member."""
    record_name = None
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            if recompute_record and name.endswith(".dist-info/RECORD"):
                record_name = name
                continue
            archive.writestr(name, payload)
        if record_name is not None:
            archive.writestr(record_name, _record_bytes(members, record_name))


def _corrupt_wheel(
    built: Path,
    tmp_path: Path,
    changes: dict[str, bytes | None],
    *,
    recompute_record: bool = True,
) -> Path:
    """Copy a built wheel with member changes applied into a temporary file."""
    members = _read_wheel(built)
    for name, payload in changes.items():
        if payload is None:
            members.pop(name, None)
        else:
            members[name] = payload
    destination = tmp_path / "tampered.whl"
    _write_wheel(members, destination, recompute_record=recompute_record)
    return destination


def _read_sdist(source: Path) -> dict[str, bytes]:
    """Return the regular-file members of a source archive as payloads."""
    members = {}
    with tarfile.open(source, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            payload = archive.extractfile(member)
            if payload is not None:
                members[member.name] = payload.read()
    return members


def _write_sdist(members: dict[str, bytes], destination: Path) -> None:
    """Write members into a gzip-compressed source archive."""
    with tarfile.open(destination, "w:gz") as archive:
        for name, payload in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))


def _sdist_prefix(members: dict[str, bytes]) -> str:
    """Return the versioned root directory shared by sdist members."""
    return next(iter(members)).split("/", 1)[0]


def _drop_record_row(record: bytes, member: str) -> bytes:
    """Return a RECORD with one member's row removed."""
    kept = [line for line in record.decode().splitlines() if not line.startswith(f"{member},")]
    return ("\n".join(kept) + "\n").encode()


def _rules(violations: list[Violation]) -> set[str]:
    """Return the named rules behind a list of audit violations."""
    return {problem.rule for problem in violations if problem.rule is not None}


def run_audit(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the distribution audit CLI against a target directory."""
    return subprocess.run(
        [sys.executable, "-m", "scripts.check_dist_audit", str(target)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


@pytest.fixture(scope="module")
def built_dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the real project once into a module-scoped distribution directory."""
    dist = tmp_path_factory.mktemp("dist")
    subprocess.run(
        ["uv", "build", "--no-sources", "--out-dir", str(dist)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return dist


def test_built_wheel_passes_audit(built_dist: Path) -> None:
    # Given the freshly built wheel of the real project.
    wheel = next(built_dist.glob("*.whl"))
    # When the wheel audit evaluates its members and metadata.
    violations = audit_wheel(wheel, EXPECTATION)
    # Then no rule fires against the untouched artifact.
    assert violations == []


def test_wheel_missing_file_is_reported(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel whose adapters module is deleted from its payload.
    wheel = _corrupt_wheel(
        next(built_dist.glob("*.whl")), tmp_path, {"agent_smith/adapters/adr.py": None}
    )
    # When the wheel audit compares members against the package allowlist.
    violations = audit_wheel(wheel, EXPECTATION)
    # Then the deleted module is reported as missing.
    assert "missing-file" in _rules(violations)


def test_wheel_unexpected_file_is_reported(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel with a module that has no allowlist entry.
    wheel = _corrupt_wheel(
        next(built_dist.glob("*.whl")),
        tmp_path,
        {"agent_smith/adapters/smuggled.py": b"pass\n"},
    )
    # When the wheel audit reconciles members with the package allowlist.
    violations = audit_wheel(wheel, EXPECTATION)
    # Then the unknown module is reported as unexpected.
    assert "unexpected-file" in _rules(violations)


def test_wheel_bytecode_cache_is_rejected(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel that ships a bytecode cache under the package directory.
    wheel = _corrupt_wheel(
        next(built_dist.glob("*.whl")),
        tmp_path,
        {"agent_smith/__pycache__/cli.cpython-314.pyc": b"cached"},
    )
    # When the audit compares cached members against the version-neutral allowlist.
    violations = audit_wheel(wheel, EXPECTATION)
    # Then bytecode caches never satisfy an allowlist entry.
    assert "unexpected-file" in _rules(violations)


def test_wheel_parent_traversal_is_rejected(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel whose payload escapes the package through parent traversal.
    wheel = _corrupt_wheel(next(built_dist.glob("*.whl")), tmp_path, {"../evil.py": b"import os\n"})
    # When the wheel audit checks every member path for safety.
    violations = audit_wheel(wheel, EXPECTATION)
    # Then traversal is reported even when the member is also unexpected.
    assert "unsafe-path" in _rules(violations)


def test_wheel_record_hash_is_verified(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel whose init module changes without updating its RECORD row.
    wheel = next(built_dist.glob("*.whl"))
    original = _read_wheel(wheel)["agent_smith/__init__.py"]
    swapped = bytes(byte ^ 0x01 for byte in original)
    tampered = _corrupt_wheel(
        wheel, tmp_path, {"agent_smith/__init__.py": swapped}, recompute_record=False
    )
    # When the wheel audit verifies every RECORD hash against the archive.
    violations = audit_wheel(tampered, EXPECTATION)
    # Then a stale RECORD row is reported as an integrity violation.
    assert "record-hash" in _rules(violations)


def test_wheel_record_row_missing_is_reported(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel whose RECORD omits a row for a shipped module.
    wheel = next(built_dist.glob("*.whl"))
    members = _read_wheel(wheel)
    record_name = next(name for name in members if name.endswith(".dist-info/RECORD"))
    edited = _drop_record_row(members[record_name], "agent_smith/__init__.py")
    tampered = _corrupt_wheel(wheel, tmp_path, {record_name: edited}, recompute_record=False)
    # When the wheel audit reconciles RECORD rows with archive members.
    violations = audit_wheel(tampered, EXPECTATION)
    # Then the orphaned member is reported with the RECORD integrity rule.
    assert "record-missing" in _rules(violations)


def test_wheel_metadata_field_is_validated(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel whose METADATA requires a later Python than the project.
    wheel = next(built_dist.glob("*.whl"))
    members = _read_wheel(wheel)
    metadata_name = next(name for name in members if name.endswith(".dist-info/METADATA"))
    edited = members[metadata_name].replace(b"Requires-Python: >=3.11", b"Requires-Python: >=3.12")
    tampered = _corrupt_wheel(wheel, tmp_path, {metadata_name: edited})
    # When the wheel audit validates METADATA fields against the expectation.
    violations = audit_wheel(tampered, EXPECTATION)
    # Then the shifted Python constraint is reported as a metadata field.
    assert "metadata-field" in _rules(violations)


def test_wheel_tag_is_validated(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel whose WHEEL declares an implementation-specific tag.
    wheel = next(built_dist.glob("*.whl"))
    members = _read_wheel(wheel)
    wheel_name = next(name for name in members if name.endswith(".dist-info/WHEEL"))
    edited = members[wheel_name].replace(b"Tag: py3-none-any", b"Tag: py311-none-any")
    tampered = _corrupt_wheel(wheel, tmp_path, {wheel_name: edited})
    # When the wheel audit validates the pure-Python WHEEL metadata.
    violations = audit_wheel(tampered, EXPECTATION)
    # Then the non-portable tag is reported as a wheel metadata violation.
    assert "wheel-metadata" in _rules(violations)


def test_wheel_entry_point_is_validated(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel whose console script points at a missing target.
    wheel = next(built_dist.glob("*.whl"))
    members = _read_wheel(wheel)
    entry_name = next(name for name in members if name.endswith(".dist-info/entry_points.txt"))
    edited = members[entry_name].replace(b"agent_smith.__main__:main", b"agent_smith.__main__:nope")
    tampered = _corrupt_wheel(wheel, tmp_path, {entry_name: edited})
    # When the wheel audit validates the console-script entry point.
    violations = audit_wheel(tampered, EXPECTATION)
    # Then the unresolvable target is reported as an entry point violation.
    assert "entry-point" in _rules(violations)


def test_built_sdist_passes_audit(built_dist: Path) -> None:
    # Given the freshly built source archive of the real project.
    source = next(built_dist.glob("*.tar.gz"))
    # When the source audit evaluates its members and metadata.
    violations = audit_sdist(source, EXPECTATION)
    # Then no rule fires against the untouched archive.
    assert violations == []


def test_sdist_missing_license_is_reported(built_dist: Path, tmp_path: Path) -> None:
    # Given a source archive that drops its declared license member.
    members = _read_sdist(next(built_dist.glob("*.tar.gz")))
    del members[f"{_sdist_prefix(members)}/LICENSE"]
    tampered = tmp_path / "tampered.tar.gz"
    _write_sdist(members, tampered)
    # When the source audit compares members against the package allowlist.
    violations = audit_sdist(tampered, EXPECTATION)
    # Then the licensed file is reported as missing.
    assert "missing-file" in _rules(violations)


def test_sdist_parent_traversal_is_rejected(built_dist: Path, tmp_path: Path) -> None:
    # Given a source archive with a member escaping its versioned root.
    members = _read_sdist(next(built_dist.glob("*.tar.gz")))
    members[f"{_sdist_prefix(members)}/../evil.py"] = b"import os\n"
    tampered = tmp_path / "tampered.tar.gz"
    _write_sdist(members, tampered)
    # When the source audit checks every member path for safety.
    violations = audit_sdist(tampered, EXPECTATION)
    # Then the traversal member is reported without being extracted.
    assert "unsafe-path" in _rules(violations)


def test_sdist_metadata_field_is_validated(built_dist: Path, tmp_path: Path) -> None:
    # Given a source archive whose PKG-INFO names a different project.
    members = _read_sdist(next(built_dist.glob("*.tar.gz")))
    info = f"{_sdist_prefix(members)}/PKG-INFO"
    members[info] = members[info].replace(b"Name: agent-smith-cli", b"Name: something-else")
    tampered = tmp_path / "tampered.tar.gz"
    _write_sdist(members, tampered)
    # When the source audit validates PKG-INFO fields against the expectation.
    violations = audit_sdist(tampered, EXPECTATION)
    # Then the shifted name is reported as a metadata field.
    assert "metadata-field" in _rules(violations)


def test_dist_audit_reports_missing_artifacts(tmp_path: Path) -> None:
    # Given an empty distribution directory.
    result = run_audit(tmp_path)
    # When the audit validates artifact cardinality and archive contents.
    # Then both artifact classes are reported without any stdout output.
    assert result.returncode == 1
    assert result.stdout == ""
    assert "[wheel-count] Expected exactly one wheel, found 0." in result.stderr
    assert "[source-count] Expected exactly one source archive, found 0." in result.stderr


def test_dist_audit_rejects_a_missing_target() -> None:
    # Given an audit target that does not exist.
    target = ROOT / "missing-dist-audit-target"
    result = run_audit(target)
    # When the audit resolves its distribution directory.
    # Then the missing target is reported without writing to stdout.
    assert result.returncode == 1
    assert result.stdout == ""
    assert "distribution directory does not exist." in result.stderr


def test_dist_audit_accepts_the_built_fixture(built_dist: Path) -> None:
    # Given a distribution directory holding the freshly built artifacts.
    # When the audit validates both archives and rebuilds the source.
    result = run_audit(built_dist)
    # Then the untouched fixture passes with no diagnostics at all.
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_dist_audit_rejects_a_divergent_pair(built_dist: Path, tmp_path: Path) -> None:
    # Given a wheel paired with an sdist whose sources disagree in content.
    wheel = next(built_dist.glob("*.whl"))
    source = next(built_dist.glob("*.tar.gz"))
    shutil.copy(wheel, tmp_path / wheel.name)
    members = _read_sdist(source)
    prefix = _sdist_prefix(members)
    init = f"{prefix}/src/agent_smith/__init__.py"
    members[init] = bytes(byte ^ 0x01 for byte in members[init])
    _write_sdist(members, tmp_path / source.name)
    # When the check rebuilds the source and compares metadata inventories.
    result = run_audit(tmp_path)
    # Then the diverging content fails the equivalence contract.
    assert result.returncode == 1
    assert "[equivalent-metadata]" in result.stderr
