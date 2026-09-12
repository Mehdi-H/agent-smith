# 8. Use skill-validator to validate local skill structure

Date: 2026-09-12

## Status

Accepted

## Context

The repository already contains commit and ADR skills. Their format needs a
repeatable feedback check alongside code checks. The maintainer proposed
[skill-validator](https://github.com/agent-ecosystem/skill-validator), and its
local structure command passes on both existing skills.

This records the selected tool retrospectively. The Agent Skills specification
also identifies [skills-ref](https://agentskills.io/specification#validation) as
a reference validator for frontmatter and naming. We identified that alternative
but did not execute a comparative evaluation or benchmark against it.

## Decision

Use skill-validator, pinned in mise.toml, through `just skills-check` and include
it in `just check`. Run `validate structure --strict` against `.agents/skills`
by default, with an optional path for individual skills or other collections.
Use the shared feedback wrapper for silent exit 0 or exit 1 with diagnostics.

## Consequences

Metadata and local structural problems receive executable feedback, including
warnings promoted to failures. Contributors install an additional development
binary through mise; the distributed Python package gains no dependency.

The check excludes remote URL validation and LLM scoring. The validator includes
additional conventions and heuristics beyond the format's required fields, so a
failure is not necessarily a specification violation. Review remains necessary
for the correctness and usefulness of the instructions.
