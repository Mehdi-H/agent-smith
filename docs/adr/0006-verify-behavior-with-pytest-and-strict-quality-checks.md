# 6. Verify behavior with pytest and strict quality checks

Date: 2026-09-12

## Status

Accepted

## Context

We need quick, actionable checks for a small CLI, plus confidence that the built artifact works outside the source checkout. The fast loop has a target of less than one second in a prepared, warm environment.

This records the requested pytest, Ruff, ty and deptry toolchain. unittest is a known alternative test runner; it was not trialled. No comparative benchmark of test runners, linters or type checkers was performed. Validation of our selected toolchain does not establish superiority over alternatives.

## Decision

Use pytest for behavior tests and pytest-cov for line and branch coverage, including subprocess coverage. Run adapter tests in just check and process integration tests in just test. Use Ruff for lint and formatting, ty targeting Python 3.10 for types, and deptry for runtime dependency consistency. Warnings fail pytest and ty; enabled Ruff and deptry violations remain errors. Commands use uv run --offline --no-sync after just setup. Build a wheel from the sdist and install it into a fresh environment in just package-check.

## Consequences

Unit tests focus on observable behavior; integration tests exercise entry points and feedback process contracts. Coverage reports describe the executed suite, so the fast subset need not cover process startup. No arbitrary coverage threshold is imposed yet. Full tests and package checks run separately from the subsecond feedback loop. Future application ports will support in-memory unit tests without shells or disk.
