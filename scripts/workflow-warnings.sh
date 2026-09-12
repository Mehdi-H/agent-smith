#!/bin/sh
# Inspect a completed run's latest attempt; gh provides pagination and JSON filtering.
set -eu
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
candidates=$(gh api --paginate "repos/$repo/actions/runs?branch=main&status=success&per_page=100" --jq '.workflow_runs[] | [.workflow_id, .id] | @tsv')
runs=$(printf '%s\n' "$candidates" | awk 'NF == 2 && $2 > latest[$1] {latest[$1] = $2} END {for (workflow in latest) print latest[workflow]}' | sort -n)
if [ -z "$runs" ]; then
    echo 'No successful workflow runs on main; cannot confirm they are warning-free.' >&2
    exit 1
fi
status=0
for run_id in $runs; do
    endpoint="repos/$repo/actions/runs/$run_id"
    state=$(gh api "$endpoint" --jq '[.status, .conclusion, .run_attempt] | @tsv')
    case "$state" in
        completed*) ;;
        *) echo "Run $run_id is not completed: $state. Wait for completion and retry." >&2; exit 1 ;;
    esac
    attempt=$(printf '%s\n' "$state" | cut -f3)
    checks=$(gh api --paginate "$endpoint/attempts/$attempt/jobs?per_page=100" --jq '.jobs[].check_run_url')
    if [ -z "$checks" ]; then
        echo "Run $run_id has no inspectable jobs; cannot confirm it is warning-free." >&2
        exit 1
    fi
    for check in $checks; do
        findings=$(gh api --paginate "$check/annotations?per_page=100" --jq '.[] | select(.annotation_level == "warning" or .annotation_level == "failure") | "\(.annotation_level): \(.path):\(.start_line): \(.title // "")\n\(.message)"')
        if [ -n "$findings" ]; then
            printf 'Run %s, check %s\n%s\n' "$run_id" "$check" "$findings" >&2
            status=1
        fi
    done
    case "$state" in
        completed"$(printf '\t')"success*) ;;
        *) printf 'Run %s did not succeed: %s\n' "$run_id" "$state" >&2; status=1 ;;
    esac

done
exit "$status"
