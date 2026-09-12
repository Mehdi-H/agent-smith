# 30. Exclude images and badges from generated README overviews

Date: 2026-09-13

## Status

Accepted

Supercedes [13. Extract README overviews with CommonMark source boundaries](0013-extract-readme-overviews-with-commonmark-source-boundaries.md)

## Context

The maintainer wants README illustrations and badges for humans, but their image
markup, alternative text and badge targets add irrelevant characters to an
agent's initial instructions. Previously the overview preserved this markup.

## Decision

Keep the CommonMark H1-to-H2 boundaries from ADR 13, but remove rendered Markdown
images (including reference images), HTML img tags, and links containing only
images from the built-in overview. Remove reference definitions made unused by
these deletions. Preserve text-bearing links, ordinary prose and literal code.
Do not modify README.md or custom extractor output.

Use the existing markdown-it-py inline rules to identify source spans, protecting
fenced and indented code blocks. Delete spans rather than re-render Markdown.
Keep meaningful source formatting and the existing empty-overview error after
sanitization. This is content minimization, not a general HTML security sanitizer.

Regular expressions alone were considered but do not handle nested destinations,
references and code reliably. Rendering all content to another format was not
selected because it would change unrelated Markdown. No comparative benchmark
was performed.

## Consequences

Agent instructions contain fewer decorative tokens. Image-only overviews now
fail as empty; projects must supply textual instructions or a custom extractor.
Code examples intentionally retain literal image syntax. The README can keep its
badges and illustrations, and the generated overview stays deterministic.
