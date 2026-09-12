set positional-arguments
set quiet

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

# Check lint, formatting, types, dependencies and fast tests without network or sync.
check: lint types dependencies
    sh scripts/feedback.sh "Fast tests" "Fix the failing assertions; use just test for full coverage reports." uv run --offline --no-sync pytest -q -m "not integration"

# Check Python lint rules and Python/justfile formatting without changing files.
lint:
    sh scripts/feedback.sh "Justfile formatting" "Run just fmt-just, then review the diff." just --fmt --check
    sh scripts/feedback.sh "Ruff lint" "Fix the reported lint violations." uv run --offline --no-sync ruff check .
    sh scripts/feedback.sh "Python formatting" "Run just fmt, then review the diff." uv run --offline --no-sync ruff format --check .

# Check types against the minimum supported Python; warnings fail the check.
types:
    sh scripts/feedback.sh "Type checking" "Fix the reported type errors and warnings." uv run --offline --no-sync ty check --error-on-warning

# Detect missing, unused or incorrectly classified runtime dependencies.
dependencies:
    sh scripts/feedback.sh "Dependency checking" "Align imports with runtime dependencies in pyproject.toml, then run just setup." uv run --offline --no-sync deptry src

# Show native pytest output for all tests, with branch coverage and XML/HTML reports.
test:
    uv run --offline --no-sync pytest --cov-report=xml --cov-report=html || exit 1

# Apply Python and justfile formatting.
fmt: fmt-just
    uv run --offline --no-sync ruff format .

# Apply just's native formatting to the justfile.
fmt-just:
    just --fmt

# Build fresh artifacts and verify the wheel in an isolated environment.
package-check:
    sh scripts/feedback.sh "Package installation" "Fix the build or installed CLI behavior reported below." uv run --no-sync python scripts/check_package.py
