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

Default to retrospective documentation of a decision already made. Record the
actual reason: an explicit project preference, familiarity, or a tool meeting the
need can be sufficient. Do not invent evaluations, benchmarks, rejected options,
advantages, or disadvantages to fill the template.

Keep the template's status, context, decision, and consequences concise. When
nothing further is known, say so instead of adding filler. List relevant known
alternatives available at the decision date, distinguishing those merely
identified from those actually evaluated. Explicitly say when no comparative
study or benchmark was performed. Do not turn retrospective documentation into
an unrequested technology survey or retroactively justify the choice as optimal.

When explicitly asked to evaluate an open decision, switch to evaluation: define
the needs and constraints, compare plausible options against them, and record the
evidence and remaining uncertainty. Do not default to the first familiar tool.
Keep the status proposed until the decision is made. Preserve superseded records.
