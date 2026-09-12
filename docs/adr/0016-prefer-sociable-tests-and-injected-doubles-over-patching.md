# 16. Prefer sociable tests and injected doubles over patching

Date: 2026-09-12

## Status

Accepted

## Context

The project owner explicitly rejects patching in tests: replacing collaborators
through global names can hide dependencies and allow difficult-to-test designs.
We want tests to encourage explicit dependency injection and sociable behavior.

## Decision

Prefer direct tests with real, fast and deterministic collaborators. Use explicitly
injected mocks, stubs or fakes at awkward boundaries. Do not use monkeypatch,
unittest.mock.patch, mocker.patch or equivalent runtime replacement techniques.
Keep the existing unit/integration/functional test pyramid; a unit test need not
isolate every collaborating object.

`just test-doubles-check`, included in `just check`, scans every Python source
under `tests`, including fixtures and helpers. A case-insensitive textual rule
rejects monkeypatch spellings and the word patch or patch-prefixed APIs. It also
checks strings, comments, imports and aliased imports. The shared shell feedback
wrapper returns silent exit 0 or exit 1 with the offending file, line and source.
The checker is deliberately a simple feedback guard, not a complete static proof:
dynamic indirection and differently named replacement APIs still require review.

Use inert text fixtures outside the Python test sources to test the guard's
negative examples. Do not add suppression markers to bypass it. Replace the
existing directory-changing fixtures by injecting a directory into the TOML
configuration adapter, leaving process-wide state untouched.

This is a project preference, not a claim that all test doubles or all solitary
tests are invalid. No comparative tooling benchmark was performed. AST-based
analysis could reduce textual false positives, but a grep-like rule was requested.

## Consequences

Tests make dependencies visible and can exercise collaborating objects together.
Textual matches in comments or strings must also be removed from test sources.
Injected mocks remain allowed; tests should assert behavior rather than mirror
implementation structure.

Reference: Martin Fowler, [Unit Test — Solitary or Sociable?](https://martinfowler.com/bliki/UnitTest.html).
