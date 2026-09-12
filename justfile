set positional-arguments

# List the repository's documented operations.
default:
    @just --list

# Manage architecture decisions with adr-tools (e.g. just adr new Use argparse).
adr +args:
    adr "$@"
