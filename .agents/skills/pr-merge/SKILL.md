---
name: pr-merge
description: Prepare and merge a repository pull request, checking its version bump, atomic history and CI before rebasing into main.
---

Merge only when the user has authorized it. That authorization covers the
necessary preparation below; do not request it again after checks pass.

Fetch the remote and inspect the PR base, head, working tree and checks. Preserve
unrelated local changes. Review the commit history for fixups that belong with
an earlier change, while retaining independent atomic Conventional Commits.
Before rewriting history, keep a local backup and verify that the resulting
file tree is unchanged. Push rewritten history with an explicit force-with-lease.

Before merging a product change, compare `[project].version` in pyproject.toml
against the PR base. Include the version bump in this PR: increment the minor
version for a new feature and the patch version for a compatible fix. Honor a
version explicitly chosen by the user. For breaking changes, settle the intended
version before proceeding; the pre-1.0 breaking-change policy is not yet defined.
Do not bump again if this PR already contains the appropriate increase, and do
not invent a product release for documentation-only or tooling-only changes.

Update uv.lock with the version, synchronize the environment and verify
`agent-smith --version` through uv. Update any documentation that states the
version. A version bump alone does not authorize publishing a package, creating
a release or adding release automation.

Complete this checklist before merging:

- [ ] CI is green for the current PR's exact final head, on every supported Python version.
- [ ] `just check` passes locally on the final changes.
- [ ] Regenerate the demo with `just demo`, inspect the GIF visually to confirm it is not
  broken (command, live preview, timing and readability), and commit the refreshed artifacts.
- [ ] The project version has been bumped in pyproject.toml and uv.lock as described above.

Regenerate and commit the demo before checking final-head CI. A successful recorder
exit alone does not establish that the GIF renders correctly.

Run the relevant documented just checks and refresh the PR description to match
the final change and validation. Take the PR out of draft and require successful
CI on its exact final head, including all supported Python versions. Merge using
GitHub's rebase method with `--match-head-commit`; do not create a merge commit or
squash all independent commits together.

Verify the PR is merged, update the local main branch by fast-forward, and verify
the resulting main CI. Report the PR link, history cleanup and validation status.
