"""A compact ADR index is built from paths, never from decision contents."""

import pytest

from agent_smith.adapters.adr import AdrListParser
from agent_smith.application.ports import GenerationError


def test_directory_is_printed_once_with_extensionless_filenames_in_source_order() -> None:
    # Given the .adr-dir contents and the exact ordered output of adr list.
    directory = "docs/adr\n"
    listing = "docs/adr/0002-use-python.md\ndocs/adr/0001-record-decisions.md\n"
    # When the list is condensed into Markdown.
    result = AdrListParser().render(directory, listing)
    # Then directory prefixes and extensions are omitted from bullets without rewriting titles.
    assert result == ("Directory: `docs/adr`\n\n- `0002-use-python`\n- `0001-record-decisions`")
    assert result.count("docs/adr") == 1


@pytest.mark.parametrize(
    ("directory", "listing", "expected"),
    [
        ("./docs/adr\r\n", "docs/adr/0001-use-python.md\r\n", "0001-use-python"),
        ("decisions", "decisions/0001-name.md.extra.md\n", "0001-name.md.extra"),
        ("decisions", "\ndecisions/0001-use `code`.md\n", "0001-use `code`"),
        ("docs/my decisions", "docs/my decisions/0001-use-python.md\n", "0001-use-python"),
    ],
)
def test_literals_and_line_endings_are_preserved_safely(
    directory: str, listing: str, expected: str
) -> None:
    # Given a filename that may contain Markdown punctuation or multiple suffixes.
    parser = AdrListParser()
    # When the output is rendered.
    result = parser.render(directory, listing)
    # Then only the final .md is stripped and content remains stable across repeated calls.
    assert expected in result
    assert result == parser.render(directory, listing)


@pytest.mark.parametrize(
    ("directory", "listing", "message"),
    [
        ("", "docs/adr/0001-test.md", ".adr-dir must contain a nonempty directory on one line."),
        (
            "docs/adr\nother",
            "docs/adr/0001-test.md",
            ".adr-dir must contain a nonempty directory on one line.",
        ),
        ("docs/adr", "", "adr list returned no architecture decisions."),
        ("docs/adr", " \n", "adr list returned no architecture decisions."),
        (
            "docs/adr",
            "Command failed",
            "Unexpected adr list path 'Command failed' for directory 'docs/adr'.",
        ),
        (
            "docs/adr",
            "other/0001-test.md",
            "Unexpected adr list path 'other/0001-test.md' for directory 'docs/adr'.",
        ),
        (
            "docs/adr",
            "docs/adr/0001-test.txt",
            "Unexpected adr list path 'docs/adr/0001-test.txt' for directory 'docs/adr'.",
        ),
        (
            "docs/adr",
            "docs/adr/0001-\tbad.md",
            "ADR filenames must be nonempty and on one line.",
        ),
    ],
)
def test_invalid_metadata_and_command_output_fail(
    directory: str, listing: str, message: str
) -> None:
    # Given malformed metadata or a listing inconsistent with its declared directory.
    parser = AdrListParser()
    # When the parser validates it.
    with pytest.raises(GenerationError) as failure:
        parser.render(directory, listing)
    # Then an actionable diagnostic is provided.
    assert str(failure.value) == message
