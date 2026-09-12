"""Composition root for the installed console script and python -m invocation."""

from collections.abc import Sequence
from importlib.metadata import version

from agent_smith.adapters.cli import run
from agent_smith.adapters.configuration import TomlConfiguration
from agent_smith.adapters.filesystem import AtomicDocumentWriter, FileTextReader
from agent_smith.adapters.just_help import JustHelpParser
from agent_smith.adapters.markdown import MarkdownOverviewParser
from agent_smith.adapters.process import ShellCommandRunner
from agent_smith.application.generation import GenerationService


def main(argv: Sequence[str] | None = None) -> int:
    """Wire concrete adapters into the application and incoming CLI boundary."""
    generator = GenerationService(
        FileTextReader(),
        MarkdownOverviewParser(),
        ShellCommandRunner(),
        AtomicDocumentWriter(),
        JustHelpParser(),
    )
    return run(
        argv, version=version("agent-smith"), configuration=TomlConfiguration(), generator=generator
    )


if __name__ == "__main__":
    raise SystemExit(main())
