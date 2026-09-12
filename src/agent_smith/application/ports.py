"""Framework-independent contracts for generating an instruction document."""

from dataclasses import dataclass
from typing import Protocol


class GenerationError(Exception):
    """An actionable failure that must leave the existing document untouched."""


@dataclass(frozen=True)
class OverviewSection:
    title: str = "Overview"
    source: str = "README.md"


@dataclass(frozen=True)
class AvailableCommandsSection:
    title: str = "Available commands"
    command: str = "just help"


@dataclass(frozen=True)
class CommandSection:
    title: str
    command: str


Section = OverviewSection | AvailableCommandsSection | CommandSection


@dataclass(frozen=True)
class GenerationRequest:
    output: str = "AGENTS.md"
    sections: tuple[Section, ...] = (OverviewSection(),)
    command: str = "agent-smith"


class Generator(Protocol):
    def generate(self, request: GenerationRequest) -> None: ...


class Configuration(Protocol):
    def load(
        self,
        path: str | None,
        *,
        output: str | None,
        no_overview: bool,
        no_available_commands: bool = False,
    ) -> GenerationRequest: ...


class TextReader(Protocol):
    def read(self, path: str) -> str: ...


class OverviewParser(Protocol):
    def extract(self, markdown: str) -> str: ...


class HelpParser(Protocol):
    def render(self, output: str) -> str: ...


class CommandRunner(Protocol):
    def run(self, command: str) -> str: ...


class DocumentWriter(Protocol):
    def write(self, path: str, content: str) -> None: ...
