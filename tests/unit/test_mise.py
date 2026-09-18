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
        ('python = "3.14 rc 1"', "- `python` — `3.14 rc 1`"),
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
    ("content", "message"),
    [
        ("[broken", "Invalid mise TOML"),
        ("", "Expected a nonempty [tools] table in mise.toml."),
        ("[tools]", "Expected a nonempty [tools] table in mise.toml."),
        ('tools = "bad"', "Expected a nonempty [tools] table in mise.toml."),
        ("[tools]\npython = 3", "tools.python.version must be a nonempty, single-line string."),
        ("[tools]\npython = true", "tools.python.version must be a nonempty, single-line string."),
        ("[tools]\npython = []", "tools.python must declare at least one version."),
        ('[tools]\npython = ""', "tools.python.version must be a nonempty, single-line string."),
        (
            '[tools]\npython = {os = "linux"}',
            "tools.python.version must be a nonempty, single-line string.",
        ),
        (
            '[tools]\npython = {version = ["3.14"]}',
            "tools.python.version must be a nonempty, single-line string.",
        ),
        (
            '[tools]\npython = [["3.14"]]',
            "tools.python.version must be a nonempty, single-line string.",
        ),
        (
            '[tools]\npython = ["3.14", 3]',
            "tools.python.version must be a nonempty, single-line string.",
        ),
        ('[tools]\n"bad\\nname" = "1"', "Tool name must be a nonempty, single-line string."),
        (
            '[tools]\npython = "bad\\nversion"',
            "tools.python.version must be a nonempty, single-line string.",
        ),
    ],
)
def test_invalid_tools_report_actionable_errors(content: str, message: str) -> None:
    # Given malformed TOML, an empty tools table or an unsupported declaration.
    parser = MiseTechStackParser()
    # When rendering is requested.
    with pytest.raises(GenerationError) as failure:
        parser.render(content)
    # Then the parser returns a diagnostic instead of inventing a version.
    assert str(failure.value).startswith(message)
