"""Run explicitly configured commands with the platform shell."""

import subprocess

from agent_smith.application.ports import GenerationError


class ShellCommandRunner:
    def __init__(self, timeout: float = 30) -> None:
        self.timeout = timeout

    def run(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                # Custom extractors are explicitly trusted shell commands, not data inputs.
                shell=True,  # nosec B602
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout,
            )
        except (OSError, UnicodeError, subprocess.TimeoutExpired) as error:
            raise GenerationError(f"Cannot execute {command!r}: {error}") from error
        if result.returncode:
            diagnostic = result.stderr or result.stdout
            raise GenerationError(
                f"Command failed (exit {result.returncode}): {command}\n{diagnostic.rstrip()}"
            )
        return result.stdout
