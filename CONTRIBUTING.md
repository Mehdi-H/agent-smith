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

> [!TIP]
> Run `just help` to discover commands with their descriptions and parameters.
> Running `just` displays the same help.

`just build` produces a wheel and source
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

## Record the terminal demo

After `just setup`, run `just demo` from the repository root. It uses VHS to
record the actual `agent-smith` command, waits for completion, checks its exit
status and shows two tmux panes side by side. On the left, `rm -f AGENTS.md`
starts from no generated file, then `agent-smith` creates it. On the right,
`watch` refreshes the Glow rendering every half second, then the demo switches
to `less -R` to scroll the same rendering down to the architecture decisions.
If recording fails,
the previous AGENTS.md is restored (or removed if it did not exist). It writes
`docs/demo/agent-smith.mp4` and
`docs/demo/agent-smith.gif`; only the GIF is versioned and embedded in the README.
The MP4 is a local export ignored by Git. This also
regenerates AGENTS.md, so review that diff with the recording.

VHS, Glow and tmux are pinned in mise.toml. Recording also requires FFmpeg,
ttyd, `less` and procps `watch` on PATH. On macOS, `less` is included; install the others with
`brew install ffmpeg ttyd watch`; on Debian/Ubuntu, use your package manager's
`ffmpeg`, `ttyd`, `less` and `procps` packages. The recorder uses a private tmux server
and closes it on exit, leaving existing terminal sessions alone. VHS may download a browser
on its first run. These media tools are not needed to use Agent Smith.

Edit `docs/demo/agent-smith.tape` to change the timing and commands,
`scripts/demo-layout.sh` for the panes, and `scripts/demo-preview.sh` for the
live preview. The preview removes terminal hyperlink metadata unsupported by
`watch`, while preserving the rendered text and colors. The Glow style in
`docs/demo/glow.json` uses ANSI colors compatible with watch, keeps link labels and hides long URL destinations for readability. Review the generated
GIF for readability and commit it with the scenario and Glow style. Rendering is
an explicit documentation task, not part of `just check`, pre-commit or CI.
The generated video is not expected to be byte-identical across platforms.

## Continuous integration

GitHub Actions runs `just check` on pull requests and pushes to `main`, using
Ubuntu and a Python 3.10–3.14 matrix. Each job installs the mise-pinned tools and
synchronizes uv.lock. `UV_PYTHON` selects the matrix interpreter instead of the
local `.python-version` pin. Keep this matrix aligned with the supported Python
classifiers in pyproject.toml.

After `just check`, CI runs `just test-integration` and `just test-functional`
on each matrix interpreter. Packaging and deployment are separate operations.

## Workflow security

Run `just workflows-check` to audit `.github/workflows` with the mise-pinned
Zizmor. It is included in `just check` and therefore in pre-commit and CI.
The audit runs offline, with strict collection so malformed workflows fail
instead of being skipped. Successful runs are silent; findings retain their
rule identifiers and source locations. Online audit rules are not run.

## Shell feedback

`just shellcheck-check` recursively checks `.sh` and `.bash` files under `scripts/`
with the mise-pinned ShellCheck. It is included in `just check`, pre-commit and CI.
ShellCheck uses each script's shebang to select its dialect. All default diagnostic
severities are enabled; no rules are suppressed. Success is silent, and failure
returns exit 1 with file, line and rule identifiers through the feedback wrapper.

## Python security feedback

`just bandit-check` scans Python application code and repository scripts with
Bandit. It is included in `just check` and fails on medium/high severity findings.
Low severity subprocess notices remain available through
`uv run --no-sync bandit -r src scripts`. Tests are outside this static-analysis
scope. The shell runner has one narrowly documented B602 exception: running
explicitly trusted user-configured shell commands is its intended contract.

`just audit-check` exports all runtime and development dependencies from uv.lock
into a temporary requirements file with hashes and audits their pinned versions with
[pip-audit](https://github.com/pypa/pip-audit), maintained by the PyPA. It needs
network access to the public vulnerability database, but no account or API key.
Dependency resolution and package installation are disabled during the audit;
the export comes from the existing lockfile. Environment markers select the
dependencies applicable to the interpreter/platform running the audit. The wrapper preserves diagnostics
and maps findings or operational errors to exit 1, with silent success.

The audit stays separate from `just check`, pre-commit and CI to keep the fast
check offline. Run it explicitly when network access is available. Bandit and
pip-audit are development dependencies locked by uv; neither is installed for
CLI consumers. See [the security feedback decision](docs/adr/0020-audit-python-security-with-bandit-and-pip-audit-feedback-checks.md).

## Git hooks

`just setup` installs Lefthook's pre-commit hook for this checkout. After updating
an existing checkout, run `mise install` and `just hooks-install` to enable it.
Every commit runs `just check` and `just cli-check`; a failure blocks the commit.
`just cli-check` invokes the installed `agent-smith --help` command through uv,
offline and without synchronizing dependencies. This verifies startup without
generating an output file as a side effect of committing.

Run `just hooks-check` to execute the hook manually. Lefthook displays a progress
summary while successful checks stay quiet.

> [!IMPORTANT]
> Hooks use mise to resolve the pinned tools. Ensure mise is on the PATH of the
> terminal or IDE that runs Git.

> [!WARNING]
> Hooks inspect the working tree, including changes that are not staged. Review
> partially staged changes before committing: a passing check does not validate
> the staged snapshot in isolation.

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

> [!NOTE]
> `just test` displays pytest's native output even on success, while still
> returning 1 on any failure. `just check` is silent on success for agents.

Commands that generate section content have a different contract: their stdout
is the content. Do not wrap those producers in the silent feedback wrapper.
Instructions and ADRs guide work before execution; these checks provide feedback
after execution.

## Changed-function complexity

Run `just complexity-check` to enforce a Complexipy cognitive complexity of at
most **8** on added or modified Python functions, including tests and scripts.
It is included in `just check`. Refactor reported functions; do not suppress the
check. Diagnostics identify the file, line, function and measured score.

The comparison uses the merge base with local `main`, including local staged,
unstaged and untracked Python changes. On `main` it uses the previous commit.
Use `COMPLEXITY_BASE=<git-ref> just complexity-check` for another baseline.
CI supplies the PR base or pre-push commit and fetches the required history.
Unchanged functions are ignored even when they exceed the limit; changed
functions must meet the limit even when their score decreased.

## Sociable tests and explicit dependencies

Prefer direct tests with real, fast collaborators. Inject mocks, stubs or fakes
when needed at boundaries; do not replace dependencies through global patching.
This applies to fixtures and helpers as well as test functions. Follow
[our sociable testing decision](docs/adr/0016-prefer-sociable-tests-and-injected-doubles-over-patching.md).

`just test-doubles-check` is included in `just check`. It rejects textual uses of
`monkeypatch`, `patch` and related API names in all Python test sources, including
comments and strings, with a file and line diagnostic. This lightweight guard
does not replace review of other runtime replacement techniques. Explicitly
injected `unittest.mock.Mock` objects are allowed.

## Skill structure

Run `just skills-check` to validate `.agents/skills`, or `just skills-check PATH`
for a single skill or another collection. This check is included in `just check`.
The mise-pinned skill-validator checks local metadata, structure, Markdown fences
and internal references. Strict mode treats warnings as failures; the shared
wrapper keeps successful runs silent. Remote link checks and LLM scoring are not
part of this fast check. Structural validity does not establish that instructions
are correct or useful; review their meaning too.

## Test structure

Follow the test pyramid: put isolated rules and application cases in `tests/unit`,
real adapter contracts in `tests/integration`, and a few complete installed-CLI
journeys in `tests/functional`. Use directories rather than duplicate markers.
Run `just tests-pyramid` to display the collected case count and percentage for each level
without running tests. Each parametrized case counts separately.
Run a level with `just test-unit`, `just test-integration` or
`just test-functional`; `just test` runs all levels. `just check` selects only
unit tests for its fast loop. Favor unit tests for edge cases without enforcing
an artificial percentage or duplicating coverage across levels.

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
The generation application owns typed ports for its inputs and effectful
adapters, using `typing.Protocol`. Application code must not
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
