"""Observable console behavior, without executing external processes."""

import pytest

from agent_smith.adapters.cli import run


def test_no_arguments_explains_current_capabilities(capsys: pytest.CaptureFixture[str]) -> None:
    assert run([], version="1.2.3") == 0
    output = capsys.readouterr()
    assert "--help" in output.out
    assert "--version" in output.out
    assert "generation is not implemented" in output.out
    assert output.err == ""


@pytest.mark.parametrize("option", ["-h", "--help"])
def test_help_exits_successfully(option: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run([option], version="1.2.3")
    assert exit_info.value.code == 0
    assert "usage: agent-smith" in capsys.readouterr().out


def test_version_uses_injected_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run(["--version"], version="1.2.3")
    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "agent-smith 1.2.3\n"


@pytest.mark.parametrize("option", ["--unknown", "--vers", "unexpected"])
def test_invalid_arguments_fail(option: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        run([option], version="1.2.3")
    assert exit_info.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "unrecognized arguments" in output.err
