---
name: pr-merge
description: Prepare and merge a repository pull request, checking its release policy, atomic history and CI before rebasing into main.
---

Merge only when the user has authorized it. That authorization covers the
necessary preparation below; do not request it again after checks pass.

Fetch the remote and inspect the PR base, head, working tree and checks. Preserve
unrelated local changes. Review the commit history for fixups that belong with
an earlier change, while retaining independent atomic Conventional Commits.
Before rewriting history, keep a local backup and verify that the resulting
file tree is unchanged. Push rewritten history with an explicit force-with-lease.

Versioning is automated by Python Semantic Release on main. Do not manually bump
pyproject.toml or uv.lock in feature PRs. Review Conventional Commits: feat bumps
minor, fix/perf bump patch, and breaking changes bump minor while below 1.0.
Documentation and tooling alone do not trigger a release. A transition to 1.0
requires an explicit maintainer decision. Check the release workflow after merge;
report failed publication separately from a successful merge.

Complete this checklist before merging:

- [ ] CI is green for the current PR's exact final head, on every supported Python version.
- [ ] `just check` passes locally on the final changes.
- [ ] Regenerate the demo with `just demo`, inspect the GIF visually to confirm it is not
  broken (command, live preview, timing and readability), and commit the refreshed artifacts.
- [ ] Commit messages express the intended release level; version files stay synchronized.

Regenerate and commit the demo before checking final-head CI. A successful recorder
exit alone does not establish that the GIF renders correctly.

Run the relevant documented just checks and refresh the PR description to match
the final change and validation. Take the PR out of draft and require successful
CI on its exact final head, including all supported Python versions. Merge using
GitHub's rebase method with `--match-head-commit`; do not create a merge commit or
squash all independent commits together.

Verify the PR is merged, update the local main branch by fast-forward, and verify
the resulting main CI. Report the PR link, history cleanup and validation status.
