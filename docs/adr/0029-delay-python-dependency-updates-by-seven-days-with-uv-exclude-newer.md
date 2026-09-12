# 29. Delay Python dependency updates by seven days with uv exclude-newer

Date: 2026-09-13

## Status

Accepted

## Context

The maintainer wants update feedback and a waiting period before adopting newly
published Python packages. A delay gives the ecosystem time to detect compromised
releases, but does not prove that a package is safe.

## Decision

Set `exclude-newer = "7 days"` under `[tool.uv]`. Use uv.lock and locked syncs for
reproducibility; fresh resolutions admit only artifacts older than seven days.
Do not add blanket exceptions. Interpreters and mise tools are outside uv's cutoff.

Expose `just updates-mise` (local mise tools, comparing against newer versions)
and `just updates-uv` (uv lock --upgrade --dry-run within current constraints and
the cooldown). `just updates-check` executes both and returns 1 for actionable
changes or inventory failures, otherwise 0 silently. Keep network-dependent
update feedback separate from offline just check.

Exclude only VHS 0.12.0 from the mise inventory, as explicitly requested and
justified by ADR 18. Future versions remain visible. The uv inventory reports
resolvable lock changes, not every version published outside dependency bounds;
major upgrades and changes to pinned build requirements still need review.

A fixed date was considered, but a rolling seven-day delay meets the ongoing
maintenance need without manual calendar changes. No security benchmark was run.

## Consequences

Adopting the cutoff initially rolls back packages published within seven days,
including Ruff, ty and uv_build. Complexipy 8.0.0 is old enough and replaces 6.2.0;
8.0.1 is not yet eligible. Test the real complexity API and all suites after changes.
Urgent security fixes may require a deliberate, documented exception rather than
silently disabling the cutoff. Continue auditing dependencies for vulnerabilities.

References: [uv settings](https://docs.astral.sh/uv/reference/settings/#exclude-newer)
and [exclude-newer guide](https://pydevtools.com/handbook/how-to/how-to-use-exclude-newer-for-reproducible-python-environments/).
