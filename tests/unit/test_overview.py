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
        ("# Project\rIntro\r## Usage", "Intro"),
        ("# Project\r\n\r\nA\r\n\r\nB\r\n\r\n## Usage", "A\n\nB"),
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
    ("source", "message"),
    [
        ("", "README overview requires a top-level Markdown H1."),
        ("No heading", "README overview requires a top-level Markdown H1."),
        ("## Only H2", "README overview requires a top-level Markdown H1."),
        ("> # Quoted\nIntro", "README overview requires a top-level Markdown H1."),
        ("```\n# Code\n```", "README overview requires a top-level Markdown H1."),
        ("# Empty\n\n## Usage", "README overview is empty between its H1 and first H2."),
        ("# Empty", "README overview is empty between its H1 and first H2."),
        (
            "# One\nIntro\n# Two\nOther",
            "README has another H1 before its first overview-ending H2.",
        ),
    ],
)
def test_invalid_overviews_report_a_domain_error(source: str, message: str) -> None:
    # Given a document without an unambiguous nonempty overview.
    parser = MarkdownOverviewParser()
    # When extraction is requested.
    with pytest.raises(GenerationError) as failure:
        parser.extract(source)
    # Then the error describes the README convention.
    assert str(failure.value) == message


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
        (
            "    a\n" * 8 + "\ntext\n\n    ![x](y.png)\n\nIntro",
            "    a\n" * 8 + "\ntext\n\n    ![x](y.png)\n\nIntro",
        ),
        ("\\![literal](image.png)\n\nIntro", "\\![literal](image.png)\n\nIntro"),
        ('<!-- <img src="hidden"> -->\n\nIntro', '<!-- <img src="hidden"> -->\n\nIntro'),
        ("**Intro** with [documentation](docs.md).", "**Intro** with [documentation](docs.md)."),
        ("[ ](url)\n\nIntro", "Intro"),
        ("[<br>](url)\n\nIntro", "[<br>](url)\n\nIntro"),
        ('[<img src="i.png">](url)\n\nIntro', "Intro"),
        (
            '<a href="x"><img src="i.png"> caption</a>\n\nIntro',
            '<a href="x"> caption</a>\n\nIntro',
        ),
        ("~~~\n![a](b.png)\n~~~\n\nIntro", "~~~\n![a](b.png)\n~~~\n\nIntro"),
        ("```\nx\n```\n![a](b.png)\n\nIntro", "```\nx\n```\n\n\nIntro"),
        (
            "```\nl0\nl1\nl2\nl3\nl4\nl5\nl6\nl7\nl8\nl9\nl10\nl11\nl12\n```\n\n```\n![x](y.png)\n```\n\nIntro",
            "```\nl0\nl1\nl2\nl3\nl4\nl5\nl6\nl7\nl8\nl9\nl10\nl11\nl12\n```\n\n```\n![x](y.png)\n```\n\nIntro",
        ),
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
    assert str(failure.value) == "README overview is empty between its H1 and first H2."
