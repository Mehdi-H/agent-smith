# Contributing

Install [mise](https://mise.jdx.dev/), then run `mise trust` and `mise install`.
Activate mise in your shell or prefix commands with `mise exec --`.
Run `just` to discover documented operations.

Use short descriptive branch names without a `codex/` prefix. Keep commits atomic
and follow the [commit skill](.agents/skills/commit/SKILL.md): Conventional Commits,
an emoji at the end of the subject, and no agent co-author trailers.

Add tools, recipes, tests and ADRs in the PR that introduces their use. Follow the
[ADR skill](.agents/skills/adr/SKILL.md) for structural operations on decisions.
The optional `.editorconfig` conventions keep indentation, encoding and line
endings consistent across editors.

## Acknowledgements

The commit skill was inspired by the
[Cinematch commit helper](https://github.com/umans-ai/cinematch/blob/main/.claude/skills/commit/SKILL.md)
from umans-ai and adapted to Agent Smith's conventions.
