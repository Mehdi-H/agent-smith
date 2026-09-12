# 4. Support maintained stable Python versions

Date: 2026-09-12

## Status

Superceded by [27. Require Python 3.11 or newer ahead of Python 3.10 end of life](0027-require-python-3-11-or-newer-ahead-of-python-3-10-end-of-life.md)

## Context

Agent Smith is distributed to projects using different supported Python versions. On 2026-09-12, maintained stable versions are 3.10 through 3.14; Python 3.15 is not yet stable.

## Decision

Declare Python >=3.10 and target compatible syntax and standard-library APIs. Use Python 3.14.7 for daily development. Track supported versions against https://devguide.python.org/versions/. Add a test matrix with the CI increment and update the minimum through a reviewed change when support ends.

## Consequences

The newest interpreter must not hide incompatibilities with older supported interpreters. Development tooling can run on the development interpreter while package tests run on supported versions. Classifiers describe the support target, not a claim that CI already exists. Python 3.10 reaches end of life in October 2026.
