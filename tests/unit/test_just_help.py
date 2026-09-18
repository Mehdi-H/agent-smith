"""Interpret help as a usage manifest without executing any listed recipe."""

import pytest

from agent_smith.adapters.just_help import JustHelpParser
from agent_smith.application.ports import GenerationError


def test_help_preserves_groups_signatures_and_descriptions() -> None:
    # Given documented commands with groups, variadic arguments and quoted defaults.
    output = """Available recipes:
    info # Project information.

    [Quality]
    check # Check the repo.
    scan +paths mode="a # b" # Scan **all** paths.

    [Build]
    build target='wheel' # Build a package.
"""
    # When help becomes Markdown.
    result = JustHelpParser().render(output)
    # Then order and complete signatures are retained, including hashes inside defaults.
    assert result == (
        "- `just info` — Project information.\n\n### Quality\n\n"
        "- `just check` — Check the repo.\n"
        '- `just scan +paths mode="a # b"` — Scan **all** paths.\n\n'
        "### Build\n\n- `just build target='wheel'` — Build a package."
    )


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("Available recipes:\n    check\n", "- `just check`"),
        ("Available recipes:\r\n    check # Works.\r\n", "- `just check` — Works."),
        ("Available recipes:\n    \x1b[32mcheck\x1b[0m\n", "- `just check`"),
        ("Available recipes:\n    show value='`example`'\n", "- ``just show value='`example`'``"),
        ("Available recipes:\n    [A *group*]\n    check\n", "### A \\*group\\*\n\n- `just check`"),
        ("Available recipes:\n check\n", "- `just check`"),
        ("Available recipes:\n    show [beta]\n", "- `just show [beta]`"),
    ],
)
def test_help_normalizes_terminal_formatting(output: str, expected: str) -> None:
    # Given help containing terminal presentation or Markdown-sensitive characters.
    parser = JustHelpParser()
    # When the help output is interpreted.
    result = parser.render(output)
    # Then the result is deterministic Markdown without terminal escapes.
    assert result == expected


@pytest.mark.parametrize(
    ("output", "message"),
    [
        ("", "Expected just help to print the standard just --list output."),
        ("Available recipes:\n", "just help did not list any available commands."),
        ("Custom help", "Expected just help to print the standard just --list output."),
        ("Available recipes:\ncheck", "Unsupported just help output: 'check'."),
        ("Available recipes:\n    [Empty]\n", "just help did not list any available commands."),
        ("Available recipes:\n    !invalid", "Unsupported just help recipe: '!invalid'."),
    ],
)
def test_unrecognized_help_fails_instead_of_inventing_commands(output: str, message: str) -> None:
    # Given output outside the supported just list convention.
    parser = JustHelpParser()
    # When the built-in tries to interpret it.
    with pytest.raises(GenerationError) as failure:
        parser.render(output)
    # Then an actionable error is raised instead of publishing an incorrect manifest.
    assert str(failure.value) == message
