# 22. Index architecture decisions with adr list and compact filenames

Date: 2026-09-12

## Status

Accepted

## Context

The project owner wants agents to see the project's architectural decisions at
startup without loading every ADR. Repeating full paths and extensions wastes
context space; semantic filenames already summarize each decision.

## Decision

Detect a root .adr-dir and add Architecture decisions after Available commands,
before custom sections. Read .adr-dir once to display its directory, then execute
adr list through the existing command port. Interpret the output behind an
injected DecisionListParser port. Never read the individual ADR files.

Render the directory once and one Markdown bullet per filename, removing its
path prefix and final .md extension. Preserve numbers, hyphens, literal characters
and the order returned by adr list. Use code spans for literal filenames and name
adr list in the provenance footer. Do not turn filenames into prose or infer
accepted/superseded status without reading decision contents.

Require listed paths to belong to the directory declared by .adr-dir. Report
invalid metadata, unsupported/empty listings and command failures rather than
publishing a misleading or partial index. Keep the previous generated document
on failure, and prevent the output from overwriting .adr-dir.

Support --no-architecture-decisions and [architecture_decisions] enabled/title
settings. With no .adr-dir the convention is inactive. Explicit enabled=true
requires the source even if it was not detected. Consumers may instead disable
the built-in and provide their own custom section.

Using adr list and compact filenames was explicitly requested. Direct filesystem
discovery and extracting H1 titles from ADR bodies were known alternatives but
were not selected; no comparative benchmark was performed. Unit tests cover pure
parsing, integration tests use real configuration files, and functional tests use
adr-tools itself and the installed CLI.

## Consequences

Agents receive a small index of semantic decision filenames, with one directory
prefix available when they want to open a full ADR. The index contains all listed
records, including superseded ones, without interpreting their status. adr-tools
must be installed when this built-in is enabled; no Python dependency is added.
Meaningful decision filenames remain important to the value of the index.
