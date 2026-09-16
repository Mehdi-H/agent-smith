"""Check that pinned GitHub Actions match the latest published release."""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TypeAlias

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    InvalidTarget,
    Location,
    Problem,
    Violation,
    run_check,
)
from scripts.checks.sha_pinning import FULL_SHA, USES, discover, reference_kind, use_reference

Target: TypeAlias = Path | tuple[Path, ...]


class ReleaseLookupError(Exception):
    """A latest release could not be resolved for an Action repository."""


@dataclass(frozen=True, slots=True)
class Release:
    """The latest published release of one Action, as a tag and commit SHA."""

    tag: str
    sha: str


class Releases(Protocol):
    """Resolve the latest published release of one Action repository."""

    def latest(self, repository: str) -> Release: ...


class GitHubReleases:
    """Resolve latest releases through the authenticated GitHub CLI."""

    def latest(self, repository: str) -> Release:
        """Return the latest release tag and the commit SHA that tag points to."""
        tag = self._query(["api", f"repos/{repository}/releases/latest", "--jq", ".tag_name"])
        sha = self._query(["api", f"repos/{repository}/commits/{tag}", "--jq", ".sha"])
        return Release(tag=tag, sha=sha)

    def _query(self, arguments: list[str]) -> str:
        """Run one gh api query and return its stripped standard output."""
        command = ["gh", *arguments]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=60, check=True
            )
        except (OSError, subprocess.SubprocessError) as error:
            detail = getattr(error, "stderr", "") or str(error)
            if isinstance(detail, bytes):
                detail = detail.decode("utf-8", "replace")
            joined = " ".join(command)
            raise ReleaseLookupError(f"gh api failed ({joined}): {detail.strip()}") from error
        return completed.stdout.strip()


@dataclass(frozen=True, slots=True)
class Reference:
    """One fully pinned external Action reference found on a workflow line."""

    path: Path
    line: int
    text: str
    repository: str
    pin: str


def external_reference(path: Path, number: int, line: str) -> Reference | None:
    """Return one fully pinned external reference, or None for every other line."""
    match = USES.match(line)
    if match is None:
        return None
    value = use_reference(match.group(1))
    if value is None or reference_kind(value) != "external":
        return None
    repository, separator, pin = value.rpartition("@")
    if not separator or not FULL_SHA.fullmatch(pin):
        return None
    return Reference(path, number, line.strip(), repository, pin)


def file_references(path: Path) -> tuple[list[Reference], list[Problem]]:
    """Collect the pinned external references of one workflow file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        problem = IncompleteCheck(ShaUpdateCheck.name, f"{path}: cannot inspect workflow: {error}")
        return [], [problem]
    references = [
        reference
        for number, line in enumerate(text.splitlines(), start=1)
        if (reference := external_reference(path, number, line)) is not None
    ]
    return references, []


def discover_files(paths: tuple[Path, ...]) -> tuple[set[Path], list[Problem]]:
    """Discover workflow files at the supplied paths."""
    files: set[Path] = set()
    problems: list[Problem] = []
    for path in paths:
        discovered, invalid = discover(path)
        files.update(discovered)
        problems.extend(invalid)
    if not files and not problems:
        names = ", ".join(str(path) for path in paths) or ".github/workflows"
        problems.append(InvalidTarget(names, "No workflow files found; check the supplied paths."))
    return files, problems


def update_problem(reference: Reference, release: Release) -> Violation:
    """Render one outdated pin as the line, latest version and SHA to write."""
    message = (
        f"external Action '{reference.repository}' is pinned to {reference.pin} but release "
        f"{release.tag} is available (commit {release.sha}); replace the line with:\n"
        f"    {reference.text}\n"
        f"    uses: {reference.repository}@{release.sha} # {release.tag}"
    )
    return Violation(message, Location(reference.path, line=reference.line), rule="outdated-pin")


def release_problems(
    releases: Releases, repository: str, references: list[Reference]
) -> list[Problem]:
    """Compare one repository's pins against its latest release."""
    try:
        release = releases.latest(repository)
    except ReleaseLookupError as error:
        return [IncompleteCheck(ShaUpdateCheck.name, f"{repository}: {error}")]
    return [
        update_problem(reference, release)
        for reference in references
        if reference.repository == repository and reference.pin.lower() != release.sha.lower()
    ]


class ShaUpdateCheck:
    """Compare pinned Action SHAs against the latest published releases."""

    name = "Action SHA update check"

    def __init__(self, releases: Releases | None = None) -> None:
        self._releases = releases if releases is not None else GitHubReleases()

    def evaluate(self, target: Target) -> CheckResult:
        """Discover workflow files and return typed update problems."""
        paths = (target,) if isinstance(target, Path) else target
        files, problems = discover_files(paths)
        references: list[Reference] = []
        for path in sorted(files):
            found, inspection_problems = file_references(path)
            references.extend(found)
            problems.extend(inspection_problems)
        for repository in sorted({reference.repository for reference in references}):
            problems.extend(release_problems(self._releases, repository, references))
        return CheckResult.from_problems(problems)


def main(arguments: list[str]) -> int:
    """Adapt command-line paths to the shared feedback-check runner."""
    paths = tuple(Path(argument) for argument in arguments) or (Path(".github/workflows"),)
    return run_check(ShaUpdateCheck(), paths)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
