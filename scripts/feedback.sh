#!/bin/sh
# Feedback contract: NAME HINT COMMAND [ARG ...]. Commands can use any language.
# Keep native output on failure and normalize any nonzero exit status to 1.
# Under collect-feedback.sh, record the outcome and let the run continue instead.
if [ "$#" -lt 3 ]; then
    printf '%s\n' 'Usage: feedback.sh NAME HINT COMMAND [ARG ...]' >&2
    exit 1
fi
name=$1
hint=$2
shift 2
collect_file=${FEEDBACK_COLLECT_FILE-}
unset FEEDBACK_COLLECT_FILE

if ! report=$(mktemp); then
    printf '%s\n' 'Cannot create a diagnostic file; check the temporary directory.' >&2
    exit 1
fi
trap 'rm -f "$report"' EXIT
trap 'printf "%s\n" "Check interrupted before completion." >&2; exit 1' HUP INT TERM

"$@" >"$report" 2>&1
status=$?
if [ "$status" -eq 0 ]; then
    if [ -n "$collect_file" ]; then
        printf 'passed\t%s\n' "$name" >>"$collect_file" || exit 1
    fi
    exit 0
fi

printf '%s failed (native exit %s).\n' "$name" "$status" >&2
cat "$report" >&2
printf '\n%s\n' "$hint" >&2
if [ -n "$collect_file" ] && printf 'failed\t%s\n' "$name" >>"$collect_file"; then
    exit 0
fi
exit 1
