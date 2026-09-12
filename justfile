set positional-arguments

# List the repository's documented operations.
default:
    @just --list

# Manage architecture decisions with adr-tools (e.g. just adr new Use argparse).
adr +args:
    adr "$@"

# Install the pinned Python and synchronize the project from uv.lock.
setup:
    uv python install
    uv sync --locked

# Run the CLI from the installed development environment.
run *args:
    uv run --no-sync agent-smith "$@"

# Build a source distribution and a wheel using the uv backend.
build:
    uv build --no-sources
