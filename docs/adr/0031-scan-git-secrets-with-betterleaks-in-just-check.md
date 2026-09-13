# 31. Scan Git secrets with Betterleaks in just check

Date: 2026-09-13

## Status

Accepted

## Context

The maintainer wants feedback before credentials or other secrets are committed by
mistake. The check must use the existing silent-success feedback contract and run
in local pre-commit hooks as well as the CI matrix.

## Decision

Pin Betterleaks 1.8.1 from its GitHub releases in mise.toml and expose
`just secrets-check` in the Quality group. Scan the complete Git history so CI
detects committed secrets, then scan the staged pre-commit diff so the local hook
detects them before a commit is created. Redact findings and generate GitHub links.
Use verbose, redacted output so diagnostics identify the rule and file without
revealing the value. Set the leak exit code explicitly to 1 so findings always
fail the feedback check.

Run both scans through the shared feedback wrapper and include the recipe in
`just check`. Use Betterleaks' built-in rules without live validation or local
suppressions. The initial history scan found no leaks and took about two seconds
on the current repository.

Gitleaks was identified as an alternative, but no comparative evaluation or
benchmark was performed. Betterleaks was explicitly requested.

## Consequences

Committed history and locally staged changes now receive secret-scanning feedback
in the same command used by pre-commit and CI. Successful scans stay silent;
findings fail with redacted diagnostics and remediation guidance.

The history scan adds about two seconds to each current `just check` invocation.
Pattern matching can produce false positives or miss unknown secret formats, so
the check complements careful review rather than replacing it. Findings require
removal and credential rotation; history already shared remotely may need further
incident response.
