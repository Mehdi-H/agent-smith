---
name: adr
description: Create, list, supersede, and edit architecture decisions with adr-tools in this repository.
---

Introduce each ADR with the PR implementing its decision. Add tooling to
mise.toml or pyproject.toml only when that PR uses it.

Use adr-tools through the documented just recipe for structural operations:
- `just adr list` to list decisions.
- `just adr new "Decision title"` to create a decision.
- `just adr new -s NUMBER "Replacement decision"` to supersede a decision.
- `just adr init docs/adr` only when initializing a new decision log.

Never manually create or number ADRs, list them through shell globbing, or update
supersession links by hand. The CLI already supplies the Nygard template. For
noninteractive creation, set `VISUAL=true EDITOR=true` when invoking the recipe.
After the CLI creates a document, use normal editing tools to fill its content.

Keep the template's status, context, decision, and consequences. Explain the
tradeoff and useful alternatives concisely. Distinguish accepted decisions from
unresolved proposals. Preserve superseded decisions.
