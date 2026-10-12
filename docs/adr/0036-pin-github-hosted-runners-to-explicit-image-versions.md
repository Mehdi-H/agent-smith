# 36. Pin GitHub-hosted runners to explicit image versions

Date: 2026-10-12

## Status

Accepted

## Context

Every job in `ci.yml` and `release.yml` ran on `runs-on: ubuntu-latest`. GitHub
moves floating `-latest` labels between image generations; `ubuntu-latest`
migrates to Ubuntu 26 on 19 October 2026 (actions/runner-images#14748). A label
migration silently changes the operating system, preinstalled tools and system
libraries under CI and releases without any repository change, so a regression
would surface as an unexplained failure on main rather than in a reviewed pull
request. Zizmor (ADR 0011) and the SHA pinning check (ADR 0033) do not inspect
runner labels. Motivated by issue 30.

## Decision

Run every job on an explicitly versioned runner label, currently
`ubuntu-24.04`, the image `ubuntu-latest` resolved to before the migration.
Upgrade the image deliberately, in a dedicated pull request, once the new image
is verified.

Add the deterministic offline check `scripts/checks/runner_pinning.py` (exposed
as `just runner-pinning-check` in `just check`). It reports every job whose
`runs-on` uses a label ending in `-latest`, such as `ubuntu-latest`,
`macos-latest` or `windows-latest`, at the workflow line and job id. It fails
closed on values it cannot read literally (expressions, block and mapping forms)
rather than passing them. It follows the shared check model of ADR 0032 and reads
workflows line by line, like the SHA pinning check, without a YAML dependency.

Alternatives considered at the decision date: keeping `ubuntu-latest` and
absorbing migrations as they come (rejected: they arrive unreviewed), pinning
only through review discipline (rejected: nothing would catch a reintroduced
floating label before push), and parsing workflows with PyYAML (rejected: it is
only a transitive lock entry, not a declared dependency).

## Consequences

CI and releases keep the same image across GitHub's label migrations, and a
floating label is caught by `just check` before push. Image upgrades become an
explicit maintenance task. A pinned image is eventually deprecated and removed
by GitHub, so the pin must be bumped before its retirement date. Runner labels
built from expressions such as `${{ matrix.os }}` cannot be verified offline and
must be written inline.
