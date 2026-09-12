# 28. Check completed GitHub Actions runs for warning annotations

Date: 2026-09-13

## Status

Accepted

## Context

Successful GitHub Actions runs can still report deprecated actions and runtimes.
The maintainer wants actionable feedback for these warnings, not just green jobs.

## Decision

Use `just workflow-warnings` to inspect every job's warning and failure
annotations for each workflow's latest successful main run through the GitHub CLI API.
Paginate runs, jobs and annotations. Group successful main runs by workflow ID
and select the newest run ID in each group. Running and failed runs do not block
selection of a previous success. Require inspectable jobs;
API failures or missing results must not produce a false success.
Return 0 silently when clean, otherwise return 1 with check URLs and diagnostics.
Pin gh through mise. Keep this network/authenticated check outside offline just check.

Replace the deprecated Codecov test-results action with codecov-action v7 using
report_type: test_results, and use that version for coverage too. Its nested
github-script v8 uses Node 24. Keep OIDC and main-only uploads, and restrict both
reports to Python 3.14 at the maintainer's request. Other supported Python
versions still run all tests, but do not contribute coverage or Test Analytics.

Parsing console logs was considered but not pursued: the annotations API provides
the same structured warnings shown by GitHub. No comparative benchmark was run.

## Consequences

Historical runs retain their warnings. Validate the next main run after each correction.
This checks historical successful runs rather than current CI health; validate the main run after
merge as well. GitHub authentication and network access are required; API or
permission failures are reported rather than interpreted as no warnings.
