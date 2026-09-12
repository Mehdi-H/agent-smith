# 24. Automate zero-major versions and changelogs with Python Semantic Release

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer requested automatic versions, a commit-derived changelog and
GitHub releases, while deliberately keeping the product below 1.0.

## Decision

Use Python Semantic Release with the Conventional Commit parser on main only.
Set allow_zero_version=true and major_on_zero=false. Features and breaking
changes bump minor; fixes and performance changes bump patch. Other changes
alone do not release. A deliberate configuration change is needed for 1.0.

PSR stamps pyproject.toml, generates CHANGELOG.md, commits the synchronized
uv.lock, tags the commit and creates the GitHub release. Run its CLI via just
and a pinned uv release group. Stop manually bumping versions in feature PRs.

release-please and manual releases are known alternatives, not evaluated here.
PSR was explicitly selected by the maintainer; no benchmark was performed.

## Consequences

The workflow needs narrowly scoped GitHub write access. A manual patch bootstrap
can start publication after a tooling-only change. Existing tags remain intact.

PSR 10.6.2 constrains Click to ~=8.1.0, which selects a version affected by
PYSEC-2026-2132. Override Click to >=8.3.3,<8.5 in uv, retaining PSR's upper
ceiling. This deliberately relaxes upstream's minor constraint; our real CLI
lifecycle tests must pass and pip-audit must remain clean. Revisit/remove this
override when upstream accepts a corrected Click version. It is a tooling-only
compatibility exception, not a runtime dependency of Agent Smith.
