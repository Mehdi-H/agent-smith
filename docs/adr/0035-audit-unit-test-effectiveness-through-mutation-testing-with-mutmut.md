# 35. Audit unit test effectiveness through mutation testing with mutmut

Date: 2026-09-18

## Status

Accepted

## Context

ADR 6 enforces branch coverage, but coverage only measures which lines tests
execute, not whether they assert the behavior. Surviving mutants reveal tests
that execute code without verifying it. The unit suite is fast (about one
second), which makes per-mutant reruns practical; integration and functional
tests spawn subprocesses and stay out of mutation scope.

## Decision

Hunt surviving mutants in the fast unit test suite with mutmut, configured in
`pyproject.toml` and run through `just test-mutation`. mutmut was selected
after an explicit comparison requested at decision time: cosmic-ray is more
rigorous but its session and Celery model is oversized for this codebase,
pytest-gremlins is fast but young and maintained by one person, and mutpy,
mutatest and poodle are unmaintained. mutmut is actively maintained, supports
the supported Python range, stores configuration in `pyproject.toml` and
matches the project's fast-feedback workflow. No benchmark was performed; the
comparison relied on documentation, maintenance status and a local spike.

Error messages are user-facing output, so tests assert them exactly rather
than by type or substring. Mutants proven equivalent (falsy `None`, wrapped
string literals whose characters are unchanged, defaults that can never be
consulted) are accepted survivors and documented rather than chased.

## Consequences

The mutation score on code exercised by unit tests rose from 79% to 97%,
with the remaining survivors being documented equivalent mutants. New tests
must kill the mutants they target; equivalent mutants require an explicit
justification instead of a weaker test.

mutmut's incremental cache does not rerun existing mutants when tests change,
so `mutants/` must be deleted after strengthening the suite. Mutation testing
is not yet part of `just check` or CI; runs are on demand until a score
threshold policy is decided.
