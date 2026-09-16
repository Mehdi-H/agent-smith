# 33. Require full-length SHA pinning and an allowlist for external Actions

Date: 2026-09-16

## Status

Accepted

## Context

The repository allowed all Actions and reusable workflows, and GitHub did not
require commit SHA pinning (`allowed_actions: all`, `sha_pinning_required:
false`). The checked-in workflows already pinned every external Action to a
full-length commit SHA, so nothing depended on the permissive setting. Zizmor
(ADR 0011) audits the workflows offline but does not enforce the repository's
Actions policy, and the setting itself cannot be expressed in committed files.
Motivated by issue 19.

## Decision

Restrict the repository's GitHub Actions policy to what the workflows use:

- Require external Actions to be pinned to a full-length commit SHA
  (`sha_pinning_required: true`).
- Allow GitHub-authored Actions.
- Allow only the external Actions currently referenced by the workflows:
  `jdx/mise-action` and `codecov/codecov-action`. Review the allowlist whenever
  a new Action is introduced.

Apply the settings through the GitHub Actions permissions API. The allowlist
patterns must carry a reference wildcard (`jdx/mise-action@*`): a bare
`owner/repo` pattern does not match SHA-pinned `uses:` references and every
pull request run fails at startup with `startup_failure`. Add the

deterministic offline check `scripts/checks/sha_pinning.py` (exposed as
`just sha-pinning-check` in `just check`) so every `uses:` reference stays
pinned to a full-length SHA and any drift is reported before the repository
setting would reject it.

Alternatives considered at the decision date: relying on zizmor alone (it does
not enforce this policy), leaving pinning unenforced (the setting would stay
permissive for no gain), and restricting Actions to verified creators only
(rejected: `jdx/mise-action` and `codecov/codecov-action` are not
GitHub-verified, so the workflows would stop running).

## Consequences

New external Actions require both a full-length SHA pin in the workflow and an
allowlist entry in the repository settings; the API must be revisited when the
allowlist changes. Tags and branch references stop working in workflows, so
Action upgrades mean new SHAs. The repository setting lives outside Git, so the
offline check covers workflow drift but the setting itself must be reviewed
manually.
