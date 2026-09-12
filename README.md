# Agent Smith 🕶️

[![CI](https://github.com/Mehdi-H/agent-smith/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Mehdi-H/agent-smith/actions/workflows/ci.yml?query=branch%3Amain)
[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Build agent instructions from your project's sources.

Run `agent-smith` at your project root to generate **`AGENTS.md`** from your
README overview, your documented just commands and optional custom extractors.
The output is deterministic Markdown.

> [!NOTE]
> The CLI is a development preview. Built-in overview and available-command
> sections are available; no package release has been published yet.

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
> To confirm installation, check that `--version` prints the installed Agent Smith version
> and `--help` displays the available options. Both should exit successfully.

Run the command **from the root of the project you want to document**. It creates
or replaces `AGENTS.md` in that directory. Successful generation is silent;
open the file to verify the result. No configuration is needed when you follow
the conventions below.

```sh
agent-smith
cat AGENTS.md
```

Use `agent-smith --output instructions.md` to choose another output filename.
The document has an H1 containing its filename, an H2 for each section and a
quoted footer identifying the command that produced that section.

## Conventions

### Overview: a README.md at the project root

Place a `README.md` at the root with a top-level H1 followed by a nonempty
introduction. Agent Smith copies the Markdown between that H1 and the first
following H2 into **Overview**. No extraction script is required.

```markdown
# My project

Describe what the project does and why someone would use it.

## Installation

This section is outside the extracted overview.
```

The first H2 ends the overview; if there is no H2, extraction continues to the
end of the file. Badges, links and GitHub alerts in the introduction are kept.
An absent README, a missing H1 or an empty introduction produces an error.
Use `--no-overview` to disable this section.

### Available commands: a documented, grouped justfile at the project root

Document your project's practices in a root `justfile` (also detected as
`Justfile` or `.justfile`). Give each recipe a descriptive comment and a group,
and provide a `help` recipe that prints the standard `just --list` output:

```just
# List the project's available commands.
[group("Help")]
help:
    @just --list

# Check modified files for whitespace errors.
[group("Quality")]
check-whitespace:
    git diff --check
```

[Install just](https://just.systems/man/en/installation.html) and make sure
`just help` works from the project root. Agent Smith automatically runs that
command and converts its output to **Available commands**: Markdown lists under
group subheadings, preserving recipe order, parameters and descriptions.
For the example above, the section contains:

```markdown
## Available commands

### Help

- `just help` — List the project's available commands.

### Quality

- `just check-whitespace` — Check modified files for whitespace errors.
```

The section ends with a footer naming `just help`. Listed recipes are not
executed; only the help recipe runs. With no root justfile, this section is
omitted and just is not required. Use `--no-available-commands` to disable it.
If help fails or does not produce the supported list format, generation fails
and the existing `AGENTS.md` is preserved. Custom help formats can be supplied
as Markdown through a custom section instead.

## Configure sections

An optional root `agent-smith.toml` customizes built-in sections and adds custom
extractors. For example, to keep both built-ins and append tracked files:

```toml
output = "AGENTS.md"

[overview]
enabled = true
source = "README.md"
title = "Overview"

[available_commands]
enabled = true
title = "Available commands"
command = "just help"

[[sections]]
title = "Tracked files"
command = "git ls-files"
```

Each custom section uses its command's UTF-8 stdout as Markdown, followed by a
footer with the exact command. Sections appear in configuration order after the
built-in overview and available commands. Set `[available_commands].enabled = false`
to disable command discovery, or change its `command` to another source of
standard just list output, such as `just --list`. Explicit `enabled = true`
requires the command to work even if no root justfile was detected.

To replace the overview with your own extractor:

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
> The help recipe and custom commands run with your permissions. Only generate
> documents from trusted projects and configurations. If extraction or writing fails, Agent Smith preserves
> the existing output file; side effects of custom scripts are not rolled back.

> [!NOTE]
> Identical configuration and extractor outputs produce identical Markdown.
> Variable command output, such as timestamps, remains variable. Extraction
> preserves relative links and does not copy reference definitions from outside
> the overview. No Markdown formatter is applied.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository setup, development commands, commit
conventions and just-in-time architecture decisions. The license is [MIT](LICENSE).
