"""Locate CommonMark headings while preserving the original Markdown body."""

from markdown_it import MarkdownIt

from agent_smith.adapters.overview_images import without_images
from agent_smith.application.generation import content_lines
from agent_smith.application.ports import GenerationError


class MarkdownOverviewParser:
    def extract(self, markdown: str) -> str:
        """Extract after the first top-level H1 and before the following H2."""
        markdown = markdown.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
        environment = {}
        headings = [
            (token.tag, token.map)
            for token in MarkdownIt("commonmark").parse(markdown, environment)
            if token.type == "heading_open" and token.level == 0 and token.map is not None
        ]
        start, end = overview_bounds(headings, len(markdown.split("\n")))
        body = content_lines("\n".join(markdown.split("\n")[start:end]))
        body = content_lines(without_images(body, environment))
        if not body:
            raise GenerationError("README overview is empty between its H1 and first H2.")
        return body


def overview_bounds(headings: list[tuple[str, list[int]]], end: int) -> tuple[int, int]:
    first = next((index for index, (tag, _) in enumerate(headings) if tag == "h1"), None)
    if first is None:
        raise GenerationError("README overview requires a top-level Markdown H1.")
    start = headings[first][1][1]
    for tag, lines in headings[first + 1 :]:
        if tag == "h2":
            return start, lines[0]
        if tag == "h1":
            raise GenerationError("README has another H1 before its first overview-ending H2.")
    return start, end
