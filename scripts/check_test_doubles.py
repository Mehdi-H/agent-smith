"""Reject textual uses of patching APIs anywhere in Python test sources."""

import re
import sys
from pathlib import Path

FORBIDDEN = re.compile(r"\b(?:monkey[ _-]?patch\w*|patch(?:\b|_\w*))", re.IGNORECASE)


def check(directory: Path) -> int:
    failed = False
    for path in sorted(directory.rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            # A literal semantic-version CLI flag is not a replacement API.
            inspected = re.sub(r"([\"'])--patch\1", "", line)
            if FORBIDDEN.search(inspected):
                print(
                    f"{path}:{number}: forbidden test replacement: {line.strip()}", file=sys.stderr
                )
                failed = True
    return int(failed)


def main() -> int:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "tests")
    try:
        if not directory.is_dir():
            raise ValueError(f"Test directory does not exist: {directory}")
        return check(directory)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
