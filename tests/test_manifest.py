"""Validate feedback against real just syntax and its native parser."""

import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).resolve().parents[1] / "scripts" / "check_manifest.py"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("prefix", "missing"),
    [
        ('# Explain usage.\n[group("Quality")]\n', []),
        ('[group("Quality")]\n', ["documentation"]),
        ("# Explain usage.\n", ["group"]),
        ("", ["documentation", "group"]),
        ('#   \n[group("Quality")]\n', ["documentation"]),
        ('# Explain usage.\n[group(" ")]\n', ["group"]),
    ],
)
def test_manifest_requires_documentation_and_group(
    prefix: str, missing: list[str], tmp_path: Path
) -> None:
    # Given a justfile with a complete or incomplete recipe declaration.
    manifest = tmp_path / "justfile"
    manifest.write_text(prefix + "sample:\n    exit 99\n")
    # When the checker inspects the manifest without running its recipe.
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(manifest)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Then only the complete declaration succeeds, with specific failure guidance.
    assert result.returncode == (1 if missing else 0)
    assert result.stdout == ""
    if missing:
        assert "recipe sample" in result.stderr
        for requirement in missing:
            assert requirement in result.stderr
    else:
        assert result.stderr == ""


@pytest.mark.integration
def test_manifest_checks_imported_private_recipes(tmp_path: Path) -> None:
    # Given an imported private helper lacking both required declarations.
    manifest = tmp_path / "justfile"
    manifest.write_text('import "helpers.just"\n')
    (tmp_path / "helpers.just").write_text("_helper:\n    exit 99\n")
    # When just parses the import and the checker inspects its recipes.
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(manifest)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Then the private helper cannot evade the manifest contract.
    assert result.returncode == 1
    assert "_helper" in result.stderr
    assert "documentation" in result.stderr
    assert "group" in result.stderr
