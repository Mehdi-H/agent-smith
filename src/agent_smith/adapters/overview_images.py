"""Remove rendered images using CommonMark rules and source spans, without reformatting prose."""

import re
from collections.abc import MutableMapping
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline, html_inline, image, link
from markdown_it.token import Token

ANCHOR = re.compile(r"<a(?:\s|>)", re.IGNORECASE)
IMG = re.compile(r"<img(?:\s|/?>)", re.IGNORECASE)


def image_only(tokens: list[Token]) -> bool:
    children = tokens[
        next(i for i, token in enumerate(tokens) if token.type == "link_open") + 1 : -1
    ]
    return bool(children) and all(
        token.type == "image"
        or (token.type == "text" and not token.content.strip())
        or (token.type == "html_inline" and IMG.match(token.content))
        for token in children
    )


class ImageSpans:
    def __init__(self, source: str, protected: list[tuple[int, int]]) -> None:
        self.source = source
        self.protected = protected
        self.spans: list[tuple[int, int]] = []
        self.anchors: list[tuple[int, int, int]] = []

    def record(self, state: StateInline, start: int, silent: bool) -> None:
        if silent or state.src != self.source:
            return
        if any(left <= start < right for left, right in self.protected):
            return
        self.spans.append((start, state.pos))

    def image(self, state: StateInline, silent: bool) -> bool:
        start = state.pos
        matched = image(state, silent)
        if matched:
            self.record(state, start, silent)
        return matched

    def link(self, state: StateInline, silent: bool) -> bool:
        start, count = state.pos, len(state.tokens)
        matched = link(state, silent)
        if matched and not silent and image_only(state.tokens[count:]):
            self.record(state, start, silent)
        return matched

    def html(self, state: StateInline, silent: bool) -> bool:
        start = state.pos
        matched = html_inline(state, silent)
        if matched and IMG.match(state.src[start : state.pos]):
            self.record(state, start, silent)
        if matched and not silent and state.src == self.source:
            self.anchor(state, start)
        return matched

    def anchor(self, state: StateInline, start: int) -> None:
        tag = state.src[start : state.pos]
        if ANCHOR.match(tag):
            self.anchors.append((start, state.pos, len(self.spans)))
        elif tag.lower() == "</a>" and self.anchors:
            opening, content, count = self.anchors.pop()
            inner = [(left - content, right - content) for left, right in self.spans[count:]]
            if inner and not remove_spans(self.source[content:start], inner).strip():
                self.record(state, opening, False)


def code_spans(parser: MarkdownIt, source: str) -> list[tuple[int, int]]:
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return [
        (offsets[token.map[0]], offsets[token.map[1]])
        for token in parser.parse(source)
        if token.type in {"fence", "code_block"} and token.map is not None
    ]


def remove_spans(source: str, spans: list[tuple[int, int]]) -> str:
    result, cursor = [], 0
    for start, end in sorted(spans):
        if start >= cursor:
            result.append(source[cursor:start])
        cursor = max(cursor, end)
    result.append(source[cursor:])
    return "".join(result)


def without_images(source: str, environment: MutableMapping[str, Any]) -> str:
    parser = MarkdownIt("commonmark")
    capture = ImageSpans(source, code_spans(parser, source))
    parser.inline.ruler.at("image", capture.image)
    parser.inline.ruler.at("link", capture.link)
    parser.inline.ruler.at("html_inline", capture.html)
    parser.inline.parse(source, parser, environment, [])
    cleaned = remove_spans(source, capture.spans)
    return without_unused_image_references(source, cleaned)


def reference_labels(tokens: list[Token]) -> set[str]:
    labels = set()
    for token in tokens:
        if "label" in token.meta:
            labels.add(token.meta["label"])
        labels.update(reference_labels(token.children or []))
    return labels


def without_unused_image_references(source: str, cleaned: str) -> str:
    parser = MarkdownIt("commonmark", {"store_labels": True})
    original = reference_labels(parser.parse(source))
    environment: dict[str, Any] = {}
    retained = reference_labels(parser.parse(cleaned, environment))
    offsets = [0]
    for line in cleaned.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    references = environment.get("references", {})
    spans = [
        (offsets[references[label]["map"][0]], offsets[references[label]["map"][1]])
        for label in original - retained
        if label in references
    ]
    return remove_spans(cleaned, spans)
