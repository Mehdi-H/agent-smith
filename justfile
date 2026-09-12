set positional-arguments
set quiet

# List the repository's documented operations.
[group("Help")]
default:
    @just --list

# Manage architecture decisions with adr-tools (e.g. just adr new Use argparse).
[group("Decisions")]
adr +args:
    adr "$@"

# Install the pinned Python and synchronize the project from uv.lock.
[group("Environment")]
setup:
    uv python install
    uv sync --locked

# Run the CLI from the installed development environment.
[group("Environment")]
run *args:
    uv run --no-sync agent-smith "$@"

# Build a source distribution and a wheel using the uv backend.
[group("Packaging")]
build:
    uv build --no-sources

# Check lint, formatting, types, dependencies and fast tests without network or sync.
[group("Quality")]
check: lint types dependencies test-structure manifest-check skills-check
    sh scripts/feedback.sh "Fast tests" "Fix the failing assertions; use just test for full coverage reports." uv run --offline --no-sync pytest -q -m "not integration"

# Check Python lint rules and Python/justfile formatting without changing files.
[group("Quality")]
lint:
    sh scripts/feedback.sh "Justfile formatting" "Run just fmt-just, then review the diff." just --fmt --check
    sh scripts/feedback.sh "Ruff lint" "Fix the reported lint violations." uv run --offline --no-sync ruff check .
    sh scripts/feedback.sh "Python formatting" "Run just fmt, then review the diff." uv run --offline --no-sync ruff format --check .

# Verify that every just recipe is documented and belongs to a group.
[group("Quality")]
manifest-check *paths:
    sh scripts/feedback.sh "Usage manifest" "Add the missing recipe comments and group attributes." uv run --offline --no-sync python scripts/check_manifest.py "$@"

# Validate local skill structure strictly (optional skill or collection directory).
[group("Quality")]
skills-check path=".agents/skills":
    sh scripts/feedback.sh "Skill structure" "Fix the reported SKILL.md metadata or structure; warnings must also be resolved." skill-validator validate structure --strict "$1"

# Check types against the minimum supported Python; warnings fail the check.
[group("Quality")]
types:
    sh scripts/feedback.sh "Type checking" "Fix the reported type errors and warnings." uv run --offline --no-sync ty check --error-on-warning

# Detect missing, unused or incorrectly classified runtime dependencies.
[group("Quality")]
dependencies:
    sh scripts/feedback.sh "Dependency checking" "Align imports with runtime dependencies in pyproject.toml, then run just setup." uv run --offline --no-sync deptry src

# Show native pytest output for all tests, with branch coverage and XML/HTML reports.
[group("Tests")]
test:
    uv run --offline --no-sync pytest --cov-report=xml --cov-report=html || exit 1

# Verify Given/When/Then comments in Python tests (optional test files or directories).
[group("Tests")]
test-structure *paths:
    sh scripts/feedback.sh "Test structure" "Structure each reported test with # Given, # When and # Then comments." uv run --offline --no-sync python scripts/check_test_structure.py "$@"

# Apply Python and justfile formatting.
[group("Formatting")]
fmt: fmt-just
    uv run --offline --no-sync ruff format .

# Apply just's native formatting to the justfile.
[group("Formatting")]
fmt-just:
    just --fmt

# Build fresh artifacts and verify the wheel in an isolated environment.
[group("Packaging")]
package-check:
    sh scripts/feedback.sh "Package installation" "Fix the build or installed CLI behavior reported below." uv run --no-sync python scripts/check_package.py
