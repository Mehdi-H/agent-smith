---
name: commit
description: Prepare and create atomic Conventional Commits for this repository.
---

Inspect the staged diff before choosing a message. Each commit must have one
coherent purpose. Stage only related files and preserve unrelated user changes.

Use `type(scope): description emoji`, with an optional scope. Types and emojis:
`feat` ✨, `fix` 🐛, `docs` 📝, `style` 💄, `refactor` ♻️, `perf` ⚡,
`test` ✅, `build` 📦, `ci` 🔧, `chore` 🧹.

Use `feat` for new behavior and `fix` for corrections. These will drive minor and
patch releases respectively; `perf` will also drive patch releases. Mark breaking
changes with `!` and explain them in a `BREAKING CHANGE:` footer. Before 1.0, breaking changes bump the minor version; reaching 1.0 requires an
explicit policy change. Do not mislabel
changes to force a release.

Do not add `Co-Authored-By` trailers for agents. Keep credentials and local
environment files out of commits. Use documented just recipes for relevant
verification and report any checks that could not run. Do not push unless asked.
