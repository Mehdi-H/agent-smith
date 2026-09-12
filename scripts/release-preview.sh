#!/bin/sh
# Preview the committed branch as main in a disposable local clone.
set -eu
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
trap 'exit 1' HUP INT TERM
semantic=$(command -v semantic-release)
origin=$(git remote get-url origin)
git clone --quiet --no-local . "$scratch/repo"
# Include the configuration under review, without mutating the real checkout.
cp pyproject.toml "$scratch/repo/pyproject.toml"
cd "$scratch/repo"
git remote set-url origin "$origin"
git fetch --quiet origin --tags
git switch --quiet -C main
"$semantic" --noop version
