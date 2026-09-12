"""Keep actionable native update results, excluding one documented broken release."""

import json
import sys
from pathlib import Path


def mise_updates(content: str) -> list[str]:
    updates = json.loads(content)
    lines = []
    for name, item in updates.items():
        latest = item.get("bump") or item["latest"]
        if name == "vhs" and latest == "0.12.0":
            continue  # ADR 18: this release cannot export our demonstration.
        lines.append(f"{name}: {item['current']} -> {latest}")
    return lines


def uv_updates(content: str) -> list[str]:
    return [
        line for line in content.splitlines() if line.startswith(("Update ", "Add ", "Remove "))
    ]


def main() -> int:
    try:
        mode, path = sys.argv[1:]
        parser = {"mise": mise_updates, "uv": uv_updates}[mode]
        for line in parser(Path(path).read_text()):
            print(line)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Cannot read update results: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
