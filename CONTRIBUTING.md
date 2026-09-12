# Contributing

Install [mise](https://mise.jdx.dev/), then run `mise trust` and `mise install`.
Activate mise in your shell or prefix commands with `mise exec --`.
From the cloned repository, prepare the development environment and verify the CLI:

```sh
mise trust
mise install
just setup
just run --help
just run --version
```

Run `just help` to discover commands with their descriptions and parameters.
Running `just` displays the same help. `just build` produces a wheel and source
distribution in `dist/` using standard Python packaging metadata.
Recipes are grouped by usage. Run `just --groups` to list groups, or
`just --list --group Quality` to focus on checks. Every recipe, including private
helpers, must have a nonempty documentation comment and belong to a nonempty
group. `just manifest-check` enforces this through just's parsed representation
and is included in `just check`.

Run `just setup` to install the pinned Python and synchronize the locked virtual
environment. `just check` runs lint, format verification, types, dependency checks
and fast tests offline, without synchronizing or downloading packages. Its target
is under one second on a prepared, warm environment. `just fmt` formats Python
and the justfile; `just fmt-just` formats only the justfile. `just check` verifies
both formats without modifying files.

Run `just test` for the full suite, including subprocess integration tests, with
native pytest output displayed directly in the terminal, including progress and
the coverage summary. Line and branch coverage reports are also available in
`coverage.xml` and `htmlcov/index.html`. Run
`just package-check` to build fresh artifacts and verify the wheel in a temporary
environment outside the checkout. These checks are more expensive than the fast
loop. Never silence warnings to make a check pass without addressing their cause.

## Git hooks

`just setup` installs Lefthook's pre-commit hook for this checkout. After updating
an existing checkout, run `mise install` and `just hooks-install` to enable it.
Every commit runs `just check` and `just cli-check`; a failure blocks the commit.
`just cli-check` invokes the installed `agent-smith` command without arguments,
through uv, offline and without synchronizing dependencies. It currently checks
startup and a successful exit; document generation is not implemented yet.

Run `just hooks-check` to execute the hook manually. Lefthook displays a progress
summary while successful checks stay quiet. Hooks use mise to resolve the pinned
tools; mise must be on the PATH of the terminal or IDE that runs Git. Checks
inspect the working tree, so review partially staged changes before committing.

## Feedback commands

The repository's check recipes return 0 silently on success, or 1 with diagnostics
on failure. Reports such as coverage remain available as files. Use the shared
process wrapper when adding a check; the checked command can use any language:

```sh
sh scripts/feedback.sh 'Check name' 'How to fix or investigate the failure' command arg1 arg2
```

The wrapper preserves native output and records the native exit code on failure.
Do not hide setup failures, missing tools or failed checks with `|| true`. Just
recipes suppress command echo; just may add its own diagnostic on failure.
This harness currently requires a POSIX shell. The installed CLI does not.

`just test` is an interactive operation: it displays pytest's native output even
on success, while still returning 1 on any failure. `just check` remains the
silent-on-success feedback loop for agents.

Commands that generate section content have a different contract: their stdout
is the content. Do not wrap those producers in the silent feedback wrapper.
Instructions and ADRs guide work before execution; these checks provide feedback
after execution.

## Skill structure

Run `just skills-check` to validate `.agents/skills`, or `just skills-check PATH`
for a single skill or another collection. This check is included in `just check`.
The mise-pinned skill-validator checks local metadata, structure, Markdown fences
and internal references. Strict mode treats warnings as failures; the shared
wrapper keeps successful runs silent. Remote link checks and LLM scoring are not
part of this fast check. Structural validity does not establish that instructions
are correct or useful; review their meaning too.

## Test structure

Structure every test with one standalone `# Given`, `# When`, and `# Then`
comment, in that order, at the test body's indentation. Add a short explanation
after the marker when it clarifies the scenario. Given describes setup or supplied
fixtures, When identifies the action, and Then introduces expected outcomes.
Avoid hiding the action in an assertion when it can be captured separately.

`just test-structure` checks the convention and is included in `just check`.
It reports the file, test definition line and test name. It recognizes actual
comments, not strings, for `test_*` functions and methods in `Test*` classes in
`test_*.py` and `*_test.py` files. Marker matching is case-insensitive. This checks
structure, not whether the comments accurately describe the test; review still
checks their meaning. The checker is repository tooling, not a requirement for
projects using Agent Smith.

## Architecture

Keep argparse in the CLI adapter and wire dependencies in the composition root.
As generation is implemented, define small typed ports next to the application
capability that owns them, with `typing.Protocol`. Application code must not
import CLI or infrastructure adapters. Inject implementations for process and
filesystem access, and test the core with in-memory implementations. Do not add
unused ports or empty layers before a capability needs them.

Use short descriptive branch names without a `codex/` prefix. Keep commits atomic
and follow the [commit skill](.agents/skills/commit/SKILL.md): Conventional Commits,
an emoji at the end of the subject, and no agent co-author trailers.

Add tools, recipes, tests and ADRs in the PR that introduces their use. Follow the
[ADR skill](.agents/skills/adr/SKILL.md) for structural operations on decisions.
Keep tool entries in mise.toml in alphabetical order by tool name.
The optional `.editorconfig` conventions keep indentation, encoding and line
endings consistent across editors.

## Acknowledgements

The commit skill was inspired by the
[Cinematch commit helper](https://github.com/umans-ai/cinematch/blob/main/.claude/skills/commit/SKILL.md)
from umans-ai and adapted to Agent Smith's conventions.
