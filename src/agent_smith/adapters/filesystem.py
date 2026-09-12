"""UTF-8 input and atomic output adapters."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from agent_smith.application.ports import GenerationError


class FileTextReader:
    def read(self, path: str) -> str:
        try:
            return Path(path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            raise GenerationError(f"Cannot read {path!r}: {error}") from error


class AtomicDocumentWriter:
    def write(self, path: str, content: str) -> None:
        destination = Path(path)
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", dir=destination.parent, delete=False
            ) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            os.replace(temporary, destination)
        except (OSError, UnicodeError) as error:
            raise GenerationError(f"Cannot write {path!r}: {error}") from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
