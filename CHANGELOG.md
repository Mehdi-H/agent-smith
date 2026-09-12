# CHANGELOG

<!-- version list -->

## v0.3.0 (2026-09-12)

Changes introduced by [PR #5](https://github.com/Mehdi-H/agent-smith/pull/5).

### Features

- generate a compact architecture decision index with adr list ([`75d2692`](https://github.com/Mehdi-H/agent-smith/commit/75d269206f25e5cbcdcecf4f7d02103f6417f028))

### Documentation

- demonstrate architecture decisions with a scrolling preview ([`82e1252`](https://github.com/Mehdi-H/agent-smith/commit/82e1252f46737608f5fdd5d84fafa8e277888719))

**Full Changelog:** [compare changes](https://github.com/Mehdi-H/agent-smith/compare/883dd8cdba896eb4308b61133260928934dac81e...82e1252f46737608f5fdd5d84fafa8e277888719)

## v0.2.0 (2026-09-12)

Changes introduced by [PR #4](https://github.com/Mehdi-H/agent-smith/pull/4).

### Features

- generate the main tech stack from mise declarations ([`c3bd9ea`](https://github.com/Mehdi-H/agent-smith/commit/c3bd9eaf7b4d986f82b5578bcaf16dbd1865e949))

### Documentation

- refresh the demo with the main tech stack ([`883dd8c`](https://github.com/Mehdi-H/agent-smith/commit/883dd8cdba896eb4308b61133260928934dac81e))

### Chores

- require a verified demo in the merge checklist ([`6628edf`](https://github.com/Mehdi-H/agent-smith/commit/6628edfd16bc51a2dbc47b93adf5f0fd19ae08f1))
- report test pyramid counts and percentages ([`bf3d1f1`](https://github.com/Mehdi-H/agent-smith/commit/bf3d1f1b6a644e66207478bce18e2df8c698d03e))
- add Bandit and pip-audit security feedback ([`9fa4156`](https://github.com/Mehdi-H/agent-smith/commit/9fa41567e8a9ec43324df1b85751bbfe4ba9a4cb))
- check shell scripts with ShellCheck ([`0cebf4b`](https://github.com/Mehdi-H/agent-smith/commit/0cebf4baee051406c1b10fa7f58ae4495dc64609))

**Full Changelog:** [compare changes](https://github.com/Mehdi-H/agent-smith/compare/3873abb6dc5b505baf1fab46268096857bc142ad...883dd8cdba896eb4308b61133260928934dac81e)

## v0.1.0 (2026-09-12)

Changes introduced by [PR #3](https://github.com/Mehdi-H/agent-smith/pull/3).

### Features

- generate grouped available commands from just help ([`855e418`](https://github.com/Mehdi-H/agent-smith/commit/855e4181ecc7f107afc08088318abc5e0e5a28dd))

### Documentation

- add a reproducible CLI demo with a live Glow preview ([`3873abb`](https://github.com/Mehdi-H/agent-smith/commit/3873abb6dc5b505baf1fab46268096857bc142ad))

### Chores

- check project versions before rebasing pull requests ([`1d84911`](https://github.com/Mehdi-H/agent-smith/commit/1d84911620ab89217116f9eafc2307e5bb630b56))

**Full Changelog:** [compare changes](https://github.com/Mehdi-H/agent-smith/compare/e9eb78746abd8604839d6f365748afd1eac6043c...3873abb6dc5b505baf1fab46268096857bc142ad)

## v0.0.0 (2026-09-12)

Initial release, combining [PR #1](https://github.com/Mehdi-H/agent-smith/pull/1) and [PR #2](https://github.com/Mehdi-H/agent-smith/pull/2).

### Features

- **cli:** add an installable argparse entry point ([`71178b8`](https://github.com/Mehdi-H/agent-smith/commit/71178b877e1da61375afe26516644e629250903b))
- generate README overview and configurable Markdown sections ([`fdbf78c`](https://github.com/Mehdi-H/agent-smith/commit/fdbf78cd1307ce255e74436503e1fa8dbf5022ad))
- enforce complexity eight on changed Python functions ([`cbb5275`](https://github.com/Mehdi-H/agent-smith/commit/cbb52757d7d2ebbb1d50b733bb580b69a32fbca3))

### Documentation

- simplify setup commands and expose just help ([`3de5b3a`](https://github.com/Mehdi-H/agent-smith/commit/3de5b3ad07dcf567303c8bf7f15e029f959fccbd))
- polish README and contributor guidance ([`934ca3f`](https://github.com/Mehdi-H/agent-smith/commit/934ca3f03f7c99bbe19f986f55b863091a5fda3e))

### Build System

- establish contribution and ADR harness ([`20aec8e`](https://github.com/Mehdi-H/agent-smith/commit/20aec8e5d4343bd81dd3b029577b0110c353bd0a))
- add strict checks with silent success feedback ([`d86dd2e`](https://github.com/Mehdi-H/agent-smith/commit/d86dd2e855a3e68593a0b75b5dd11c992cf64590))
- validate the grouped self-documented usage manifest ([`0f2241c`](https://github.com/Mehdi-H/agent-smith/commit/0f2241cbac4492470fa4ee1babd45ef495eecbf3))
- validate skill structure with skill-validator ([`de21e7b`](https://github.com/Mehdi-H/agent-smith/commit/de21e7bb450b8bd240e9efc220a55e1b8b50f9f6))
- **hooks:** check quality and CLI startup before commits ([`c448072`](https://github.com/Mehdi-H/agent-smith/commit/c4480722ff5889c72dd3f3a3ac34aa69ea19db08))
- audit workflow security with Zizmor in just check ([`2900109`](https://github.com/Mehdi-H/agent-smith/commit/2900109eb9e5703f75d414b36d6baf6c443e6d1b))

### Continuous Integration

- run just check across supported Python versions ([`77a536d`](https://github.com/Mehdi-H/agent-smith/commit/77a536db1e9bca2a83f830e0ec2653e22f6ec1ba))

### Tests

- enforce given when then structure in tests ([`6d28578`](https://github.com/Mehdi-H/agent-smith/commit/6d28578b2f41ed694b01d10de626145f5947a100))
- organize unit integration and functional test suites ([`395b412`](https://github.com/Mehdi-H/agent-smith/commit/395b4127a18a1370dced1b4405d0ce1efa0cca68))
- enforce sociable tests without patching ([`e9eb787`](https://github.com/Mehdi-H/agent-smith/commit/e9eb78746abd8604839d6f365748afd1eac6043c))

**Full Changelog:** [compare changes](https://github.com/Mehdi-H/agent-smith/compare/640a367c029b515b2e6093a2bf58767d3b90a656...e9eb78746abd8604839d6f365748afd1eac6043c)
