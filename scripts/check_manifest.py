"""Validate documentation and grouping through just's parsed manifest."""

import json
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

from scripts.checks.core import (
    CheckResult,
    IncompleteCheck,
    InvalidTarget,
    Location,
    Violation,
    run_check,
)


class Recipe(TypedDict):
    doc: str | None
    attributes: list[str | dict[str, str]]
    namepath: str


class Manifest(TypedDict):
    source: str
    recipes: dict[str, Recipe]
    modules: dict[str, "Manifest"]
    groups: list[str]


def recipe_violations(
    source: str, name: str, recipe: Recipe, groups: tuple[str, ...]
) -> list[Violation]:
    """Report missing documentation or grouping for one recipe."""
    recipe_name = f"recipe {recipe['namepath'] or name}"
    location = Location(Path(source), symbol=recipe_name)
    violations = []
    if not (recipe["doc"] or "").strip():
        violations.append(
            Violation(
                "add a nonempty documentation comment above the recipe.",
                location,
                rule="documentation",
            )
        )
    own_groups = [
        attribute["group"]
        for attribute in recipe["attributes"]
        if isinstance(attribute, dict) and "group" in attribute
    ]
    if not any(group.strip() for group in (*groups, *own_groups)):
        violations.append(
            Violation(
                'add a nonempty [group("...")] attribute.',
                location,
                rule="group",
            )
        )
    return violations


def manifest_violations(
    manifest: Manifest, inherited_groups: tuple[str, ...] = ()
) -> list[Violation]:
    """Check every recipe, including private recipes and nested modules."""
    violations = []
    groups = (*inherited_groups, *manifest["groups"])
    for name, recipe in manifest["recipes"].items():
        violations.extend(recipe_violations(manifest["source"], name, recipe, groups))
    for module in manifest["modules"].values():
        violations.extend(manifest_violations(module, groups))
    return violations


class ManifestCheck:
    """Evaluate a justfile's parsed manifest against its documentation contract."""

    name = "Manifest check"

    def evaluate(self, target: Path | None) -> CheckResult:
        """Return typed recipe violations without printing or choosing a status."""
        if target is None:
            return CheckResult(
                (
                    InvalidTarget(
                        "Usage",
                        "check_manifest.py [justfile]",
                    ),
                )
            )
        if not target.is_file():
            return CheckResult(
                (InvalidTarget(str(target), "justfile does not exist or is not a file."),)
            )
        try:
            result = subprocess.run(
                ["just", "--justfile", str(target), "--dump", "--dump-format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode:
                message = result.stderr or result.stdout or f"Cannot parse {target}."
                return CheckResult((IncompleteCheck(self.name, message),))
            manifest: Manifest = json.loads(result.stdout)
            return CheckResult.from_problems(manifest_violations(manifest))
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError) as error:
            return CheckResult(
                (
                    IncompleteCheck(
                        self.name,
                        f"{target}: cannot inspect the just manifest: {error}",
                    ),
                )
            )


def main(arguments: list[str]) -> int:
    """Adapt command-line arguments to the shared feedback-check runner."""
    if len(arguments) == 1:
        path = Path(arguments[0])
    elif not arguments:
        path = Path("justfile")
    else:
        path = None
    return run_check(ManifestCheck(), path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
