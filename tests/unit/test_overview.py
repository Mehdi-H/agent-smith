"""Markdown boundaries are tested in memory, including misleading headings."""

import pytest

from agent_smith.adapters.markdown import MarkdownOverviewParser
from agent_smith.application.ports import GenerationError


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("# Project\n\nIntroduction.\n\n## Usage\nExcluded", "Introduction."),
        ("# Project\nIntroduction.", "Introduction."),
        ("# Project\n\n  **Keep this**  \n\n## Usage", "  **Keep this**  "),
        ("Project\n=======\n\nIntro\n\nUsage\n-----\nNo", "Intro"),
        ("  # Project ###\n\nIntro\n\n  ## Usage ##", "Intro"),
        ("# Project\n\n```md\n## Code\n```\n\n## Usage", "```md\n## Code\n```"),
        ("# Project\n\n~~~\n# Code\n## Code\n~~~\n\n## Usage", "~~~\n# Code\n## Code\n~~~"),
        ("# Project\n\n    ## Code\n\n## Usage", "    ## Code"),
        ("# Project\n\n> ## Quote\n\nIntro\n\n## Usage", "> ## Quote\n\nIntro"),
        ("# Project\n\n- ## List\n\n## Usage", "- ## List"),
        ("# Project\n\n<!--\n## Hidden\n-->\n\nIntro\n\n## Usage", "<!--\n## Hidden\n-->\n\nIntro"),
        ("# Project\n\n### Detail\nKeep\n\n## Usage", "### Detail\nKeep"),
        ("# Project\n\n##not-heading\n\n## Usage", "##not-heading"),
        ("# Project\r\n\r\nCafé 🕶️\r\n\r\n## Usage", "Café 🕶️"),
        ("\ufeff# Project\nIntro\n## Usage", "Intro"),
        ("Before\n\n## Earlier\n\n# Project\nIntro\n## Usage", "Intro"),
        (
            "# Project\n\n[![CI](badge.svg)](url)\n\n> [!NOTE]\n> Hello\n\n## Usage",
            "[![CI](badge.svg)](url)\n\n> [!NOTE]\n> Hello",
        ),
    ],
)
def test_extracts_only_overview_source(source: str, expected: str) -> None:
    # Given Markdown containing genuine or misleading heading boundaries.
    parser = MarkdownOverviewParser()
    # When the built-in extractor locates the overview.
    result = parser.extract(source)
    # Then only the requested source is returned without reformatting its body.
    assert result == expected


@pytest.mark.parametrize(
    "source",
    [
        "",
        "No heading",
        "## Only H2",
        "> # Quoted\nIntro",
        "```\n# Code\n```",
        "# Empty\n\n## Usage",
        "# Empty",
        "# One\nIntro\n# Two\nOther",
    ],
)
def test_invalid_overviews_report_a_domain_error(source: str) -> None:
    # Given a document without an unambiguous nonempty overview.
    parser = MarkdownOverviewParser()
    # When extraction is requested.
    with pytest.raises(GenerationError) as failure:
        parser.extract(source)
    # Then the error describes the README convention.
    assert "README" in str(failure.value)
