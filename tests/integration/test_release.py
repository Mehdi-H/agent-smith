"""Exercise the real release CLI against disposable Git histories without publishing."""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PSR = Path(sys.executable).with_name("semantic-release")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def release_repo(tmp_path: Path) -> Path:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["semantic_release"]
    config["build_command"] = ""
    (tmp_path / "release.json").write_text(json.dumps({"semantic_release": config}))
    (tmp_path / "pyproject.toml").write_text('[project]\nname="example"\nversion="0.3.0"\n')
    (tmp_path / "uv.lock").write_text("# Fixture lock\n")
    git(tmp_path, "init", "-b", "main")
    git(tmp_path, "config", "user.name", "Release Test")
    git(tmp_path, "config", "user.email", "release@example.invalid")
    git(tmp_path, "remote", "add", "origin", "https://github.com/example/fixture.git")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "feat: initial version")
    git(tmp_path, "tag", "v0.3.0")
    return tmp_path


def semantic(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GITHUB_")}
    environment.pop("GH_TOKEN", None)
    return subprocess.run(
        [str(PSR), "-c", "release.json", *args],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
    )


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("fix: repair output", "0.3.1"),
        ("perf: speed up", "0.3.1"),
        ("feat: another extractor", "0.4.0"),
        ("feat!: change configuration", "0.4.0"),
    ],
)
def test_release_level(release_repo: Path, message: str, expected: str) -> None:
    # Given a real tagged history and a conventional commit.
    git(release_repo, "commit", "--allow-empty", "-m", message)
    # When PSR computes the next release without writing.
    result = semantic(release_repo, "version", "--print")
    # Then the configured pre-1.0 policy determines the version.
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected
    assert git(release_repo, "status", "--porcelain") == ""


def test_release_writes_changelog_and_tag_without_remote_changes(release_repo: Path) -> None:
    # Given a feature after the existing release.
    git(release_repo, "commit", "--allow-empty", "-m", "feat: add a new extractor")
    # When releasing locally with both external operations disabled.
    result = semantic(release_repo, "version", "--no-push", "--no-vcs-release")
    # Then the version, changelog and local tag agree.
    assert result.returncode == 0, result.stderr
    assert (
        tomllib.loads((release_repo / "pyproject.toml").read_text())["project"]["version"]
        == "0.4.0"
    )
    assert "add a new extractor" in (release_repo / "CHANGELOG.md").read_text().lower()
    assert git(release_repo, "describe", "--tags", "--exact-match") == "v0.4.0"
    assert git(release_repo, "status", "--porcelain") == ""


@pytest.mark.parametrize("branch", ["main", "feature"])
def test_no_release_for_docs_or_non_main(release_repo: Path, branch: str) -> None:
    # Given documentation on main or a feature on a non-release branch.
    git(release_repo, "switch", "-C", branch)
    message = "docs: clarify usage" if branch == "main" else "feat: new extractor"
    git(release_repo, "commit", "--allow-empty", "-m", message)
    head = git(release_repo, "rev-parse", "HEAD")
    # When PSR attempts a local release.
    result = semantic(release_repo, "version", "--no-push", "--no-vcs-release")
    # Then it creates neither a release commit nor a tag.
    assert result.returncode in (0, 1), result.stderr
    assert git(release_repo, "rev-parse", "HEAD") == head
    assert git(release_repo, "tag") == "v0.3.0"
    assert not (release_repo / "CHANGELOG.md").exists()


@pytest.mark.parametrize(
    ("actions", "ref", "event", "expected"),
    [
        ("", "refs/heads/main", "push", 1),
        ("true", "refs/heads/topic", "push", 1),
        ("true", "refs/tags/v0.4.0", "push", 1),
        ("true", "refs/heads/main", "pull_request", 1),
        ("true", "refs/heads/main", "push", 0),
    ],
)
def test_publication_guard(actions: str, ref: str, event: str, expected: int) -> None:
    # Given explicit execution context without any publication credentials.
    environment = {
        "PATH": os.environ["PATH"],
        "GITHUB_ACTIONS": actions,
        "GITHUB_REF": ref,
        "GITHUB_EVENT_NAME": event,
    }
    # When running the guard directly without performing publication.
    result = subprocess.run(
        ["sh", str(ROOT / "scripts/release-guard.sh")],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Then only the main push context is allowed.
    assert result.returncode == expected
    assert bool(result.stderr) == bool(expected)


def test_bootstrap_forces_only_a_patch(release_repo: Path) -> None:
    # Given only tooling changes since the existing release.
    git(release_repo, "commit", "--allow-empty", "-m", "ci: automate releases")
    # When explicitly bootstrapping without either remote publication operation.
    result = semantic(release_repo, "version", "--patch", "--no-push", "--no-vcs-release")
    # Then the new local tag stays below 1.0.
    assert result.returncode == 0, result.stderr
    assert git(release_repo, "describe", "--tags", "--exact-match") == "v0.3.1"


def test_lock_refresh_keeps_third_party_versions(tmp_path: Path) -> None:
    # Given the real locked project with only its version stamp changed.
    project = (ROOT / "pyproject.toml").read_text()
    current = tomllib.loads(project)["project"]["version"]
    major, minor, micro = current.split(".")
    following = f"{major}.{minor}.{int(micro) + 1}"
    project = project.replace(f'version = "{current}"', f'version = "{following}"', 1)
    (tmp_path / "pyproject.toml").write_text(project)
    (tmp_path / "uv.lock").write_bytes((ROOT / "uv.lock").read_bytes())
    before = tomllib.loads((tmp_path / "uv.lock").read_text())["package"]
    # When performing the release build's project-only lock refresh.
    result = subprocess.run(
        ["uv", "lock", "--upgrade-package", "agent-smith-cli"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=30,
    )
    # Then only the project's version changes, preserving tested dependencies.
    assert result.returncode == 0, result.stderr
    after = tomllib.loads((tmp_path / "uv.lock").read_text())["package"]
    project_after = next(package for package in after if package["name"] == "agent-smith-cli")
    assert project_after["version"] == following
    assert [p for p in before if p["name"] != "agent-smith-cli"] == [
        p for p in after if p["name"] != "agent-smith-cli"
    ]
