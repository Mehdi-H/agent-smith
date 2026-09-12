"""Locate CommonMark headings while preserving the original Markdown body."""

from markdown_it import MarkdownIt

from agent_smith.application.generation import content_lines
from agent_smith.application.ports import GenerationError


class MarkdownOverviewParser:
    def extract(self, markdown: str) -> str:
        """Extract after the first top-level H1 and before the following H2."""
        markdown = markdown.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        start: int | None = None
        end = len(markdown.split("\n"))
        for token in MarkdownIt("commonmark").parse(markdown):
            if token.type != "heading_open" or token.level != 0 or token.map is None:
                continue
            if start is None:
                if token.tag == "h1":
                    start = token.map[1]
            elif token.tag == "h2":
                end = token.map[0]
                break
            elif token.tag == "h1":
                raise GenerationError("README has another H1 before its first overview-ending H2.")
        if start is None:
            raise GenerationError("README overview requires a top-level Markdown H1.")
        body = content_lines("\n".join(markdown.split("\n")[start:end]))
        if not body:
            raise GenerationError("README overview is empty between its H1 and first H2.")
        return body
