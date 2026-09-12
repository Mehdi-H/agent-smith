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
            "> [!NOTE]\n> Hello",
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


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("![logo](logo.png)\n\nIntro", "Intro"),
        ('Before ![a](image(a).png "title") after', "Before  after"),
        ("[![CI](badge.svg)](https://ci)\n\nIntro", "Intro"),
        ('<IMG src="logo.png" alt="Logo > text" />\n\nIntro', "Intro"),
        ('<img\n src="logo.png"\n>\n\nIntro', "Intro"),
        ('<a href="https://ci"><img src="badge.svg"></a>\n\nIntro', "Intro"),
        ("[![icon](icon.png) Documentation](docs.md)", "[ Documentation](docs.md)"),
        ("![Logo][image]\n\nIntro\n\n[image]: logo.png", "Intro"),
        (
            "![Logo][image]\n\n[Download][image]\n\n[image]: logo.png",
            "[Download][image]\n\n[image]: logo.png",
        ),
        ("[![CI][badge]][ci]\n\nIntro\n\n[badge]: badge.svg\n[ci]: https://ci", "Intro"),
        (
            '`![example](image.png)` and `<img src="example">`',
            '`![example](image.png)` and `<img src="example">`',
        ),
        (
            '```md\n![example](image.png)\n<img src="example">\n```',
            '```md\n![example](image.png)\n<img src="example">\n```',
        ),
        ("    ![example](image.png)\n\nIntro", "    ![example](image.png)\n\nIntro"),
        ("\\![literal](image.png)\n\nIntro", "\\![literal](image.png)\n\nIntro"),
        ('<!-- <img src="hidden"> -->\n\nIntro', '<!-- <img src="hidden"> -->\n\nIntro'),
        ("**Intro** with [documentation](docs.md).", "**Intro** with [documentation](docs.md)."),
    ],
)
def test_overview_removes_rendered_images_and_preserves_text(body: str, expected: str) -> None:
    # Given prose mixed with rendered images or literal code examples.
    parser = MarkdownOverviewParser()
    # When the overview is projected into agent instructions.
    result = parser.extract(f"# Project\n\n{body}\n\n## Usage")
    # Then visual-only content disappears without reformatting the remaining prose.
    assert result == expected


def test_image_only_overview_is_empty_after_sanitization() -> None:
    # Given an overview containing only a linked badge.
    parser = MarkdownOverviewParser()
    # When its visual-only content is removed.
    with pytest.raises(GenerationError) as failure:
        parser.extract("# Project\n\n[![CI](badge.svg)](https://ci)\n\n## Usage")
    # Then the existing empty-overview convention remains enforced.
    assert "empty" in str(failure.value)
