# 13. Extract README overviews with CommonMark source boundaries

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer requested a built-in overview extractor that reads the content
between a README's H1 and first following H2. Users should not need a script for
this common convention, while remaining free to disable or replace it.

Plain line matching was considered but cannot reliably distinguish headings
from code, quotes or HTML blocks. We choose markdown-it-py's CommonMark parser
for heading boundaries and line maps. We consulted its documentation and tested
representative inputs; no comparative library benchmark was performed.

## Decision

Use markdown-it-py behind the OverviewParser port. Extract the source after the
first top-level Markdown H1 and before the first following top-level H2. Support
ATX (`#`) and setext (underlined) headings. Nested headings and text inside code
or HTML blocks are not boundaries.

If no following H2 exists, use the remainder. Missing H1, another H1 before the
H2, or an empty overview produces an error. Preserve source Markdown, including
badges and alerts, while normalizing line endings and surrounding blank lines.
Do not render to HTML or reformat the extracted body.

## Consequences

The built-in extractor handles real Markdown boundaries without maintaining a
partial parser. The distributed CLI gains a markdown-it-py runtime dependency.
Its edge cases are tested without files or subprocesses.

Extraction does not rewrite relative links or copy reference definitions from
outside the selected region. Users can supply a custom extractor if their
README's layout or desired content differs from this convention. Raw HTML
headings are not CommonMark heading tokens and are not supported as boundaries.
