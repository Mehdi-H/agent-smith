# 2. Use just as the documented operations interface

Date: 2026-09-12

## Status

Accepted

## Context

Humans and agents need discoverable operations that can also be reused by future
CI workflows. Separate shell instructions in documentation and CI would drift.

## Decision

Use commented just recipes as the repository's operations interface. Running
`just` lists those recipes. Pin just and adr-tools in mise.toml. Introduce further
tools and recipes only when they serve implemented capabilities. Future CI `run`
steps will call just recipes; setup and artifact actions can use GitHub actions.

## Consequences

Local and automated runs share commands. mise must bootstrap just before its
recipes can run. Recipes may call small scripts when logic grows, but remain the
documented entry point. Unlike Make, just does not infer file build dependencies,
which suits explicit checks and development operations.
