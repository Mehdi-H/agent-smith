# 21. Use ShellCheck for shell script feedback in just check

Date: 2026-09-12

## Status

Accepted

## Context

The project owner requested a feedback check for Bash and other shell scripts.
The repository's recorder and audit wrappers currently use POSIX sh.

## Decision

Pin ShellCheck in mise.toml and expose just shellcheck-check in the Quality group.
Recursively scan .sh and .bash files under scripts, respecting their shebangs.
Use all default diagnostic severities without suppressions. Run through the shared
feedback wrapper: silent exit 0 on success, exit 1 with native file/line/rule
diagnostics on failure. Include the recipe in just check, which already runs in
pre-commit and the CI matrix.

The initial scan found SC2155 in the recorder's PATH export. Separate assignment
from export so command-substitution errors are not masked by the export builtin.

ShellCheck was explicitly requested and meets this need. bash -n was a known
syntax-only alternative; it does not provide the same static diagnostics.
No comparative benchmark was performed.

## Consequences

Shell errors join the existing local feedback loop without network access.
New .sh/.bash files under scripts are discovered automatically. Other locations
or extensions need an explicit scope update; this check does not execute scripts.
