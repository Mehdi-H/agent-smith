#!/bin/sh
# Audit the locked dependency set without resolving or installing packages.
set -eu
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
trap 'exit 1' HUP INT TERM
uv export --locked --offline --all-groups --no-emit-project --format requirements-txt --output-file "$scratch/requirements.txt" >/dev/null
uv run --offline --no-sync pip-audit --requirement "$scratch/requirements.txt" --disable-pip --require-hashes --strict --progress-spinner off
