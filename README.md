# Agent Smith 🕶️

Build agent instructions from your project's sources.

Agent Smith will assemble deterministic Markdown from documented project
operations and configuration, with `AGENTS.md` as the default output.

**Status:** the development harness and installable CLI are available. Document
generation is not implemented yet, and no package release has been published.

## Install

Agent Smith supports Python 3.10–3.14. No release is available on PyPI yet:
start from a checkout of this version of the repository and install the CLI
from its root directory with uv:

```sh
uv tool install .
```

This installs the command in an isolated environment. If uv reports that its
tool directory is missing from your PATH, run `uv tool update-shell` and restart
your terminal.

Alternatively, install with pip in an activated Python virtual environment:

```sh
python -m pip install .
```

## Run and verify

```sh
agent-smith --version
agent-smith --help
agent-smith
```

`--version` should print `agent-smith 0.0.0`, the current unreleased version.
`--help` displays the available options. Both commands should exit successfully.
Running `agent-smith` without arguments currently displays the same help;
it does not create an `AGENTS.md` file yet.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository setup, development commands, commit
conventions and just-in-time architecture decisions. The license is [MIT](LICENSE).
