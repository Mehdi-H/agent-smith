# 20. Audit Python security with Bandit and pip-audit feedback checks

Date: 2026-09-12

## Status

Accepted

## Context

The project owner requested static code and dependency vulnerability feedback.
The existing fast check is offline and returns a clear success/failure signal.
Safety was initially requested, but the owner prefers an alternative without
account authentication and selected pip-audit because it is maintained by PyPA.

## Decision

Lock Bandit and pip-audit in the uv development dependency group. Expose
just bandit-check and just audit-check through the shared shell feedback wrapper.
Success is silent; findings and operational errors preserve native diagnostics
and return exit 1.

Run Bandit on src and scripts as part of just check. Block medium/high severity
findings; low severity subprocess notices remain available through a direct scan.
Keep one local B602 exception on the shell-command adapter, with its rationale
beside the call: executing explicitly trusted user-configured shell commands is
required behavior. Do not suppress that rule globally. Tests are outside this
Bandit scope.

Use pip-audit to check an export of all runtime and development dependencies from
uv.lock, preserving hashes and requiring them during the audit. Environment markers select dependencies for the current interpreter
and platform. Do not resolve or install packages while auditing. Pass --strict so
collection failures are not mistaken for a clean audit. Remove the temporary
requirements file afterwards. The public vulnerability service requires network
access but no account or API key. Keep the audit separate from just check,
pre-commit and CI so the fast loop remains offline.

Safety 3.8.1 was installed and its authentication requirement verified; no
vulnerability scan ran without credentials. Remove it from the project.
OSV-Scanner was identified as another account-free alternative suitable for
multiple ecosystems; it was not benchmarked. No comparative benchmark of
vulnerability-database coverage was performed.

## Consequences

Static analysis supplies a local feedback signal, while the dependency audit
reflects the public database at execution time and can fail on network problems.
Neither check proves the absence of vulnerabilities. Security tools are development
dependencies and do not increase the installed CLI's runtime dependencies.

References: [Bandit](https://bandit.readthedocs.io/),
[pip-audit](https://github.com/pypa/pip-audit), and
[Safety authentication](https://docs.safetycli.com/safety-docs/safety-cli/installation-and-authentication).
