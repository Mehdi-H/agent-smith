# 14. Generate Markdown through command and document ports

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer wants useful built-in extractors as well as custom sections from
user-defined commands. The first built-in is README overview, active without
configuration. Argparse and effectful adapters must remain replaceable without
changing generation rules.

We initially considered exposing a separate overview producer command. The
maintainer clarified that a built-in plus optional user configuration is the
desired interface. TOML fits Python tooling; YAML and JSON were identified but
not evaluated. No numeric test quota or benchmark determined this architecture.

## Decision

Use typed incoming Configuration and Generator protocols and outgoing reader,
overview parser, command runner and document writer protocols. Wire concrete
adapters only in the composition root. Unit tests supply in-memory ports.

Load optional `agent-smith.toml` from the invocation directory or an explicit
`--config` path. CLI `--output` overrides config, then defaults to `AGENTS.md`.
`--no-overview` disables the built-in; `[overview].enabled = false` does the same
in config. Append custom `[[sections]]` in declared order, with title and command.
Reject unknown settings and empty or multiline titles/commands. Resolve paths
and execute commands relative to the invocation directory.

Render an H1 with the output filename and an H2 per section. Built-in provenance
includes the `agent-smith` invocation with shell-quoted CLI arguments, supplied
by the CLI adapter through the generation request. This command regenerates the
whole document using the same configuration and working directory. Custom
provenance includes the exact configured command. Preserve body Markdown,
normalize line endings, and end the
document with one newline. Identical requests and extractor outputs must produce
identical bytes; commands that vary their output cannot be made deterministic.

Prepare all sections before an atomic file replacement. Errors return exit 1
and a diagnostic without replacing an existing document. Use the platform shell
for explicitly configured commands, with a 30-second timeout and UTF-8 stdout.
Use stdlib tomllib on Python 3.11+ and conditionally depend on tomli for Python
3.10. Configure a DEP001 exception for tomllib: deptry running on 3.10 scans the
version-guarded import even though that branch cannot execute on 3.10. Other
missing-dependency checks remain enabled. This avoids installing a TOML backport
on runtimes that already provide one. Keep configuration examples within TOML
1.0 syntax supported by every runtime; CI exercises the actual imports and files.

## Consequences

Users can generate an overview immediately, replace it, or append arbitrary
command-backed sections without writing Python. Custom commands are executable
configuration and run with the user's permissions; users must trust them.
Their own side effects are outside the document writer's atomicity guarantee.

No Markdown formatter, extractor plugin registry or release automation is added.
Output parent directories must already exist. Filesystem replacement and shell
semantics remain adapter concerns. The pre-commit startup check now uses `--help`
to avoid generating repository instructions as a side effect of committing.
