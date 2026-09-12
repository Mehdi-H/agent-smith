"""Pure parsing of declared tools, independent of mise or the host environment."""

import pytest

from agent_smith.adapters.mise import MiseTechStackParser
from agent_smith.application.ports import GenerationError


@pytest.mark.parametrize(
    ("declaration", "expected"),
    [
        ('python = "3.14"', "- `python` — `3.14`"),
        ('python = ["3.14", "3.10"]', "- `python` — `3.14`, `3.10`"),
        ('node = { version = "lts", postinstall = "never execute" }', "- `node` — `lts`"),
        ('node = [{version = "22"}, {version = "24"}]', "- `node` — `22`, `24`"),
        ('"github:org/tool" = "latest"', "- `github:org/tool` — `latest`"),
        ('"a`b" = "ref:main"', "- ``a`b`` — `ref:main`"),
        ('python = "{{env.VERSION}}"', "- `python` — `{{env.VERSION}}`"),
    ],
)
def test_supported_tool_declarations(declaration: str, expected: str) -> None:
    # Given a supported declaration whose values must remain literal.
    content = "[tools]\n" + declaration
    # When the pure parser renders it.
    result = MiseTechStackParser().render(content)
    # Then the tool and declared versions appear in one Markdown bullet.
    assert result == expected


def test_preserves_declaration_order_and_ignores_other_tables() -> None:
    # Given tools in deliberate order and unrelated environment and task values.
    content = (
        '[env]\nTOKEN = "not-for-output"\n[tools]\nuv = "latest"\npython = "3.14"\n'
        '[tasks.build]\nrun = "never execute"\n'
    )
    # When the same content is parsed repeatedly.
    first = MiseTechStackParser().render(content)
    second = MiseTechStackParser().render(content)
    # Then only tools appear, in their source order, with byte-identical Markdown.
    assert first == second == "- `uv` — `latest`\n- `python` — `3.14`"


@pytest.mark.parametrize(
    "content",
    [
        "[broken",
        "",
        "[tools]",
        'tools = "bad"',
        "[tools]\npython = 3",
        "[tools]\npython = true",
        "[tools]\npython = []",
        '[tools]\npython = ""',
        '[tools]\npython = {os = "linux"}',
        '[tools]\npython = {version = ["3.14"]}',
        '[tools]\npython = [["3.14"]]',
        '[tools]\n"bad\\nname" = "1"',
        '[tools]\npython = "bad\\nversion"',
    ],
)
def test_invalid_tools_report_actionable_errors(content: str) -> None:
    # Given malformed TOML, an empty tools table or an unsupported declaration.
    parser = MiseTechStackParser()
    # When rendering is requested.
    with pytest.raises(GenerationError) as error:
        parser.render(content)
    # Then the parser returns a diagnostic instead of inventing a version.
    assert str(error.value)
