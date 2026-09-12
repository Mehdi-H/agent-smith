# 19. Generate the main tech stack from declared mise tools

Date: 2026-09-12

## Status

Accepted

## Context

The project owner wants a Main tech stack section containing Markdown bullets
extracted automatically from mise.toml. Generation must remain deterministic and
usable without asking consumers to implement a Python extractor.

## Decision

Detect a root mise.toml and read its [tools] table through an injected
TechStackParser port and a pure MiseTechStackParser adapter. Reuse the existing
TOML support (tomllib, or tomli on Python 3.10); no dependency is added.

Render one bullet per tool, preserving tool names, declared versions and source
order. Support version strings, arrays, and tables with a string version field,
including arrays of tables. Ignore installation options and other TOML sections.
Keep aliases and templates literal: do not execute mise, evaluate templates,
run hooks, resolve versions, or merge global and environment configuration.

Place the section after Overview and before Available commands and custom sections. Allow
--no-tech-stack and [tech_stack] enabled/title/source settings, following the
existing configuration precedence. With no source file the convention is inactive;
explicit enabled=true requires the source. Invalid or empty tools declarations
produce a diagnostic, and generation leaves the previous output untouched.
Reject output paths that would overwrite the selected source. The provenance
footer uses the actual agent-smith invocation, including CLI arguments.

Direct parsing meets the requested need and isolates the extractor from filesystem
and process effects. Calling mise to query its resolved configuration and using a
custom shell extractor were known alternatives; no comparative benchmark was run.
Tests cover parsing rules with direct unit tests, real configuration files at the
integration level, and a few installed-CLI scenarios without runtime replacement.

## Consequences

The result describes declared tools, not necessarily installed versions or the
entire application stack. Tools declared only in other files are not inferred.
Unsupported version structures fail explicitly rather than fabricating a value;
additional mise forms can be supported later as concrete needs arise. Consumers
can disable or replace the built-in with a custom section.

Reference: [mise configuration](https://mise.jdx.dev/configuration.html).
