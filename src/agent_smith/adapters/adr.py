"""Condense adr list paths into a directory and literal extensionless filenames."""

from pathlib import PurePosixPath

from agent_smith.application.generation import inline_code
from agent_smith.application.ports import GenerationError


def decision_stem(line: str, directory: str) -> str:
    path = PurePosixPath(line)
    if path.parent != PurePosixPath(directory) or path.suffix != ".md":
        raise GenerationError(f"Unexpected adr list path {line!r} for directory {directory!r}.")
    if any(ord(char) < 32 for char in line) or not path.stem:
        raise GenerationError("ADR filenames must be nonempty and on one line.")
    return path.stem


class AdrListParser:
    def render(self, directory: str, listing: str) -> str:
        directory = directory.strip()
        if not directory or any(ord(char) < 32 for char in directory):
            raise GenerationError(".adr-dir must contain a nonempty directory on one line.")
        paths = [line for line in listing.splitlines() if line.strip()]
        if not paths:
            raise GenerationError("adr list returned no architecture decisions.")
        bullets = [f"- {inline_code(decision_stem(line, directory))}" for line in paths]
        return f"Directory: {inline_code(directory)}\n\n" + "\n".join(bullets)
