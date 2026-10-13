# 38. Report every failing feedback check in one run of just check

Date: 2026-10-12

## Status

Accepted

## Context

`just check` and `just check-repo-wide` ran their checks as just dependencies and
recipe lines. Just stops at the first failing line, and it has no keep-going
option, so one run reported a single problem. Finding every problem took a
fix-and-rerun loop. That loop is slow for `check-repo-wide`, which needs the
network and builds, audits and previews releases. Some recipes, such as `lint`
and `secrets-check`, run several feedback checks, so running whole recipes in a
loop would still hide failures inside them. Motivated by issue 47.

## Decision

Collect outcomes at the feedback wrapper boundary. `scripts/collect-feedback.sh
COMMAND` runs the command with `FEEDBACK_COLLECT_FILE` pointing to a temporary
outcome file. When that variable is set, `scripts/feedback.sh` still prints the
check name, native diagnostics and hint on failure. It then records the outcome
and exits 0, so just carries on with the next check. The wrapper unsets the
variable before it runs its command, so a nested check inside a checked command
keeps the normal contract and fails that outer check.

After the command, the collector exits 0 silently when every check passed. If any
check failed, it prints `Check summary: F of N checks failed.` on stderr, names
each failing check and exits 1. A step outside the wrapper that fails, such as a
prerequisite, stops the run. The collector reports that stop with its exit code,
then summarizes the checks that already ran.

`just check` and `just check-repo-wide` keep `setup` as a just dependency, so a
broken environment is reported once and up front, before any check runs. Their
checks move to the private recipes `_check-suite` and `_check-repo-wide-suite`,
which the collector runs. `_check-repo-wide-suite` depends on `_check-suite`
rather than on `check`, so a repository-wide run has one setup and one summary.

Alternatives considered at the decision date: a runner that loops over recipe
names (rejected: failures inside multi-check recipes stay hidden unless every
check becomes its own recipe), and just's parallel dependencies (rejected: the
run still stops on the first failure and interleaves output).

## Consequences

One run reports every failing check with its feedback, followed by a summary.
The silent zero on success from ADR 0007 is unchanged. A wrapped check exits 0
on failure only under the collector, which always turns any recorded failure
into exit 1. Running a single check recipe or a private suite directly keeps the
fail-fast contract. Pre-commit runs `just check` and then `just cli-check`.
Lefthook is not piped, so both run and are reported even when the first fails.
CI runs `just check` as one step, with the same output. Its separate integration
and functional test steps are still skipped after a failed step. Steps that are
not wrapped by feedback.sh, such as `setup`, still stop the run on failure.
