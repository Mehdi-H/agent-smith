set positional-arguments
set quiet

# List the repository's documented operations.
[group("Help")]
help:
    @just --list

# Record a real CLI demonstration as MP4 and GIF under docs/demo.
[group("Documentation")]
demo:
    sh scripts/record-demo.sh

# Manage architecture decisions with adr-tools (e.g. just adr new Use argparse).
[group("Decisions")]
adr +args:
    adr "$@"

# Install Python, synchronize uv.lock dependencies and install Git hooks.
[group("Environment")]
setup:
    uv python install
    uv sync --locked --group release
    just hooks-install

# Install the repository's Lefthook Git hooks in this checkout.
[group("Hooks")]
hooks-install:
    mise exec -- lefthook install

# Run the pre-commit checks manually without creating a commit.
[group("Hooks")]
hooks-check:
    mise exec -- lefthook run pre-commit --force

# Verify CLI startup through help without generating a file during pre-commit.
[group("Quality")]
cli-check:
    sh scripts/feedback.sh "Agent Smith CLI" "Run just setup for installation issues, or fix the CLI failure reported below." uv run --offline --no-sync agent-smith --help

# Run the CLI from the installed development environment.
[group("Environment")]
run *args:
    uv run --no-sync agent-smith "$@"

# Build a source distribution and a wheel using the uv backend.
[group("Packaging")]
build:
    rm -f dist/*.whl dist/*.tar.gz
    uv build --no-sources

# Check lint, formatting, types, dependencies and fast tests without network or sync.
[group("Quality")]
check: lint types dependencies bandit-check shellcheck-check complexity-check test-doubles-check test-structure manifest-check skills-check workflows-check
    sh scripts/feedback.sh "Unit tests" "Fix the failing assertions; use just test for full coverage reports." uv run --offline --no-sync pytest -q tests/unit

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

# Audit GitHub Actions security offline, failing on malformed workflows too.
[group("Quality")]
workflows-check:
    sh scripts/feedback.sh "Workflow security" "Fix the Zizmor findings in .github/workflows; inspect the reported rule and location." zizmor --offline --strict-collection --no-progress .github/workflows

# Validate local skill structure strictly (optional skill or collection directory).
[group("Quality")]
skills-check path=".agents/skills":
    sh scripts/feedback.sh "Skill structure" "Fix the reported SKILL.md metadata or structure; warnings must also be resolved." skill-validator validate structure --strict "$1"

# Check types against the minimum supported Python; warnings fail the check.
[group("Quality")]
types:
    sh scripts/feedback.sh "Type checking" "Fix the reported type errors and warnings." uv run --offline --no-sync ty check --error-on-warning

# Limit changed Python functions to cognitive complexity 8 against the branch baseline.
[group("Quality")]
complexity-check:
    sh scripts/feedback.sh "Changed function complexity" "Refactor each reported function to complexity 8 or less; set COMPLEXITY_BASE to override the Git baseline." uv run --offline --no-sync python scripts/check_complexity.py

# Detect missing, unused or incorrectly classified runtime dependencies.
[group("Quality")]
dependencies:
    sh scripts/feedback.sh "Dependency checking" "Align imports with runtime dependencies in pyproject.toml, then run just setup." uv run --offline --no-sync deptry src

# Run all tests with branch coverage, XML/HTML reports and JUnit test results.
[group("Tests")]
test:
    uv run --offline --no-sync pytest --cov-report=xml --cov-report=html --junitxml=junit.xml -o junit_family=legacy || exit 1

# Run fast unit tests in isolation from files and subprocesses.
[group("Tests")]
test-unit:
    uv run --offline --no-sync pytest tests/unit || exit 1

# Run focused integration tests against real adapters and tools.
[group("Tests")]
test-integration:
    uv run --offline --no-sync pytest tests/integration || exit 1

# Run user scenarios through the installed CLI in a separate process.
[group("Tests")]
test-functional:
    uv run --offline --no-sync pytest tests/functional || exit 1

# Reject patching in tests; use real collaborators or explicitly injected doubles.
[group("Quality")]
test-doubles-check:
    sh scripts/feedback.sh "Test doubles" "Remove patching; inject collaborators or exercise real behavior in sociable tests." uv run --offline --no-sync python scripts/check_test_doubles.py

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

# Count collected test cases by pyramid level without executing them.
[group("Tests")]
tests-pyramid:
    uv run --offline --no-sync python scripts/tests_pyramid.py

# Audit Python source and tooling for medium/high severity security findings.
[group("Quality")]
bandit-check:
    sh scripts/feedback.sh "Bandit" "Fix the reported security issue; keep exceptions narrow and justified." uv run --offline --no-sync bandit -r src scripts --severity-level medium

# Audit locked Python dependencies for known vulnerabilities (network required).
[group("Quality")]
audit-check:
    sh scripts/feedback.sh "pip-audit" "Update vulnerable dependencies and uv.lock, or resolve the reported network error." sh scripts/check_audit.sh

# Check all .sh and .bash scripts recursively with ShellCheck.
[group("Quality")]
shellcheck-check:
    sh scripts/feedback.sh "ShellCheck" "Fix the shell diagnostics at the reported files and lines." find scripts -type f \( -name '*.sh' -o -name '*.bash' \) -exec shellcheck {} +

# Preview committed changes as main in a disposable clone without publishing.
[group("Release")]
release-preview:
    uv run --locked --group release sh scripts/release-preview.sh

# Synchronize the stamped version and build verified release distributions.
[group("Release")]
release-build:
    uv lock --upgrade-package agent-smith-cli
    just build
    just distributions-check

# Verify the exact wheel and sdist in dist before publication.
[group("Release")]
distributions-check:
    uv run --offline --no-sync python scripts/check_distributions.py

# Create the next semantic release from the checked main workflow.
[group("Release")]
release:
    sh scripts/release.sh

# Upload the built distributions to the current GitHub release.
[group("Release")]
publish-github:
    sh scripts/release-guard.sh
    uv run --locked --group release semantic-release publish

# Publish verified distributions to PyPI through the main workflow's OIDC identity.
[group("Release")]
publish-pypi:
    sh scripts/release-guard.sh
    uv publish --trusted-publishing always --check-url https://pypi.org/simple/ dist/*.whl dist/*.tar.gz

# Recover existing release assets for a PyPI retry without another version bump.
[group("Release")]
release-recover tag:
    sh scripts/release-recover.sh "$1"

# Check annotations from the latest successful main run of each workflow (network and gh auth required).
[group("Quality")]
workflow-warnings:
    sh scripts/feedback.sh "Workflow annotations" "Fix the reported actions, rerun the workflow, then check the latest main run again." sh scripts/workflow-warnings.sh
