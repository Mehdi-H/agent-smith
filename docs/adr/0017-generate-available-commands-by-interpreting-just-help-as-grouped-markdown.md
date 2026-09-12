# 17. Generate Available commands by interpreting just help as grouped Markdown

Date: 2026-09-12

## Status

Accepted

## Context

The project owner wants a second built-in section describing available project
commands, sourced from `just help`, and selected a Markdown list organized by
group. The project's justfile is its self-documented usage manifest.

## Decision

Detect a root justfile (case-insensitive justfile or .justfile) and enable an
Available commands section after Overview, before custom sections. Projects
without one retain README-only behavior and do not need just installed.

Run `just help` via the existing command-runner port, with its existing timeout
and failure handling. Interpret standard `just --list` output through a HelpParser
port and a JustHelpParser adapter. Preserve ordering, group names, signatures
including parameter defaults, and descriptions. Render groups as H3 headings
and recipes as Markdown bullets prefixed with `just`. Strip ANSI color sequences
and normalize line endings. Preserve Markdown in descriptions and escape code
spans and group headings. Ungrouped recipes remain bullets without an invented
group. The footer names the exact source command, defaulting to `just help`.

Users should document and group their root justfile recipes and provide a help
recipe delegating to `just --list`. The built-in does not execute listed recipes.
The help recipe itself is executable project code and must be trusted.

`--no-available-commands` disables this section. `[available_commands]` supports
`enabled`, `title` and `command`; an explicit boolean overrides detection and the
CLI disable flag takes precedence. An explicit enablement requires a working
source even without a detected justfile. Other formats can use the existing
custom Markdown command sections. An unavailable command, failed command, empty
list or unsupported help format fails without replacing the existing document.

We considered embedding raw terminal output, but the user selected grouped
Markdown. Using just's JSON dump would provide a structured source, but it would
bypass the requested help recipe. No comparative benchmark was conducted. No
new runtime dependency is required.

## Consequences

The public README documents the root README and justfile conventions and includes
a complete help example. Tests use direct parser calls, injected collaborators
and a few real justfile CLI scenarios, without patching.

The parser supports the standard human-readable recipe listing, not arbitrary
help prose, customized list prefixes, or terminal UI layouts. Unsupported output
is diagnosed rather than silently turned into an incorrect command manifest.
The recipe order and descriptions remain project-controlled; deterministic
output assumes deterministic help output.

Reference: [Just listing conventions](https://just.systems/man/en/listing-available-recipes.html)
and [recipe groups](https://just.systems/man/en/groups.html).
