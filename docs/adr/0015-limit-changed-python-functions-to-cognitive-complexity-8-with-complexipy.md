# 15. Limit changed Python functions to cognitive complexity 8 with Complexipy

Date: 2026-09-12

## Status

Accepted

## Context

We want fast, actionable complexity feedback for the current branch without
forcing unrelated legacy functions to be refactored. The project owner selected
Complexipy and an absolute maximum cognitive complexity of eight.

## Decision

Use Complexipy 6.x as a uv-managed development dependency. `just complexity-check`
runs the selector through the shared shell feedback wrapper and is part of
`just check`, pre-commit and CI. Success is silent exit 0; violations or inability
to perform analysis return exit 1 with file, definition line, qualified function
name, measured score and the required maximum. A score of eight passes.

Compare the working tree, including staged changes and untracked Python files,
against the merge base of local `main` and HEAD. On local `main`, compare against
HEAD's parent. `COMPLEXITY_BASE` explicitly selects a comparison reference. CI
fetches complete history and supplies the PR base SHA or the pre-push SHA on main.
Missing history is an error, not a reason to silently skip analysis.

Parse changed Python files with the stdlib AST to locate functions, methods and
nested or async functions. Compare their source, including decorators and
comments, ignoring shifts in line numbers and enclosing indentation. Analyze
only added or modified definitions using Complexipy's code API. Removed
functions and unchanged functions are not gated. A change inside a nested
function also changes its enclosing function. Inline complexity suppressions
are disabled. All repository Python files are in scope, including tests and scripts.

Complexipy's native diff gate was inspected but allows already-complex functions
that do not increase in score. That does not satisfy our absolute limit for every
modified function. The small source selector preserves the stricter contract;
Complexipy remains responsible for computing cognitive complexity. Other
complexity tools were not comparatively evaluated.

## Consequences

Changed functions over eight must be refactored even if their score improved.
Functions with unchanged source may retain existing debt. The check does not
execute project code or the selected functions. Git history is required, and
local `main` must represent the intended integration branch; an explicit baseline
can be supplied when working with a different branch.

The parser and source-selection contract need tests alongside the feedback
contract. The runtime package gains no dependency from this development tool.

Reference: [Complexipy diff behavior](https://github.com/rohaquinlop/complexipy#complexity-diff).
