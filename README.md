# Agent Smith 🕶️

Build agent instructions from your project's sources.

Agent Smith will assemble deterministic Markdown from documented project
operations and configuration, with `AGENTS.md` as the default output.

**Status:** the development harness and installable CLI are available. Document
generation is not implemented yet, and no package release has been published.

## Getting started

Install [mise](https://mise.jdx.dev/) and clone this repository, then run:

```sh
mise trust
mise install
mise exec -- just setup
mise exec -- just run --help
mise exec -- just run --version
```

If mise is activated in your shell, you can call `just` directly. Run `just` for
the list of documented operations. `just build` produces a wheel and source
distribution in `dist/`; the package uses standard Python packaging metadata and
can be installed with pip or uv. It targets Python 3.10–3.14.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, commit
conventions and just-in-time architecture decisions. The license is [MIT](LICENSE).
