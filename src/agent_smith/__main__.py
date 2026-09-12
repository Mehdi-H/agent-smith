"""Composition root for the installed console script and python -m invocation."""

from collections.abc import Sequence
from importlib.metadata import version

from agent_smith.adapters.cli import run


def main(argv: Sequence[str] | None = None) -> int:
    """Wire installation metadata into the console adapter."""
    return run(argv, version=version("agent-smith"))


if __name__ == "__main__":
    raise SystemExit(main())
