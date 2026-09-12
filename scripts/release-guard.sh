#!/bin/sh
# Keep publication inside the authorized main-branch GitHub workflow.
set -eu
if [ "${GITHUB_ACTIONS:-}" != true ] || [ "${GITHUB_REF:-}" != refs/heads/main ]; then
    printf '%s\n' 'Releases must run in GitHub Actions from main.' >&2
    exit 1
fi
case "${GITHUB_EVENT_NAME:-}" in
    push|workflow_dispatch) ;;
    *) printf '%s\n' 'This event cannot publish a release.' >&2; exit 1 ;;
esac
