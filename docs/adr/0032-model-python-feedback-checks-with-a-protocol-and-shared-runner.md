# 32. Model Python feedback checks with a Protocol and shared runner

Date: 2026-09-13

## Status

Accepted

## Context

The repository has Python feedback scripts with similar process contracts but
different conventions such as `check`, `inspect` and `verify`. Some print from
domain logic or choose their own exit status. New checks should expose named,
typed problems while preserving the language-independent feedback boundary from
ADR 7: silence on success, actionable stderr on failure and only exit 0 or 1.

## Decision

Model each Python feedback check with a structural `Check[Target]` Protocol whose
`evaluate` method returns an immutable `CheckResult`. Represent findings as the
discriminated `Problem` union of `Violation`, `InvalidTarget` and
`IncompleteCheck`, with optional source `Location` data.

Use one `run_check` process adapter to catch incomplete evaluations, render
problems on stderr and derive exactly exit 0 or 1 from whether problems exist.
Keep target types specific to each domain instead of forcing paths, globs, Git
state and package artifacts into one universal target abstraction.

Prefer structural composition over a base class. Concrete checks may be classes
or functions adapted to the Protocol, and cannot own printing or process status.
Retain the POSIX feedback wrapper for native and non-Python tools. Migrate Python
checks behind thin `main` entry points without changing their command-line scope.

An abstract base class and a universal path-based check type were considered but
not selected. No comparative implementation or benchmark was performed.

## Consequences

Python checks share one vocabulary, rendering path and fail-closed process
contract. Contract tests can exercise the runner once, while domain tests assert
typed problems without capturing output. Adding a check requires a target,
evaluator and thin CLI adapter rather than repeated status and printing logic.

The Protocol cannot prevent arbitrary code from bypassing the runner at runtime;
type checking, tests and review enforce that boundary. Operational checks such as
package installation may still perform subprocesses and temporary writes during
evaluation. ADR 7 remains current because this internal Python composition does
not replace its language-independent process contract.
