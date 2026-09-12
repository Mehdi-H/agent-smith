"""Argparse adapter; console behavior belongs outside the application core."""

import argparse
from collections.abc import Sequence


def run(argv: Sequence[str] | None, *, version: str) -> int:
    """Handle informational options until document generation is implemented."""
    parser = argparse.ArgumentParser(
        prog="agent-smith",
        description="Build agent instructions from your project's sources.",
        epilog="Document generation is not implemented yet.",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parser.parse_args(argv)
    parser.print_help()
    return 0
