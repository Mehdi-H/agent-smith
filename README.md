# Agent Smith 🕶️

[![CI](https://github.com/Mehdi-H/agent-smith/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Mehdi-H/agent-smith/actions/workflows/ci.yml?query=branch%3Amain)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Build agent instructions from your project's sources.

Agent Smith will assemble deterministic Markdown from documented project
operations and configuration, with `AGENTS.md` as the default output.

> [!NOTE]
> The CLI is available as a development preview. Document generation is not
> implemented yet, and no package release has been published.

## Install

Agent Smith supports Python 3.10–3.14. No release is available on PyPI yet:
start from a checkout of this version of the repository and install the CLI
from its root directory with uv:

```sh
uv tool install .
```

This installs the command in an isolated environment.

> [!TIP]
> If uv reports that its tool directory is missing from your PATH, run
> `uv tool update-shell` and restart your terminal.

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

> [!TIP]
> To confirm installation, check that `--version` prints `agent-smith 0.0.0`
> and `--help` displays the available options. Both should exit successfully.

Running `agent-smith` without arguments currently displays the same help;
it does not create an `AGENTS.md` file yet.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository setup, development commands, commit
conventions and just-in-time architecture decisions. The license is [MIT](LICENSE).
