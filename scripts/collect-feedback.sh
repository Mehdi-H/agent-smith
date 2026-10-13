#!/bin/sh
# Collect feedback: COMMAND [ARG ...]. Every feedback.sh check inside COMMAND runs
# and reports its own diagnostics; one summary names the failures at the end.
# A step outside feedback.sh that fails, such as a prerequisite, stops the run.
if [ "$#" -lt 1 ]; then
    printf '%s\n' 'Usage: collect-feedback.sh COMMAND [ARG ...]' >&2
    exit 1
fi

if ! outcomes=$(mktemp); then
    printf '%s\n' 'Cannot create an outcome file; check the temporary directory.' >&2
    exit 1
fi
trap 'rm -f "$outcomes"' EXIT
trap 'printf "%s\n" "Check run interrupted before completion." >&2; exit 1' HUP INT TERM

FEEDBACK_COLLECT_FILE=$outcomes "$@"
status=$?
ran=$(grep -c '' "$outcomes")
failed=$(grep -c '^failed	' "$outcomes")

if [ "$status" -ne 0 ]; then
    printf '\n%s\n' "Check run stopped before completion (native exit $status) by a step outside the checks; fix the error reported above, then run it again." >&2
    if [ "$ran" -eq 0 ]; then
        exit 1
    fi
elif [ "$failed" -eq 0 ]; then
    exit 0
fi

printf '\n%s\n' "Check summary: $failed of $ran checks failed." >&2
sed -n 's/^failed	/- /p' "$outcomes" >&2
exit 1
