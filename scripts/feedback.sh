#!/bin/sh
# Feedback contract: NAME HINT COMMAND [ARG ...]. Commands can use any language.
# Keep native output on failure and normalize any nonzero exit status to 1.
if [ "$#" -lt 3 ]; then
    printf '%s\n' 'Usage: feedback.sh NAME HINT COMMAND [ARG ...]' >&2
    exit 1
fi
name=$1
hint=$2
shift 2

if ! report=$(mktemp); then
    printf '%s\n' 'Cannot create a diagnostic file; check the temporary directory.' >&2
    exit 1
fi
trap 'rm -f "$report"' EXIT
trap 'printf "%s\n" "Check interrupted before completion." >&2; exit 1' HUP INT TERM

"$@" >"$report" 2>&1
status=$?
if [ "$status" -eq 0 ]; then
    exit 0
fi

printf '%s failed (native exit %s).\n' "$name" "$status" >&2
cat "$report" >&2
printf '\n%s\n' "$hint" >&2
exit 1
