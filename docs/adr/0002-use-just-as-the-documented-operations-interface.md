# 2. Use justfiles as self-documented usage manifests

Date: 2026-09-12

## Status

Accepted

## Context

Humans and agents need discoverable operations that can also be reused by future
CI workflows. Separate shell instructions in documentation and CI would drift.

This records the maintainer's choice of an autodocumented justfile. Make is a known alternative, also mentioned in the companion article; no comparative trial was performed.

## Decision

Use the justfile as a self-documented usage manifest: an executable interface
contract for someone discovering the repository. Its help is generated from the
actual recipe names, parameters, groups and adjacent descriptions. Descriptions
explain the operation's purpose; implementation commands stay in the recipes.
Running `just` presents the available usages, grouped by intent, without having
to read the implementation. Every recipe must have a description and a group;
`just manifest-check` verifies these structural requirements.

This applies the pattern described in
[Living documentation, parce que la doc, ça peut être fun !](https://blog.octo.com/living-documentation-parce-que-la-doc-ca-peut-etre-fun-%21),
whose Makefile example expresses the same intent. We use just's native discovery
instead of maintaining a separate inventory of commands in prose.

Pin just and adr-tools in mise.toml. Introduce further
tools and recipes only when they serve implemented capabilities. Future CI `run`
steps will call just recipes; setup and artifact actions can use GitHub actions.

## Consequences

Local and automated runs share commands. mise must bootstrap just before its
recipes can run. Recipes may call small scripts when logic grows, but remain the
documented entry point. Unlike Make, just does not infer file build dependencies,
which suits explicit checks and development operations.

Generated help stays linked to executable usages. Review still checks whether a
description is useful and accurate: the presence check cannot establish meaning.
