# 9. Use Lefthook to check repository quality and CLI startup before commits

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer requested Lefthook to run repository checks and the installed CLI
before every commit. Existing just recipes provide the operations interface and
the shared feedback wrapper keeps successful checks quiet.

This is retrospective documentation of that explicit preference. Known
alternatives include pre-commit and native Git hook scripts. We did not evaluate
or benchmark those alternatives.

## Decision

Use Lefthook, pinned in mise.toml, to run `just check` followed by `just cli-check`
on pre-commit. The latter runs `uv run --offline --no-sync agent-smith` without
arguments and fails if the installed command exits unsuccessfully.

Install hooks through `just hooks-install`, also called by `just setup`. Expose
`just hooks-check` for manual execution. Resolve hook tools through mise, and
retain Lefthook's visual summary plus detailed diagnostics on failure.

## Consequences

Each local commit gets quality feedback and a CLI startup check. Contributors
must install hooks per checkout and expose mise on the PATH used by Git,
including when committing from an IDE. Checks use the working tree rather than
an isolated copy of staged files. They do not format or stage changes.

The CLI currently displays help without arguments; this verifies startup, not
generation correctness. Revisit that smoke check when generation is introduced.
Local hooks can be bypassed and do not replace future CI checks.
