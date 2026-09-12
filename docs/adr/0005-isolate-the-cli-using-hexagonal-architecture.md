# 5. Isolate the CLI using hexagonal architecture

Date: 2026-09-12

## Status

Accepted

## Context

Agent Smith will assemble Markdown from project sources. Its behavior must be testable independently of argument parsing, process execution and filesystem access, and replacing the CLI library must not require rewriting generation.

This records the explicitly requested architectural principles and the accepted argparse choice. Click and Typer were identified and discussed at a documentation level. Neither was prototyped or benchmarked for Agent Smith.

## Decision

Follow the three principles in the OCTO article: separate user adapters, business logic and infrastructure; point dependencies inward; define ports at the boundaries. Use argparse only in the CLI adapter. The composition root supplies installation metadata. As generation is introduced, define focused typing.Protocol interfaces beside the application capabilities that own them, inject infrastructure adapters, and pass ordinary typed requests and results across the CLI boundary. Keep argparse.Namespace, sys.exit, subprocess and filesystem operations outside the core. Use explicit composition, without a dependency injection framework.

## Consequences

For this increment, help and version are adapter concerns: no artificial generation service or unused ports are created. Later application tests can call incoming ports directly and provide small in-memory implementations of outgoing ports. Adapters will have integration and shared contract tests so replacements preserve behavior. SOLID means focused responsibilities and small substitutable interfaces, not an interface for every class. Argparse avoids runtime dependencies; Click or Typer could replace this adapter later.

Reference: https://blog.octo.com/architecture-hexagonale-trois-principes-et-un-exemple-dimplementation
