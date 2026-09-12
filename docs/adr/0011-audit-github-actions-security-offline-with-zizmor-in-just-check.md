# 11. Audit GitHub Actions security offline with Zizmor in just check

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer requested a Zizmor audit of the existing GitHub Actions workflow
and execution measurements to choose its place in the feedback loop. The initial
offline audit reported no findings. On macOS, 15 invocations measured a warm
median of about 26 ms for Zizmor and 57 ms through the just feedback recipe.

This records the requested choice. Actionlint is a known complementary checker
for workflow syntax and expressions, with some security checks. We compared their
documented purposes, but did not execute or benchmark actionlint.

## Decision

Pin Zizmor in mise.toml and expose `just workflows-check` in the Quality group.
Run `zizmor --offline --strict-collection --no-progress .github/workflows` through
the shared feedback wrapper and include the recipe in `just check`.

Use the default audit persona without suppressions. Treat collection errors as
failures, and normalize any nonzero exit code through the wrapper. The measured
cost is small enough for frequent local checks, as well as pre-commit and CI.

## Consequences

The same local recipe now audits workflow security in the editor feedback loop,
Git hooks and GitHub Actions. Findings report the rule and source location while
successful checks stay quiet. No runtime dependency is added to the Python CLI.

Offline mode excludes audits requiring network access. A clean result is not a
security guarantee or a replacement for review. Measurements concern the current
single workflow on one machine; revisit the cost as the repository grows.
