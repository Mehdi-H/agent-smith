"""Unit tests for the pure distribution-audit functions, without files or archives."""

import base64
import hashlib
from pathlib import Path

import pytest

from scripts.check_dist_audit import (
    Expectation,
    allowlist_violations,
    entry_points_violations,
    filename_violation,
    metadata_violations,
    parse_metadata,
    record_violations,
    safety_violations,
    sdist_inventory,
    unsafe_reason,
    wheel_file_violations,
    wheel_inventory,
)
from scripts.checks.core import Location, Violation

EXPECTATION = Expectation(
    name="agent-smith-cli",
    version="0.6.0",
    requires_python=">=3.11",
    readme="README.md",
    dependencies=("markdown-it-py>=4,<5",),
    urls=(
        ("Issues", "https://example.test/issues"),
        ("Repository", "https://example.test"),
    ),
    scripts=(("agent-smith", "agent_smith.__main__:main"),),
    license_expression="MIT",
    license_files=("LICENSE",),
)

PACKAGE_PATHS = (
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
)


def _record_hash(content: bytes) -> str:
    """Return the unpadded urlsafe base64 sha256 digest used by RECORD rows."""
    digest = hashlib.sha256(content).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _record_text(members: dict[str, bytes], record_name: str) -> str:
    """Render one RECORD row per member (sorted) plus the record's own row."""
    rows = [
        f"{name},sha256={_record_hash(members[name])},{len(members[name])}"
        for name in sorted(name for name in members if name != record_name)
    ]
    return "\n".join([*rows, f"{record_name},,"]) + "\n"


def _metadata_text(
    version: str = "0.6.0",
    requires_python: str | None = ">=3.11",
    requires_dist: str = "markdown-it-py>=4,<5",
) -> str:
    """Render METADATA fields matching the release contract by default."""
    fields = [
        "Metadata-Version: 2.3",
        "Name: agent-smith-cli",
        f"Version: {version}",
    ]
    if requires_python is not None:
        fields.append(f"Requires-Python: {requires_python}")
    fields.extend(
        [
            "License-Expression: MIT",
            "License-File: LICENSE",
            f"Requires-Dist: {requires_dist}",
            "Project-URL: Issues, https://example.test/issues",
            "Project-URL: Repository, https://example.test",
        ]
    )
    return "\n".join(fields) + "\n"


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/etc/passwd", "absolute path"),
        ("C:/Windows/x.dll", "absolute path"),
        ("../evil.py", "parent traversal"),
        ("pkg/../../evil.py", "parent traversal"),
        ("pkg\\..\\evil.py", "backslash separator"),
        ("agent_smith/__main__.py", None),
    ],
)
def test_unsafe_reason_returns_hazard_categories(path: str, expected: str | None) -> None:
    # Given a member path taken from a distribution archive.
    # When the path is inspected for escape attempts.
    reason = unsafe_reason(path)
    # Then the hazard category or acceptance matches the contract.
    assert reason == expected


def test_safety_violations_flags_parent_traversal() -> None:
    # Given a wheel with one benign member and one parent traversal.
    # When every member path is checked for safety.
    violations: list[Violation] = safety_violations(
        ["agent_smith/cli.py", "../evil.py"], Path("dist/x.whl")
    )
    # Then only the traversal is reported with its hazard category.
    assert len(violations) == 1
    location: Location | None = violations[0].location
    assert violations[0].rule == "unsafe-path"
    assert location is not None and location.symbol == "../evil.py"
    assert "parent traversal" in violations[0].message


def test_allowlist_violations_report_missing_and_unexpected_files() -> None:
    # Given a wheel whose members differ from the version-neutral allowlist.
    # When the member set is compared against the allowlist.
    violations = allowlist_violations({"a.py", "b.py"}, {"b.py", "c.py"}, Path("dist/x.whl"))
    # Then both directions of the difference are reported with symbols.
    missing = next(violation for violation in violations if violation.rule == "missing-file")
    unexpected = next(violation for violation in violations if violation.rule == "unexpected-file")
    assert len(violations) == 2
    assert missing.location is not None and missing.location.symbol == "a.py"
    assert unexpected.location is not None and unexpected.location.symbol == "c.py"


def test_allowlist_violations_accept_exact_membership() -> None:
    # Given a wheel whose members match the allowlist exactly.
    # When the member set is compared against the allowlist.
    violations = allowlist_violations({"a.py", "b.py"}, {"a.py", "b.py"}, Path("dist/x.whl"))
    # Then nothing is missing or unexpected.
    assert violations == []


def test_wheel_inventory_matches_package_and_dist_info_allowlist() -> None:
    # Given the release contract for the current distribution version.
    expected = set(PACKAGE_PATHS) | {
        f"agent_smith_cli-0.6.0.dist-info/{name}"
        for name in ("METADATA", "WHEEL", "RECORD", "entry_points.txt", "licenses/LICENSE")
    }
    # When the wheel inventory is derived from the expectation.
    inventory = wheel_inventory(EXPECTATION)
    # Then it matches the package allowlist plus the dist-info records.
    assert inventory == expected


def test_sdist_inventory_matches_metadata_and_src_tree() -> None:
    # Given the release contract for the current source distribution.
    expected = {"PKG-INFO", "pyproject.toml", "pyproject.toml.orig", "README.md", "LICENSE"} | {
        f"src/{path}" for path in PACKAGE_PATHS
    }
    # When the sdist inventory is derived from the expectation.
    inventory = sdist_inventory(EXPECTATION)
    # Then it matches the root metadata files plus the src tree.
    assert inventory == expected


def test_metadata_violations_accept_contract_matching_fields() -> None:
    # Given METADATA whose fields reproduce the release contract.
    metadata = parse_metadata(_metadata_text())
    # When the parsed fields are validated against the contract.
    violations = metadata_violations(metadata, EXPECTATION, Location(Path("dist/x.whl")))
    # Then no field deviates from the contract.
    assert violations == []


def test_metadata_violations_catch_version_mismatches() -> None:
    # Given METADATA declaring a stale version.
    metadata = parse_metadata(_metadata_text(version="0.5.0"))
    # When the parsed fields are validated against the contract.
    violations = metadata_violations(metadata, EXPECTATION, Location(Path("dist/x.whl")))
    # Then the expected version is named in a single violation.
    assert len(violations) == 1
    assert violations[0].rule == "metadata-field"
    assert violations[0].message == "Version must be '0.6.0', found '0.5.0'."


def test_metadata_violations_catch_missing_requires_python() -> None:
    # Given METADATA without a Requires-Python declaration.
    metadata = parse_metadata(_metadata_text(requires_python=None))
    # When the parsed fields are validated against the contract.
    violations = metadata_violations(metadata, EXPECTATION, Location(Path("dist/x.whl")))
    # Then the absent field is reported with the empty parsed value.
    assert len(violations) == 1
    assert "Requires-Python" in violations[0].message
    assert "found ''" in violations[0].message


def test_metadata_violations_normalize_requires_dist_whitespace() -> None:
    # Given a Requires-Dist spelled with a space around the comma.
    metadata = parse_metadata(_metadata_text(requires_dist="markdown-it-py>=4, <5"))
    # When the parsed fields are validated against the contract.
    violations = metadata_violations(metadata, EXPECTATION, Location(Path("dist/x.whl")))
    # Then the normalized comparison still matches.
    assert violations == []


def test_wheel_file_violations_accept_universal_purelib_wheel() -> None:
    # Given a WHEEL declaring the universal pure-Python tag.
    text = "Wheel-Version: 1.0\nGenerator: uv 0.12.10\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    # When the WHEEL metadata is validated.
    violations = wheel_file_violations(text, Location(Path("dist/x.whl")))
    # Then the universal purelib declaration passes.
    assert violations == []


def test_wheel_file_violations_reject_platform_tags() -> None:
    # Given a WHEEL declaring a platform-specific tag.
    text = "Wheel-Version: 1.0\nGenerator: uv 0.12.10\nRoot-Is-Purelib: true\nTag: py311-none-any\n"
    # When the WHEEL metadata is validated.
    violations = wheel_file_violations(text, Location(Path("dist/x.whl")))
    # Then the non-universal tag is reported as wheel-metadata.
    assert len(violations) == 1
    assert violations[0].rule == "wheel-metadata"


def test_entry_points_violations_accept_contract_script() -> None:
    # Given an entry points file declaring the expected console script.
    text = "[console_scripts]\nagent-smith = agent_smith.__main__:main\n\n"
    # When the entry point target is validated.
    violations = entry_points_violations(text, EXPECTATION, Location(Path("dist/x.whl")))
    # Then the declared target matches the contract.
    assert violations == []


def test_entry_points_violations_reject_altered_targets() -> None:
    # Given an entry points file pointing at an undeclared target.
    text = "[console_scripts]\nagent-smith = agent_smith.__main__:nope\n\n"
    # When the entry point target is validated.
    violations = entry_points_violations(text, EXPECTATION, Location(Path("dist/x.whl")))
    # Then the mismatched target is reported as entry-point.
    assert len(violations) == 1
    assert violations[0].rule == "entry-point"


def test_record_violations_accept_consistent_rows() -> None:
    # Given a RECORD whose rows match the archive members exactly.
    record_name = "dist-info/RECORD"
    members = {"a.py": b"aaa", "b.py": b"bbbb", record_name: b""}
    # When every hash and size is reconciled with the members.
    violations = record_violations(
        _record_text(members, record_name),
        members,
        members.__getitem__,
        Path("dist/x.whl"),
        record_name,
    )
    # Then the archive contents and RECORD agree.
    assert violations == []


def test_record_violations_catch_hash_mismatches() -> None:
    # Given a RECORD computed for earlier member content.
    record_name = "dist-info/RECORD"
    stale = {"a.py": b"aaa", record_name: b""}
    current = {"a.py": b"aax", record_name: b""}
    # When an archive member is rewritten without changing its length.
    violations = record_violations(
        _record_text(stale, record_name),
        current,
        current.__getitem__,
        Path("dist/x.whl"),
        record_name,
    )
    # Then the stale hash is reported as a record-hash violation.
    assert len(violations) == 1
    assert violations[0].rule == "record-hash"


def test_record_violations_catch_size_mismatches() -> None:
    # Given a RECORD row whose size field contradicts the member.
    record_name = "dist-info/RECORD"
    text = f"a.py,sha256={_record_hash(b'aaa')},99\n{record_name},,\n"
    members = {"a.py": b"aaa", record_name: b""}
    # When the row is reconciled against the archive member.
    violations = record_violations(
        text, members, members.__getitem__, Path("dist/x.whl"), record_name
    )
    # Then the wrong size is reported as a record-size violation.
    assert len(violations) == 1
    assert violations[0].rule == "record-size"


def test_record_violations_catch_omitted_members() -> None:
    # Given a RECORD that forgets one member row.
    record_name = "dist-info/RECORD"
    members = {"a.py": b"aaa", "b.py": b"bbbb", record_name: b""}
    text = _record_text({"a.py": b"aaa", record_name: b""}, record_name)
    # When the text is reconciled against the full member set.
    violations = record_violations(
        text, members, members.__getitem__, Path("dist/x.whl"), record_name
    )
    # Then the absent b.py row is reported as record-missing.
    assert len(violations) == 1
    assert violations[0].rule == "record-missing"


def test_record_violations_catch_unexpected_rows() -> None:
    # Given a RECORD containing a row for a phantom member.
    record_name = "dist-info/RECORD"
    members = {"a.py": b"aaa", "b.py": b"bbbb", record_name: b""}
    phantom = {"a.py": b"aaa", "b.py": b"bbbb", "c.py": b"ccc", record_name: b""}
    # When the text is reconciled against the real member set.
    violations = record_violations(
        _record_text(phantom, record_name),
        members,
        members.__getitem__,
        Path("dist/x.whl"),
        record_name,
    )
    # Then the phantom row is reported as record-extra.
    assert len(violations) == 1
    assert violations[0].rule == "record-extra"


def test_record_violations_reject_self_hash_rows() -> None:
    # Given a RECORD carrying a hash and size for its own row.
    record_name = "dist-info/RECORD"
    text = f"a.py,sha256={_record_hash(b'aaa')},3\n{record_name},sha256=x,1\n"
    members = {"a.py": b"aaa", record_name: b""}
    # When the record's own row is inspected.
    violations = record_violations(
        text, members, members.__getitem__, Path("dist/x.whl"), record_name
    )
    # Then the malformed self row is reported as record-format.
    assert len(violations) == 1
    assert violations[0].rule == "record-format"


def test_record_violations_reject_two_field_rows() -> None:
    # Given a RECORD row missing its size field.
    record_name = "dist-info/RECORD"
    text = f"a.py,sha256=x\n{record_name},,\n"
    members = {"a.py": b"aaa", record_name: b""}
    # When the malformed row is inspected.
    violations = record_violations(
        text, members, members.__getitem__, Path("dist/x.whl"), record_name
    )
    # Then the malformed row is reported as record-format and its member as missing.
    assert len(violations) == 2
    assert {violation.rule for violation in violations} == {"record-format", "record-missing"}


def test_filename_violation_accepts_expected_artifact_name() -> None:
    # Given a wheel whose name matches the expected release artifact.
    artifact = Path("dist/agent_smith_cli-0.6.0-py3-none-any.whl")
    # When the artifact name is validated.
    violations = filename_violation(artifact, "agent_smith_cli-0.6.0-py3-none-any.whl")
    # Then the expected name passes.
    assert violations == []


def test_filename_violation_rejects_stale_names() -> None:
    # Given a wheel whose name no longer matches the release contract.
    artifact = Path("dist/agent_smith_cli-0.6.0-py3-none-any.whl")
    # When the artifact name is validated against a different expectation.
    violations = filename_violation(artifact, "agent_smith_cli-0.5.0-py3-none-any.whl")
    # Then a single artifact-name violation names the expected artifact.
    assert len(violations) == 1
    assert violations[0].rule == "artifact-name"
    assert "agent_smith_cli-0.5.0-py3-none-any.whl" in violations[0].message
