# 25. Publish verified distributions from main with PyPI trusted publishing

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer registered agent-smith-cli on PyPI with a pending publisher for
Mehdi-H/agent-smith, release.yml and the pypi environment. Releases must follow
successful checks on main and expose downloadable GitHub artifacts.

## Decision

Use release.yml on main to call the reusable CI matrix before running just release.
Use the GitHub token for version commits, tags and releases; serialize release runs.
Build once, smoke-test wheel and sdist, retain GitHub Actions artifacts, attach
them to the GitHub release, and publish the same files with uv Trusted Publishing.
Only the separate PyPI job receives id-token:write, in the main-only pypi environment.

Manual bootstrap forces a patch release. Recovery downloads an existing main tag
release instead of rebuilding or bumping; uv checks existing PyPI files for retries.
Permanent PyPI tokens and the PyPA publishing action were known alternatives;
no benchmark was performed. uv was chosen to expose publishing through just.

## Consequences

No publication runs on PRs or tags. Build commands remain locally executable.
GitHub and PyPI publication is not transactional; a failed upload may require
the documented recovery. The initial publication remains a maintainer-triggered action.
