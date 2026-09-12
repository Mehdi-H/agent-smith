#!/bin/sh
# Run both human-facing inventories; updates and command failures require action.
set -eu
report=$(mktemp)
trap 'rm -f "$report"' EXIT
status=0
for recipe in updates-mise updates-uv; do
    if ! just "$recipe" > "$report" 2>&1; then
        printf '%s failed:\n' "$recipe" >&2
        cat "$report" >&2
        status=1
    elif [ -s "$report" ]; then
        printf '%s:\n' "$recipe" >&2
        cat "$report" >&2
        status=1
    fi
done
exit "$status"
