"""Argparse adapter; console behavior belongs outside the application core."""

import argparse
import shlex
import sys
from collections.abc import Sequence
from dataclasses import replace

from agent_smith.application.ports import Configuration, GenerationError, Generator


def run(
    argv: Sequence[str] | None, *, version: str, configuration: Configuration, generator: Generator
) -> int:
    """Translate CLI options into an application request through incoming ports."""
    parser = argparse.ArgumentParser(
        prog="agent-smith",
        description="Build agent instructions from your project's sources.",
        epilog="Detects README.md, justfile and mise.toml; customize sections in agent-smith.toml.",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parser.add_argument("--config", metavar="PATH", help="Read this TOML configuration file.")
    parser.add_argument(
        "--output", metavar="PATH", help="Override the output path (default: AGENTS.md)."
    )
    parser.add_argument(
        "--no-overview", action="store_true", help="Disable the built-in README overview."
    )
    parser.add_argument(
        "--no-available-commands",
        action="store_true",
        help="Disable the built-in just help section.",
    )
    parser.add_argument(
        "--no-tech-stack", action="store_true", help="Disable the built-in mise.toml tech stack."
    )
    invocation = list(sys.argv[1:] if argv is None else argv)
    arguments = parser.parse_args(invocation)
    try:
        request = configuration.load(
            arguments.config,
            output=arguments.output,
            no_overview=arguments.no_overview,
            no_available_commands=arguments.no_available_commands,
            no_tech_stack=arguments.no_tech_stack,
        )
        generator.generate(replace(request, command=shlex.join(["agent-smith", *invocation])))
    except GenerationError as error:
        print(f"agent-smith: {error}", file=sys.stderr)
        return 1
    return 0
