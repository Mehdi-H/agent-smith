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


Choose a title that explicitly states the decision, not merely its topic or the
question discussed. The title and CLI-generated filename will form a compact
feedforward index in AGENTS.md: an agent should understand the chosen direction
without opening every ADR, and read the body only when it needs the rationale.

Name the selected tool, policy or architectural boundary, with its relevant
scope. Prefer "Use uv to manage Python and dependencies" over "Python tooling",
and "Use Python 3.14 for development" over "Python version". Include a version
when the version itself is the decision; do not invent one or confuse the local
development version with the supported runtime range. Include a patch version
only if that exact patch is what the decision selects. Keep the title concise,
concrete and understandable on its own; leave alternatives and justification in
the body. Pass this title to `just adr new` so the filename carries the decision.

When a decision changes, use the CLI supersession workflow. Historical titles
must not be interpreted as current instructions without considering ADR status.

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
