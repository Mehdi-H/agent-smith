"""CLI translation uses incoming ports without touching files or processes."""

from dataclasses import dataclass, field

import pytest

from agent_smith.adapters.cli import run
from agent_smith.application.ports import GenerationError, GenerationRequest


@dataclass
class Services:
    loaded: list[tuple[str | None, str | None, bool]] = field(default_factory=list)
    generated: list[GenerationRequest] = field(default_factory=list)
    failure: bool = False

    def load(self, path: str | None, *, output: str | None, no_overview: bool) -> GenerationRequest:
        self.loaded.append((path, output, no_overview))
        return GenerationRequest(output or "AGENTS.md")

    def generate(self, request: GenerationRequest) -> None:
        if self.failure:
            raise GenerationError("Cannot read README.md")
        self.generated.append(request)


def test_default_invocation_delegates_generation(capsys: pytest.CaptureFixture[str]) -> None:
    # Given in-memory implementations of both incoming ports.
    services = Services()
    # When the user invokes the CLI with no arguments.
    status = run([], version="1.2.3", configuration=services, generator=services)
    # Then the default request is generated with silent success.
    assert status == 0
    assert services.loaded == [(None, None, False)]
    assert services.generated == [GenerationRequest()]
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("option", ["-h", "--help", "--version"])
def test_information_does_not_load_configuration(
    option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    # Given incoming ports that would record any generation or configuration access.
    services = Services()
    # When an informational option is used.
    with pytest.raises(SystemExit) as exit_info:
        run([option], version="1.2.3", configuration=services, generator=services)
    # Then the CLI exits before any side effect and prints the requested information.
    assert exit_info.value.code == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert ("agent-smith 1.2.3" if option == "--version" else "usage: agent-smith") in output.out
    assert services.loaded == services.generated == []


@pytest.mark.parametrize("arguments", [["--unknown"], ["--vers"], ["unexpected"], ["--output"]])
def test_invalid_arguments_fail(arguments: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    # Given ports that must not be called for an invalid invocation.
    services = Services()
    # When argparse receives unsupported or incomplete arguments.
    with pytest.raises(SystemExit) as exit_info:
        run(arguments, version="1.2.3", configuration=services, generator=services)
    # Then usage errors report stderr and leave generation untouched.
    assert exit_info.value.code == 2
    assert capsys.readouterr().err
    assert services.loaded == services.generated == []


def test_cli_passes_explicit_overrides() -> None:
    # Given CLI values that should take precedence over configuration.
    services = Services()
    # When the user selects a configuration, output and disables the overview.
    status = run(
        ["--config", "custom.toml", "--output", "custom.md", "--no-overview"],
        version="1.2.3",
        configuration=services,
        generator=services,
    )
    # Then all explicit choices reach the configuration port without interpretation.
    assert status == 0
    assert services.loaded == [("custom.toml", "custom.md", True)]
    assert services.generated[0].output == "custom.md"


def test_generation_errors_have_no_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    # Given a failing application service.
    services = Services(failure=True)
    # When generation fails.
    status = run([], version="1", configuration=services, generator=services)
    # Then the public failure is actionable and confined to stderr.
    assert status == 1
    assert capsys.readouterr() == ("", "agent-smith: Cannot read README.md\n")


def test_provenance_preserves_cli_arguments_with_shell_quoting() -> None:
    # Given paths containing spaces and shell metacharacters.
    services = Services()
    arguments = ["--config", "my config.toml", "--output", "notes;draft.md"]
    # When the CLI supplies provenance to the application.
    run(arguments, version="1", configuration=services, generator=services)
    # Then the command can be copied without changing argument boundaries.
    assert services.generated[0].command == (
        "agent-smith --config 'my config.toml' --output 'notes;draft.md'"
    )
