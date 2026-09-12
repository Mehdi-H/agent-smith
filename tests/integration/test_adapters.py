"""Effects are verified at their real filesystem and subprocess boundaries."""

import sys
from pathlib import Path

import pytest

from agent_smith.adapters.filesystem import AtomicDocumentWriter, FileTextReader
from agent_smith.adapters.process import ShellCommandRunner
from agent_smith.application.ports import GenerationError


def test_utf8_reader_and_atomic_writer(tmp_path: Path) -> None:
    # Given a Unicode source with BOM and an existing destination.
    source = tmp_path / "README.md"
    source.write_bytes(b"\xef\xbb\xbf" + "# Café\r\n".encode())
    destination = tmp_path / "AGENTS.md"
    destination.write_text("Old", encoding="utf-8")
    # When the input is read and a document atomically replaces the output.
    content = FileTextReader().read(str(source))
    AtomicDocumentWriter().write(str(destination), content)
    # Then bytes are UTF-8 with LF and no temporary file remains.
    assert destination.read_bytes() == "# Café\n".encode()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["AGENTS.md", "README.md"]


def test_replace_failure_keeps_destination(tmp_path: Path) -> None:
    # Given an output path that is an existing directory.
    destination = tmp_path / "AGENTS.md"
    destination.mkdir()
    # When atomic replacement cannot succeed.
    with pytest.raises(GenerationError):
        AtomicDocumentWriter().write(str(destination), "Content")
    # Then the existing destination survives and temporary output is cleaned up.
    assert destination.is_dir()
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.parametrize("content", [None, b"\xff"])
def test_read_errors_become_application_errors(content: bytes | None, tmp_path: Path) -> None:
    # Given an absent or non-UTF-8 source file.
    source = tmp_path / "README.md"
    if content is not None:
        source.write_bytes(content)
    # When the filesystem reader accesses it.
    with pytest.raises(GenerationError) as failure:
        FileTextReader().read(str(source))
    # Then the failing source path is part of the diagnostic.
    assert str(source) in str(failure.value)


def test_shell_returns_only_stdout() -> None:
    # Given a command that writes different content to stdout and stderr.
    command = (
        f'''"{sys.executable}" -c "import sys; print('Body'); print('Debug', file=sys.stderr)"'''
    )
    # When the configured command executes.
    output = ShellCommandRunner().run(command)
    # Then stderr is not incorporated into the Markdown section.
    assert output == "Body\n"


def test_shell_failure_preserves_native_diagnostic() -> None:
    # Given an extractor that fails with a diagnostic.
    command = (
        f'"{sys.executable}" -c "import sys; '
        "print('Broken extractor', file=sys.stderr); sys.exit(7)\""
    )
    # When it runs through the process adapter.
    with pytest.raises(GenerationError) as failure:
        ShellCommandRunner().run(command)
    # Then the command, native status and diagnostic are reported.
    assert command in str(failure.value)
    assert "exit 7" in str(failure.value)
    assert "Broken extractor" in str(failure.value)


def test_shell_timeout_is_a_failure() -> None:
    # Given a command longer than the adapter's configured timeout.
    command = f'''"{sys.executable}" -c "import time; time.sleep(0.2)"'''
    # When the timeout expires.
    with pytest.raises(GenerationError) as failure:
        ShellCommandRunner(timeout=0.01).run(command)
    # Then the adapter reports the command failure rather than successful empty output.
    assert "timed out" in str(failure.value)
