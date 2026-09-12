# 10. Run just check in GitHub Actions on Python 3.10 through 3.14

Date: 2026-09-12

## Status

Accepted

## Context

The maintainer requested minimal GitHub CI for pull requests and main, running
the existing fast feedback command across the Python versions declared supported
by this package. Deployment remains a later increment.

This records that explicit choice. Other CI services and a single-interpreter
job are known alternatives, but were not comparatively evaluated. GitHub Actions
matches the requested hosting platform and a matrix exercises each supported
minor version.

The maintainer also wants CI failures to be reproducible locally through the
same documented operations. Duplicating tool invocations in workflow YAML is a
known alternative, but was not evaluated: sharing just recipes is the explicit
project preference.

## Decision

Run `just check` on Ubuntu for Python 3.10, 3.11, 3.12, 3.13 and 3.14 on
`pull_request` and pushes to `main`. Install repository tools with mise and
synchronize the existing uv.lock with `uv sync --locked`.

Prefer documented just recipes for repository operations in GitHub Actions.
Keep their commands, options and failure behavior in the justfile rather than
duplicating them in workflow YAML. When adding a CI operation, reuse an existing
recipe or introduce one that contributors can also run locally.

Keep runner-specific orchestration in the workflow: checkout, tool installation,
matrix interpreter selection, caching and dependency preparation. The current
workflow prepares uv directly because `just setup` also installs local Git hooks.

Use `UV_PYTHON` to select the matrix version instead of `.python-version`, as
documented in [uv's GitHub Actions guide](https://docs.astral.sh/uv/guides/integration/github/).
Pin checkout and mise actions by commit SHA, grant read-only repository access,
bound execution time, and let other matrix jobs finish if one fails.

## Consequences

Pull requests receive hosted checks for all five supported Python versions,
including the fast tests used locally. Maintain the matrix alongside package
classifiers when Python support changes. Five jobs repeat static checks; this
keeps the initial workflow consistent with the local command.

Contributors can investigate failures by running the same just recipe with the
same interpreter and locked dependencies. Shared commands reduce drift; they do
not guarantee identical behavior across different operating systems or external
environments.

This workflow does not run the full integration suite, build distributions or
publish releases. It establishes Linux checks rather than a cross-platform
guarantee. Successful checks are silent; GitHub displays their step status and
failures retain the feedback wrapper's diagnostics.
