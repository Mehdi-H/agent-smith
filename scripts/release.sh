#!/bin/sh
# Release only the checked main revision; bootstrap is an explicit manual action.
set -eu
sh scripts/release-guard.sh
if [ "$(git branch --show-current)" != main ]; then
    printf '%s\n' 'Check out the main branch before releasing.' >&2
    exit 1
fi
git fetch origin main --tags
if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
    printf '%s\n' 'main advanced after checks; release from a fresh checked run.' >&2
    exit 1
fi
set --
if [ "${RELEASE_BOOTSTRAP:-false}" = true ]; then
    if [ "${GITHUB_EVENT_NAME:-}" != workflow_dispatch ]; then
        printf '%s\n' 'Bootstrap requires a manual workflow dispatch.' >&2
        exit 1
    fi
    set -- --patch
fi
uv run --locked --group release semantic-release version "$@"
