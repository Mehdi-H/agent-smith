# 37. Support Python 3.11 through 3.15 and report coverage from Python 3.15

Date: 2026-10-12

## Status

Accepted

Supercedes [27. Require Python 3.11 or newer ahead of Python 3.10 end of life](0027-require-python-3-11-or-newer-ahead-of-python-3-10-end-of-life.md)

Amends [10. Run just check in GitHub Actions on Python 3.10 through 3.14](0010-run-just-check-in-github-actions-on-python-3-10-through-3-14.md)

## Context

Python 3.15.0 was released on 2026-10-09, according to the
[Python version status](https://devguide.python.org/versions/) and
[endoflife.date](https://endoflife.date/python). Issue #41 asks to add it to the
tested and declared versions. The maintainer explicitly requires the final
release in CI, not a release candidate.

uv 0.12.19 resolved `3.15` to 3.15.0rc2. uv 0.13.0, released on 2026-10-09, is
the first uv release that downloads Python 3.15.0; mise.toml already pins it.

## Decision

Keep Python >=3.11, and test Python 3.11 through 3.15 in CI. Declare the Python
3.15 classifier. Upload coverage and Test Analytics reports to Codecov only from
the newest tested interpreter, Python 3.15, on main; this replaces the Python
3.14 reporting interpreter mentioned in ADR 28.

Keep uv 0.13.0 or newer in mise.toml so CI installs Python 3.15.0 rather than a
release candidate.

ADR 27's other decisions still hold: Ruff and ty target Python 3.11 and the runtime
uses standard-library tomllib. Daily development moves from Python 3.14.7 to
Python 3.15.0 through `.python-version`.
ADR 10 still selects `just check` in GitHub Actions; its 3.10–3.14 matrix is
replaced by this range.

Testing a release candidate was an available alternative, but was not selected
given the maintainer's preference for the final release. No comparative
benchmark was performed. `just check` and `just test` passed locally
on Python 3.15.0 with the locked dependencies.

## Consequences

CI runs five interpreter versions. Adding the next Python version follows the
same steps: matrix, classifier, Codecov condition and documentation. Downgrading
uv below 0.13.0 would silently test a Python 3.15 release candidate.
