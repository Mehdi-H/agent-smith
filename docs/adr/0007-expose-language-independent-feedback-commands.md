# 7. Expose language-independent feedback commands

Date: 2026-09-12

## Status

Accepted

## Context

Agents need both guidance before acting and clear feedback after acting. Native tools differ in output verbosity and failure exit codes. The repository must not require Java, Rust or other consumers to write Python scripts just to expose project commands.

This records the requested feedback contract. A Python interface, reusable shell functions and just-only composition were discussed as possible approaches. The shell wrapper was implemented to exercise the process contract; no comparative implementations or benchmarks were produced.

## Decision

Define feedback as a process contract: a completed successful check returns 0 with empty stdout and stderr; an unsuccessful or incomplete check returns 1 with actionable diagnostics on stderr. Use a small POSIX shell wrapper that accepts a command and its arguments, captures output, and preserves native diagnostics and the original exit code in the failure message. Document recipes in just, which suppresses command echo. Commands may invoke any language. Use composition rather than inheritance or a Python Tool base class.

## Consequences

Just can display its own failure context after the wrapper fails. Native codes such as 2 or 127 become 1 at the feedback boundary but remain visible in diagnostics. Reports are still written to files on successful tests. Setup, formatting and artifact production are operations, not feedback checks, and may print progress. Section producers in the future generator must keep stdout as their Markdown content; the feedback wrapper must not be applied to them. A POSIX shell is a requirement of this repository harness, not of the distributed Python package; native Windows harness support must be verified with the CI increment.

Reference: https://martinfowler.com/articles/harness-engineering.html
