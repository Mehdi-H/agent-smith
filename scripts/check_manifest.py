"""Validate documentation and grouping through just's parsed manifest."""

import json
import subprocess
import sys
from pathlib import Path
from typing import TypedDict


class Recipe(TypedDict):
    doc: str | None
    attributes: list[str | dict[str, str]]
    namepath: str


class Manifest(TypedDict):
    source: str
    recipes: dict[str, Recipe]
    modules: dict[str, "Manifest"]
    groups: list[str]


def inspect(manifest: Manifest, inherited_groups: tuple[str, ...] = ()) -> list[str]:
    """Check every recipe, including private recipes and nested modules."""
    errors = []
    groups = (*inherited_groups, *manifest["groups"])
    for name, recipe in manifest["recipes"].items():
        location = f"{manifest['source']}: recipe {recipe['namepath'] or name}"
        if not (recipe["doc"] or "").strip():
            errors.append(f"{location}: add a nonempty documentation comment above the recipe.")
        own_groups = [
            attribute["group"]
            for attribute in recipe["attributes"]
            if isinstance(attribute, dict) and "group" in attribute
        ]
        if not any(group.strip() for group in (*groups, *own_groups)):
            errors.append(f'{location}: add a nonempty [group("...")] attribute.')
    for module in manifest["modules"].values():
        errors.extend(inspect(module, groups))
    return errors


def main(arguments: list[str]) -> int:
    """Parse using the pinned just executable; report failures without executing recipes."""
    if len(arguments) > 1:
        print("Usage: check_manifest.py [justfile]", file=sys.stderr)
        return 1
    path = Path(arguments[0] if arguments else "justfile")
    try:
        result = subprocess.run(
            ["just", "--justfile", str(path), "--dump", "--dump-format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode:
            print(result.stderr or result.stdout or f"Cannot parse {path}.", file=sys.stderr)
            return 1
        manifest: Manifest = json.loads(result.stdout)
        errors = inspect(manifest)
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError) as error:
        print(f"{path}: cannot inspect the just manifest: {error}", file=sys.stderr)
        return 1
    for error in errors:
        print(error, file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
