# 27. Require Python 3.11 or newer ahead of Python 3.10 end of life

Date: 2026-09-13

## Status

Accepted

Supercedes [4. Support maintained stable Python versions](0004-support-maintained-stable-python-versions.md)

## Context

Python 3.10 reaches end of life in October 2026, according to the
[Python version status](https://devguide.python.org/versions/) and
[endoflife.date](https://endoflife.date/python). It is still supported upstream
at the time of this decision. The maintainer explicitly chooses to retire it
now rather than wait until its end of life.

## Decision

Require Python >=3.11 and test Python 3.11 through 3.14 in CI. Target Python 3.11
in Ruff and ty, update the package classifiers and documentation, and regenerate
uv.lock. Keep Python 3.14.7 for daily development.

Use standard-library tomllib directly. Remove the Python 3.10 tomli runtime
fallback and the deptry exception that existed for its guarded tomllib import.

Waiting until October was an available alternative, but was not selected given
the maintainer's preference. No comparative benchmark was performed.

## Consequences

Users on Python 3.10 must upgrade their interpreter to install future releases.
Existing published releases remain available. Record this as a breaking change;
under the current zero-major release policy it triggers a minor version bump.
CI has four interpreter versions and the runtime no longer needs a TOML backport.
Historical ADRs retain their original context; this ADR replaces ADR 4's policy.
