# Agent Smith 🕶️

[![CI](https://github.com/Mehdi-H/agent-smith/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Mehdi-H/agent-smith/actions/workflows/ci.yml?query=branch%3Amain)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Build agent instructions from your project's sources.

Agent Smith assembles deterministic Markdown from your README and custom
commands, with `AGENTS.md` as the default output.

> [!NOTE]
> The CLI is a development preview. README overview generation and custom
> command sections are available; no package release has been published yet.

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

Run `agent-smith` from your project's directory to generate `AGENTS.md`. By
default, it extracts the introduction between the first top-level H1 and the
next H2 in `README.md`, preserving its Markdown, badges and alerts. If there is
no following H2, the overview extends to the end of the file. Missing headings
or an empty overview produce an error.

The output contains an H1 with the filename, an `Overview` H2, the extracted
content and a quoted provenance footer with the `agent-smith` command and its
CLI arguments. Rerunning that command regenerates the document using the same
configuration, from the same working directory. Successful generation is silent.

```sh
agent-smith --output instructions.md
```

## Configure sections

An optional `agent-smith.toml` configures the built-in overview and custom
sections. For example, to keep the overview and append tracked files:

```toml
output = "AGENTS.md"

[overview]
enabled = true
source = "README.md"
title = "Overview"

[[sections]]
title = "Tracked files"
command = "git ls-files"
```

Each custom section uses its command's UTF-8 stdout as Markdown, followed by a
footer with the exact command. Sections appear in configuration order after the
built-in overview. To replace the built-in with your own extractor:

```toml
[overview]
enabled = false

[[sections]]
title = "Overview"
command = "./scripts/my-overview.sh"
```

Supply your own script for that command. You can also disable the built-in with
`--no-overview`, and select another configuration with `--config path/to/config.toml`.
`--output` takes precedence over configuration. Paths and command working
directories are relative to where you invoke the CLI, including with `--config`.
The output's parent directory must exist.

> [!WARNING]
> Custom commands run in your platform's shell with your permissions. Only use
> trusted configurations. If extraction or writing fails, Agent Smith preserves
> the existing output file; side effects of custom scripts are not rolled back.

> [!NOTE]
> Identical configuration and extractor outputs produce identical Markdown.
> Variable command output, such as timestamps, remains variable. Extraction
> preserves relative links and does not copy reference definitions from outside
> the overview. No Markdown formatter is applied.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository setup, development commands, commit
conventions and just-in-time architecture decisions. The license is [MIT](LICENSE).
