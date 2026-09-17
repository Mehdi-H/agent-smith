# 34. Audit wheel and sdist contents with an explicit allowlist before publication

Date: 2026-09-17

## Status

Accepted

## Context

The build pipeline produces exactly one wheel and one sdist, installs each
artifact outside the checkout and exercises the installed CLI (`just
package-check`, `just distributions-check`). These smoke tests prove the
distributions are usable but not that their contents and metadata match the
intended release contract. Motivated by issue 14
(https://github.com/Mehdi-H/agent-smith/issues/14), which asks for a stricter
audit inspired by uv's `scripts/check_uv_wheel_contents.py`: compare every
wheel entry against a version-neutral allowlist and reject missing or
unexpected files before publication.

## Decision

Add `scripts/check_dist_audit.py`, exposed as `just dist-audit` and run in
`just release-build` before publication. The check derives the release
contract (name, version, requires-python, dependencies, project URLs, console
script, license) from the repository's pyproject.toml so version bumps need no
edits, and:

- requires exactly one wheel and one sdist, named for the current version
  (stale artifacts fail);
- compares wheel and sdist members with an explicit, version-neutral
  allowlist, rejecting absolute paths, parent traversal, and missing or
  unexpected files (caches, tests and build-only sources have no allowlist
  entry);
- validates METADATA/PKG-INFO fields, the pure-Python WHEEL tag and the
  console-script entry point;
- verifies every sha256 and size in RECORD and reconciles RECORD rows with
  archive members both ways;
- rebuilds a wheel from the sdist in isolation and requires equivalent
  inventory and dist-info metadata.

The package-file allowlist lives explicitly in the script: adding a module
means extending it, so unexpected content fails closed and every packaging
change is reviewed deliberately. The existing installation smoke tests (`just
distributions-check`) are kept unchanged.

Alternatives considered at the decision date: deriving the allowlist from the
checkout's `src/` tree (rejected: a leaked or forgotten module would stay
invisible to the check), and byte-for-byte reproducible wheels (deferred:
timestamps are not normalized yet).

## Consequences

Adding or removing a packaged module requires an explicit allowlist edit,
which makes packaging changes visible in review. The sdist-derived wheel
rebuild adds one `uv build` to the release path; the build backend is pinned
(`uv_build==0.12.10`), so its behavior is deterministic. RECORD integrity is
verified locally rather than trusting the archive. Byte-for-byte
reproducibility and native signing remain out of scope.
