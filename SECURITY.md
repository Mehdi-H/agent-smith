# Security Policy

## Supported versions

Only the latest published release is supported. It targets Python 3.11 and
newer. Older releases do not receive security fixes; upgrade before reporting.

## Reporting a vulnerability

Do not open a public issue for a vulnerability report. Use GitHub's private
vulnerability reporting instead:

<https://github.com/Mehdi-H/agent-smith/security/advisories/new>

A useful report includes the affected version, your environment, the steps to
reproduce the issue and, when relevant, an estimate of its impact. Keep
exploit details out of any public channel until a fix is available.

## What this policy does not cover

Vulnerabilities in development tooling, CI configuration or the demo
recordings are out of scope for private reporting; raise them as regular
public issues. For vulnerabilities in locked dependencies, the maintainers run
`just audit-check` (pip-audit) with network access; see
[the contributing guide](CONTRIBUTING.md#python-security-feedback).
