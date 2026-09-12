# 23. Publish the agent-smith-cli distribution because agent-smith is taken

Date: 2026-09-12

## Status

Accepted

## Context

The `agent-smith` distribution name is already occupied on PyPI. The maintainer
selected `agent-smith-cli` and registered a pending trusted publisher for it.

The issue motivating this decision, and any context that influences or constrains the decision.

## Decision

Publish as `agent-smith-cli`, keeping the `agent-smith` executable and
`agent_smith` Python module. Configure the build backend explicitly and resolve
runtime version metadata using the distribution name.

`agent-smith-md` and `smith-agents` were naming suggestions, not benchmarked
alternatives. This documents the chosen name, not a comparative study.

The change that we're proposing or have agreed to implement.

## Consequences

Installers use `agent-smith-cli`; existing CLI invocations remain unchanged.
The initial PyPI publication must match the pending publisher name.

What becomes easier or more difficult to do and any risks introduced by the change that will need to be mitigated.
