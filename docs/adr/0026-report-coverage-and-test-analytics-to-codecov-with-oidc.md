# 26. Report coverage and test analytics to Codecov with OIDC

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer wants hosted coverage and Test Analytics in Codecov. CI previously
ran suites separately; their coverage files replaced each other, so the last
suite alone would not represent the full test run.

## Decision

Use just test to run all suites together on each supported Python version,
producing coverage.xml and legacy-format junit.xml. Upload explicitly selected
reports with the pinned Codecov coverage and test-results actions using OIDC.
The reusable CI and its caller grant id-token:write; no stored Codecov token is
needed. Report uploads run after test failures when the report exists, but not
after cancellation. Upload coverage and Test Analytics only on main, on push or
manual workflow dispatch. All PRs run tests but skip Codecov uploads.

Static upload tokens were offered by Codecov's setup screen; OIDC was selected
to avoid maintaining a long-lived secret. No comparative benchmark was performed.

## Consequences

The Codecov GitHub App must be installed for this repository. Named reports let
Codecov distinguish Python matrix runs. Local reports remain ignored by Git.
Upload failures are visible CI failures; Codecov availability therefore affects
releases that depend on CI. Unit-only just check remains the fast feedback path.
