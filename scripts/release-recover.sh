#!/bin/sh
# Retry only artifacts already attached to a release whose tag belongs to main.
set -eu
sh scripts/release-guard.sh
tag=${1:?A release tag is required}
if ! printf '%s\n' "$tag" | LC_ALL=C grep -Eq '^v0\.[0-9]+\.[0-9]+$'; then
    printf '%s\n' 'Expected an existing v0.MINOR.PATCH tag.' >&2
    exit 1
fi
if [ "${GITHUB_EVENT_NAME:-}" != workflow_dispatch ]; then
    printf '%s\n' 'Recovery requires a manual workflow dispatch.' >&2
    exit 1
fi
git fetch origin main --tags
git merge-base --is-ancestor "$tag" origin/main
mkdir -p dist
rm -f dist/*.whl dist/*.tar.gz
gh release download "$tag" --pattern '*.whl' --pattern '*.tar.gz' --dir dist
just distributions-check
printf 'released=true\n' >> "$GITHUB_OUTPUT"
