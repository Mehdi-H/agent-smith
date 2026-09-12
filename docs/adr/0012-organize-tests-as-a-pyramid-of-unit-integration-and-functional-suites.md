# 12. Organize tests as a pyramid of unit integration and functional suites

Date: 2026-09-12

## Status

Accepted

## Context

The first generation feature needs precise feedback for Markdown rules, confidence
in technical adapters, and a few complete user scenarios. The maintainer proposed
the [OCTO test pyramid series](https://blog.octo.com/la-pyramide-des-tests-par-la-pratique-1-5)
as a reference and expressed a preference for visible test levels.

The article emphasizes fast, reliable and precise feedback. Pytest markers were
an alternative for selecting levels; the existing suite used an integration
marker. We choose directories for discoverability, without a comparative benchmark.

## Decision

Organize tests in `tests/unit`, `tests/integration` and `tests/functional`:

- Unit tests exercise rules and application behavior with in-memory port
  implementations, without filesystem or subprocess dependencies.
- Integration tests exercise specific adapters against real files or processes.
- Functional tests exercise complete user scenarios through the installed CLI.

Use directories as the single source of level selection, without duplicate
markers. Keep Given/When/Then comments in all tests. Put combinations and edge
cases primarily in unit tests, adapter contracts in integration tests, and only
essential user journeys in functional tests. Do not enforce a numerical quota
or duplicate tests just to make the counts look like a pyramid.

`just check` runs only unit tests plus static checks. Expose `just test-unit`,
`just test-integration` and `just test-functional` for focused execution;
`just test` runs everything. CI runs all three levels on the Python matrix.

## Consequences

Contributors can choose a feedback scope by command or directory. The existing
harness contains many process integration tests; the new application rules will
grow the unit-test base rather than relabeling those integrations as unit tests.

Only the full suite produces representative package coverage. Level-specific
coverage reports describe just that invocation. CI costs slightly more than the
fast local loop, while still reusing the same just recipes.
