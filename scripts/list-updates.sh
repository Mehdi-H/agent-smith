#!/bin/sh
# Produce only actionable updates on stdout; preserve native errors on stderr.
set -eu
report=$(mktemp)
trap 'rm -f "$report"' EXIT
case "$1" in
    mise)
        if ! mise outdated --local --bump --json > "$report"; then exit 1; fi
        uv run --offline --no-sync python scripts/update_report.py mise "$report"
        ;;
    uv)
        if ! uv lock --upgrade --dry-run --color never > "$report" 2>&1; then
            cat "$report" >&2
            exit 1
        fi
        uv run --offline --no-sync python scripts/update_report.py uv "$report"
        ;;
    *) echo 'Expected mise or uv.' >&2; exit 1 ;;
esac
