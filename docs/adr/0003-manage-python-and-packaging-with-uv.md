# 3. Manage Python and packaging with uv

Date: 2026-09-12

## Status

Accepted

## Context

We need a standard installable Python package, reproducible development dependencies, and one owner for the Python interpreter. Contributors use different package installers.

This records the requested use of uv and the implementation choice to give it ownership of Python. mise was discussed as an alternative interpreter manager; pip with venv is another known installation approach. These alternatives were not evaluated comparatively or benchmarked. The src layout and uv_build fit the pure-Python packaging requirements; no build-backend comparison was performed.

## Decision

Use uv for Python installation, virtual environments, dependency locking and builds. Pin Python in .python-version and uv in mise.toml; mise manages development CLI tools, not Python. Use the uv_build backend with a pinned version and the src layout. Declare the standard console entry point in pyproject.toml. Start at unpublished version 0.0.0 until release automation is introduced.

## Consequences

pip and other PEP 517-compatible installers can install the package without uv. Developers run just setup before using the package. uv.lock records the development resolution; users resolve runtime requirements from package metadata. Compared with also managing Python through mise, a single owner avoids conflicting interpreter selections. Native extensions would require reconsidering uv_build.
