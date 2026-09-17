"""Audit built distribution archives against the repository's release contract."""

import base64
import csv
import email.parser
import hashlib
import io
import re
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from email.message import Message
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    InvalidTarget,
    Location,
    Violation,
    run_check,
)

REPOSITORY_ROOT: Path = Path(__file__).resolve().parents[1]
WHEEL_TAG = "py3-none-any"
DIST_INFO_FILES = frozenset({"METADATA", "WHEEL", "RECORD", "entry_points.txt"})
SDIST_BUILD_FILES = frozenset({"PKG-INFO", "pyproject.toml", "pyproject.toml.orig"})
PACKAGE_FILES = frozenset(
    {
        "agent_smith/__init__.py",
        "agent_smith/__main__.py",
        "agent_smith/adapters/__init__.py",
        "agent_smith/adapters/adr.py",
        "agent_smith/adapters/cli.py",
        "agent_smith/adapters/configuration.py",
        "agent_smith/adapters/filesystem.py",
        "agent_smith/adapters/just_help.py",
        "agent_smith/adapters/markdown.py",
        "agent_smith/adapters/mise.py",
        "agent_smith/adapters/overview_images.py",
        "agent_smith/adapters/process.py",
        "agent_smith/application/__init__.py",
        "agent_smith/application/generation.py",
        "agent_smith/application/ports.py",
    }
)


@dataclass(frozen=True, slots=True)
class Expectation:
    """Release contract derived from the repository's pyproject.toml."""

    name: str
    version: str
    requires_python: str
    readme: str
    dependencies: tuple[str, ...]
    urls: tuple[tuple[str, str], ...]
    scripts: tuple[tuple[str, str], ...]
    license_expression: str
    license_files: tuple[str, ...]

    @property
    def distribution(self) -> str:
        """Return the normalized distribution name used in artifact filenames."""
        return re.sub(r"[-_.]+", "_", self.name).lower()


def load_expectation(pyproject: Path) -> Expectation:
    """Derive the release contract from a pyproject.toml metadata section."""
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    project = data["project"]
    license_field = project.get("license", "")
    if isinstance(license_field, str):
        license_expression = license_field
    elif isinstance(license_field, dict):
        license_expression = license_field.get("text", "")
    else:
        license_expression = ""
    return Expectation(
        name=project["name"],
        version=project["version"],
        requires_python=project["requires-python"],
        readme=project["readme"],
        dependencies=tuple(sorted(project.get("dependencies", []))),
        urls=tuple(sorted((label, url) for label, url in project.get("urls", {}).items())),
        scripts=tuple(
            sorted((name, target) for name, target in project.get("scripts", {}).items())
        ),
        license_expression=license_expression,
        license_files=tuple(sorted(project.get("license-files", []))),
    )


def unsafe_reason(member: str) -> str | None:
    """Return why an archive member path is unsafe, or None when it is safe."""
    if PurePosixPath(member).is_absolute() or re.match(r"^[A-Za-z]:", member):
        return "absolute path"
    if ".." in PurePosixPath(member).parts:
        return "parent traversal"
    if "\\" in member:
        return "backslash separator"
    return None


def safety_violations(members: Iterable[str], archive: Path) -> list[Violation]:
    """Report archive members whose paths could escape an extraction root."""
    problems: list[Violation] = []
    for member in members:
        reason = unsafe_reason(member)
        if reason is not None:
            problems.append(
                Violation(
                    f"Unsafe archive member ({reason}).",
                    Location(archive, symbol=member),
                    rule="unsafe-path",
                )
            )
    return problems


def allowlist_violations(
    expected: Collection[str], actual: Collection[str], archive: Path
) -> list[Violation]:
    """Report expected files that are missing and actual files that are unexpected."""
    problems: list[Violation] = []
    for name in sorted(set(expected) - set(actual)):
        problems.append(
            Violation(
                "Missing expected file; rebuild, or fix the allowlist if the "
                "removal is intentional.",
                Location(archive, symbol=name),
                rule="missing-file",
            )
        )
    for name in sorted(set(actual) - set(expected)):
        problems.append(
            Violation(
                "Unexpected file; remove it, or extend the allowlist if the "
                "addition is intentional.",
                Location(archive, symbol=name),
                rule="unexpected-file",
            )
        )
    return problems


def wheel_inventory(expectation: Expectation) -> set[str]:
    """Return the exact wheel member paths the release contract expects."""
    dist_info = f"{expectation.distribution}-{expectation.version}.dist-info"
    inventory = set(PACKAGE_FILES)
    inventory.update(f"{dist_info}/{name}" for name in DIST_INFO_FILES)
    inventory.update(f"{dist_info}/licenses/{name}" for name in expectation.license_files)
    return inventory


def sdist_inventory(expectation: Expectation) -> set[str]:
    """Return the exact sdist member paths the release contract expects."""
    inventory = set(SDIST_BUILD_FILES)
    inventory.add(expectation.readme)
    inventory.update(expectation.license_files)
    inventory.update(f"src/{path}" for path in PACKAGE_FILES)
    return inventory


def parse_metadata(text: str) -> Message:
    """Parse core metadata RFC 822 text into a message object."""
    return email.parser.Parser().parsestr(text)


def _normalized(value: str) -> str:
    """Strip every run of whitespace from a metadata header value."""
    return "".join(value.split())


def _single_value_problem(
    metadata: Message, field: str, expected: str, location: Location
) -> list[Violation]:
    """Report one single-value core metadata field that disagrees with the contract."""
    actual = metadata.get(field, "")
    if actual != expected:
        return [
            Violation(
                f"{field} must be {expected!r}, found {actual!r}.",
                location,
                rule="metadata-field",
            )
        ]
    return []


def _multi_value_problem(
    metadata: Message, field: str, expected: Collection[str], location: Location
) -> list[Violation]:
    """Report one multi-value core metadata field that disagrees with the contract."""
    actual = sorted({_normalized(value) for value in metadata.get_all(field, [])})
    want = sorted({_normalized(value) for value in expected})
    if actual != want:
        return [
            Violation(
                f"{field} must be {sorted(expected)!r}, found {sorted(actual)!r}.",
                location,
                rule="metadata-field",
            )
        ]
    return []


def metadata_violations(
    metadata: Message, expectation: Expectation, location: Location
) -> list[Violation]:
    """Compare core metadata fields against the release contract values."""
    problems: list[Violation] = []
    for field, expected in (
        ("Name", expectation.name),
        ("Version", expectation.version),
        ("Requires-Python", expectation.requires_python),
        ("License-Expression", expectation.license_expression),
    ):
        problems.extend(_single_value_problem(metadata, field, expected, location))
    for field, expected in (
        ("Requires-Dist", expectation.dependencies),
        ("Project-URL", tuple(f"{label}, {url}" for label, url in expectation.urls)),
        ("License-File", expectation.license_files),
    ):
        problems.extend(_multi_value_problem(metadata, field, expected, location))
    return problems


def wheel_file_violations(text: str, location: Location) -> list[Violation]:
    """Validate the WHEEL file's declared wheel version, purity and tag."""
    metadata = parse_metadata(text)
    problems: list[Violation] = []
    for field, expected in (
        ("Wheel-Version", "1.0"),
        ("Root-Is-Purelib", "true"),
        ("Tag", WHEEL_TAG),
    ):
        actual = metadata.get(field, "")
        if actual != expected:
            problems.append(
                Violation(
                    f"{field} must be {expected!r}, found {actual!r}.",
                    location,
                    rule="wheel-metadata",
                )
            )
    return problems


def entry_points_violations(
    text: str, expectation: Expectation, location: Location
) -> list[Violation]:
    """Compare the console scripts section with the declared entry points."""
    expected = [
        "[console_scripts]",
        *(f"{name} = {target}" for name, target in expectation.scripts),
    ]
    actual = [line.strip() for line in text.splitlines() if line.strip()]
    if actual != expected:
        return [
            Violation(
                f"console scripts must be {expected!r}, found {actual!r}.",
                location,
                rule="entry-point",
            )
        ]
    return []


def _parse_record_rows(
    text: str, archive: Path
) -> tuple[dict[str, tuple[str, str]], list[Violation]]:
    """Parse RECORD rows, returning well-formed rows and format problems."""
    rows: dict[str, tuple[str, str]] = {}
    problems: list[Violation] = []
    for row in csv.reader(io.StringIO(text)):
        if not row:
            continue
        if len(row) != 3:
            problems.append(
                Violation(
                    f"RECORD row must have three fields, found {len(row)}.",
                    Location(archive, symbol=row[0] if row else None),
                    rule="record-format",
                )
            )
            continue
        rows[row[0]] = (row[1], row[2])
    return rows, problems


def _record_extra_problems(
    rows: dict[str, tuple[str, str]], members: set[str], archive: Path
) -> list[Violation]:
    """Report RECORD rows that do not correspond to an archive member."""
    problems: list[Violation] = []
    for path in sorted(set(rows) - members):
        problems.append(
            Violation(
                "RECORD entry without an archive member.",
                Location(archive, symbol=path),
                rule="record-extra",
            )
        )
    return problems


def _record_missing_problems(
    rows: dict[str, tuple[str, str]], members: set[str], archive: Path
) -> list[Violation]:
    """Report archive members that lack a well-formed RECORD row."""
    problems: list[Violation] = []
    for path in sorted(members - set(rows)):
        problems.append(
            Violation(
                "Archive member absent from RECORD.",
                Location(archive, symbol=path),
                rule="record-missing",
            )
        )
    return problems


def _record_integrity_problems(
    rows: dict[str, tuple[str, str]],
    members: set[str],
    record_name: str,
    read: Callable[[str], bytes],
    archive: Path,
) -> list[Violation]:
    """Verify the sha256 and size claims of shared members except RECORD itself."""
    problems: list[Violation] = []
    for path in sorted((members & set(rows)) - {record_name}):
        payload = read(path)
        hash_field, size_field = rows[path]
        hash_bytes = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=")
        digest = f"sha256={hash_bytes.decode('ascii')}"
        if hash_field != digest:
            problems.append(
                Violation(
                    "RECORD sha256 does not match the member content.",
                    Location(archive, symbol=path),
                    rule="record-hash",
                )
            )
        if size_field != str(len(payload)):
            problems.append(
                Violation(
                    f"RECORD size must be {len(payload)}, found {size_field!r}.",
                    Location(archive, symbol=path),
                    rule="record-size",
                )
            )
    return problems


def record_violations(
    text: str,
    member_files: Collection[str],
    read: Callable[[str], bytes],
    archive: Path,
    record_name: str,
) -> list[Violation]:
    """Verify the RECORD's self-description, member coverage and integrity."""
    rows, problems = _parse_record_rows(text, archive)
    members = set(member_files)
    if rows.get(record_name) != ("", ""):
        problems.append(
            Violation(
                "RECORD must list itself without hash or size.",
                Location(archive, symbol=record_name),
                rule="record-format",
            )
        )
    problems.extend(_record_extra_problems(rows, members, archive))
    problems.extend(_record_missing_problems(rows, members, archive))
    problems.extend(_record_integrity_problems(rows, members, record_name, read, archive))
    return problems


def filename_violation(artifact: Path, expected_name: str) -> list[Violation]:
    """Report an artifact whose filename disagrees with the expected distribution."""
    if artifact.name != expected_name:
        return [
            Violation(
                f"Stale or misnamed artifact; expected {expected_name}.",
                Location(artifact),
                rule="artifact-name",
            )
        ]
    return []


def _audit_dist_info_document(
    document: str,
    member: str,
    text: str,
    files: Collection[str],
    expectation: Expectation,
    wheel: Path,
    read: Callable[[str], bytes],
) -> list[Violation]:
    """Audit one present dist-info document according to its kind."""
    location = Location(wheel, symbol=document)
    if document == "METADATA":
        return metadata_violations(parse_metadata(text), expectation, location)
    if document == "WHEEL":
        return wheel_file_violations(text, location)
    if document == "entry_points.txt":
        return entry_points_violations(text, expectation, location)
    return record_violations(text, files, read, wheel, member)


def audit_wheel(wheel: Path, expectation: Expectation) -> list[Violation]:
    """Audit one wheel's filename, inventory, metadata, entry points and RECORD."""
    root = f"{expectation.distribution}-{expectation.version}"
    problems = list(filename_violation(wheel, f"{root}-{WHEEL_TAG}.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        problems.extend(safety_violations(names, wheel))
        files = [name for name in names if not name.endswith("/")]
        problems.extend(allowlist_violations(wheel_inventory(expectation), files, wheel))
        dist_info = f"{root}.dist-info"
        for document in ("METADATA", "WHEEL", "entry_points.txt", "RECORD"):
            member = f"{dist_info}/{document}"
            if member not in files:
                continue
            text = archive.read(member).decode("utf-8")
            problems.extend(
                _audit_dist_info_document(
                    document,
                    member,
                    text,
                    files,
                    expectation,
                    wheel,
                    archive.read,
                )
            )
    return problems


def _sdist_files(
    members: list[tarfile.TarInfo], prefix: str, source: Path
) -> tuple[list[str], list[Violation]]:
    """Separate prefixed sdist files from members outside the release root."""
    files: list[str] = []
    problems: list[Violation] = []
    for member in members:
        if not member.isfile():
            continue
        name = member.name
        if not name.startswith(f"{prefix}/"):
            problems.append(
                Violation(
                    f"Member outside the {prefix}/ root.",
                    Location(source, symbol=name),
                    rule="archive-prefix",
                )
            )
            continue
        files.append(name[len(prefix) + 1 :])
    return files, problems


def _sdist_metadata_violations(
    members: list[tarfile.TarInfo],
    archive: tarfile.TarFile,
    prefix: str,
    expectation: Expectation,
    source: Path,
) -> list[Violation]:
    """Audit the PKG-INFO metadata when the source archive carries it."""
    location = Location(source, symbol="PKG-INFO")
    pkg_info = f"{prefix}/PKG-INFO"
    for member in members:
        if member.name == pkg_info and member.isfile():
            payload = archive.extractfile(member)
            if payload is not None:
                text = payload.read().decode("utf-8")
                return metadata_violations(parse_metadata(text), expectation, location)
    return []


def audit_sdist(source: Path, expectation: Expectation) -> list[Violation]:
    """Audit one sdist's filename, root prefix, inventory and PKG-INFO metadata."""
    prefix = f"{expectation.distribution}-{expectation.version}"
    problems = list(filename_violation(source, f"{prefix}.tar.gz"))
    with tarfile.open(source) as archive:
        members = archive.getmembers()
        problems.extend(safety_violations([member.name for member in members], source))
        files, prefix_problems = _sdist_files(members, prefix, source)
        problems.extend(prefix_problems)
        problems.extend(allowlist_violations(sdist_inventory(expectation), files, source))
        problems.extend(_sdist_metadata_violations(members, archive, prefix, expectation, source))
    return problems


def _run(
    command: list[str], *, cwd: Path, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a build command without leaking output on success."""
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
    )


def _execution_message(
    error: OSError
    | RuntimeError
    | KeyError
    | UnicodeDecodeError
    | subprocess.CalledProcessError
    | subprocess.TimeoutExpired
    | tomllib.TOMLDecodeError
    | zipfile.BadZipFile
    | tarfile.TarError,
) -> str:
    """Include captured tool diagnostics when an external command cannot complete."""
    details = getattr(error, "stderr", None) or getattr(error, "stdout", None)
    if isinstance(details, str) and details.strip():
        return f"{error}: {details.strip()}"
    return str(error)


class DistAuditCheck:
    """Audit wheel and source distribution contents, metadata and integrity."""

    name = "Distribution audit"

    def evaluate(self, target: Path | None) -> CheckResult:
        """Return structured problems found while auditing the dist directory."""
        if target is None:
            return CheckResult(
                (
                    InvalidTarget(
                        "check_dist_audit.py",
                        "Usage: check_dist_audit.py [dist]",
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
            problems = self._count_problems(target, wheels, sources)
            if problems:
                return CheckResult.from_problems(problems)
            expectation = load_expectation(REPOSITORY_ROOT / "pyproject.toml")
            problems.extend(audit_wheel(wheels[0], expectation))
            problems.extend(audit_sdist(sources[0], expectation))
            if problems:
                return CheckResult.from_problems(problems)
            return self._equivalence(wheels[0], sources[0])
        except (
            OSError,
            RuntimeError,
            KeyError,
            UnicodeDecodeError,
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            tomllib.TOMLDecodeError,
            zipfile.BadZipFile,
            tarfile.TarError,
        ) as error:
            return CheckResult((IncompleteCheck(self.name, _execution_message(error)),))

    @staticmethod
    def _count_problems(
        target: Path, wheels: tuple[Path, ...], sources: tuple[Path, ...]
    ) -> list[Violation]:
        """Report stale or duplicate artifacts instead of raising unpack errors."""
        problems: list[Violation] = []
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

    def _equivalence(self, wheel: Path, source: Path) -> CheckResult:
        """Rebuild the sdist in isolation and compare it with the direct wheel."""
        with TemporaryDirectory(prefix="smith-dist-audit-") as directory:
            root = Path(directory)
            extracted = root / "extracted"
            self._extract_source(source, extracted)
            roots = [child for child in extracted.iterdir() if child.is_dir()]
            if len(roots) != 1:
                raise RuntimeError(
                    f"sdist must contain exactly one root directory, found {len(roots)}."
                )
            out = root / "out"
            out.mkdir()
            _run(
                [
                    "uv",
                    "build",
                    "--wheel",
                    "--no-sources",
                    "--out-dir",
                    str(out),
                    str(roots[0]),
                ],
                cwd=root,
                timeout=120,
            )
            rebuilt = tuple(out.glob("*.whl"))
            if len(rebuilt) != 1:
                raise RuntimeError(f"Expected exactly one rebuilt wheel, found {len(rebuilt)}.")
            return self._compare_wheels(wheel, rebuilt[0])

    @staticmethod
    def _extract_source(source: Path, destination: Path) -> None:
        """Extract an sdist member-by-member with write_bytes, never extractall."""
        with tarfile.open(source) as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                payload = archive.extractfile(member)
                if payload is None:
                    continue
                target = destination / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload.read())

    @staticmethod
    def _compare_wheels(wheel: Path, rebuilt: Path) -> CheckResult:
        """Compare the direct wheel's inventory and metadata with the rebuilt wheel."""
        with (
            zipfile.ZipFile(wheel) as direct,
            zipfile.ZipFile(rebuilt) as derived,
        ):
            direct_files = {name for name in direct.namelist() if not name.endswith("/")}
            derived_files = {name for name in derived.namelist() if not name.endswith("/")}
            if direct_files != derived_files:
                return CheckResult(
                    (
                        Violation(
                            "Inventory differs from the sdist-derived wheel: "
                            f"only direct {sorted(direct_files - derived_files)}, "
                            f"only rebuilt {sorted(derived_files - direct_files)}.",
                            Location(wheel),
                            rule="equivalent-inventory",
                        ),
                    )
                )
            problems = _equivalent_metadata_problems(direct, derived, direct_files, wheel)
            return CheckResult.from_problems(problems)


def _equivalent_metadata_problems(
    direct: zipfile.ZipFile,
    derived: zipfile.ZipFile,
    files: Collection[str],
    wheel: Path,
) -> list[Violation]:
    """Report shared dist-info members whose bytes differ between two wheels."""
    problems: list[Violation] = []
    for name in sorted(files):
        if ".dist-info/" not in name:
            continue
        if direct.read(name) != derived.read(name):
            problems.append(
                Violation(
                    "Metadata differs from the sdist-derived wheel.",
                    Location(wheel, symbol=name),
                    rule="equivalent-metadata",
                )
            )
    return problems


def main(arguments: list[str]) -> int:
    """Evaluate the dist target through the shared feedback runner."""
    target = (
        Path(arguments[0])
        if len(arguments) == 1
        else Path.cwd() / "dist"
        if not arguments
        else None
    )
    return run_check(DistAuditCheck(), target)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
