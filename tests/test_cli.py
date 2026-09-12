"""Observable console behavior, without executing external processes."""

import pytest

from agent_smith.adapters.cli import run


def test_no_arguments_explains_current_capabilities(capsys: pytest.CaptureFixture[str]) -> None:
    # Given an invocation with no arguments and an installed version.
    arguments: list[str] = []
    # When the CLI runs.
    status = run(arguments, version="1.2.3")
    output = capsys.readouterr()
    # Then it explains available capabilities without reporting an error.
    assert status == 0
    assert "--help" in output.out
    assert "--version" in output.out
    assert "generation is not implemented" in output.out
    assert output.err == ""


@pytest.mark.parametrize("option", ["-h", "--help"])
def test_help_exits_successfully(option: str, capsys: pytest.CaptureFixture[str]) -> None:
    # Given a supported help option supplied by parametrization.
    arguments = [option]
    # When help is requested.
    with pytest.raises(SystemExit) as exit_info:
        run(arguments, version="1.2.3")
    # Then the CLI exits successfully and displays usage.
    assert exit_info.value.code == 0
    assert "usage: agent-smith" in capsys.readouterr().out


def test_version_uses_injected_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    # Given installation metadata supplied to the adapter.
    version = "1.2.3"
    # When the version is requested.
    with pytest.raises(SystemExit) as exit_info:
        run(["--version"], version=version)
    # Then the injected version is printed before a successful exit.
    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "agent-smith 1.2.3\n"


@pytest.mark.parametrize("option", ["--unknown", "--vers", "unexpected"])
def test_invalid_arguments_fail(option: str, capsys: pytest.CaptureFixture[str]) -> None:
    # Given an unsupported argument, including an abbreviated option.
    arguments = [option]
    # When the CLI parses the arguments.
    with pytest.raises(SystemExit) as exit_info:
        run(arguments, version="1.2.3")
    # Then it rejects the invocation with a diagnostic on stderr.
    assert exit_info.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "unrecognized arguments" in output.err
