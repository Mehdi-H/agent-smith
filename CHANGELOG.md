# CHANGELOG

<!-- version list -->

## v0.6.0 (2026-09-16)

### Chores

- Update tools and lock Python dependencies 🧹
  ([`f89c5cc`](https://github.com/Mehdi-H/agent-smith/commit/f89c5cc90d490f08f7e2bb4aa88fa7125aa24341))

- **quality**: Add repository-wide check harness 🧹
  ([`9451870`](https://github.com/Mehdi-H/agent-smith/commit/9451870d9e5d9fef7d6e826ffd45e4465c022e35))

- **security**: Scan commits for secrets with Betterleaks 🧹
  ([`e5fcd83`](https://github.com/Mehdi-H/agent-smith/commit/e5fcd832864a5cdf4e4acb7ad2b111dcf5060a9b))

### Documentation

- Refresh terminal demonstration 📝
  ([`41c79a3`](https://github.com/Mehdi-H/agent-smith/commit/41c79a340e60abd0eeffc38a4a5bd7b60ccbbccd))

- Refresh terminal demonstration 📝
  ([`443d0b5`](https://github.com/Mehdi-H/agent-smith/commit/443d0b5f99f6da70bc6147da34361c9ea7fca502))

- **readme**: Refresh introduction and conventions 📝
  ([`ec33d90`](https://github.com/Mehdi-H/agent-smith/commit/ec33d90ed9a29f8fbddd176b989a9041db6a4273))

### Features

- **quality**: Enforce Action SHA pinning with update check ✨
  ([`6f34958`](https://github.com/Mehdi-H/agent-smith/commit/6f349588d6206cb8584e51d836e0e2842e2348fc))

### Refactoring

- Unify Python feedback check contracts ♻️
  ([`7289eef`](https://github.com/Mehdi-H/agent-smith/commit/7289eef79cd4bdf514aec33d923c4c3c57cc3e7b))


## v0.5.0 (2026-09-12)

### Chores

- Check dependency updates with a seven-day Python cooldown 🧹
  ([`ee124ff`](https://github.com/Mehdi-H/agent-smith/commit/ee124ff84c1671b949b7de091d3ed0a731ceb3de))

- Share agent instructions with Claude Code via symlink 🧹
  ([`f5e76f6`](https://github.com/Mehdi-H/agent-smith/commit/f5e76f6dd0069700e5bddbd296ce9fe0d8fdb37e))

### Continuous Integration

- Report workflow warnings and replace deprecated Codecov actions 🔧
  ([`68e1806`](https://github.com/Mehdi-H/agent-smith/commit/68e18065073bbe8857ff9dbb38f20df6f7c9014f))

### Documentation

- Illustrate the README overview 📝
  ([`49258b7`](https://github.com/Mehdi-H/agent-smith/commit/49258b7df071c6d872a4f677a293baaeff75dcbf))

### Features

- Omit images and badges from generated overviews ✨
  ([`60698be`](https://github.com/Mehdi-H/agent-smith/commit/60698be9e6f47b55857bb753b92114125861b04a))


## v0.4.0 (2026-09-12)

### Continuous Integration

- Upload coverage and test analytics to Codecov with OIDC 🔧
  ([`2fc4167`](https://github.com/Mehdi-H/agent-smith/commit/2fc41672adf46573e44b7b3f88bb883a644be520))

- Use Node 24 artifact actions 🔧
  ([`af5b884`](https://github.com/Mehdi-H/agent-smith/commit/af5b8848e4590ecd90114b88d367e98d30110ece))

### Documentation

- Explain repeated TOML tables for custom sections 📝
  ([`accff0f`](https://github.com/Mehdi-H/agent-smith/commit/accff0f5bfaf15c3d295c4c29095a10fddc8e7ad))

- Highlight our generated agent instructions in the demo 📝
  ([`734bada`](https://github.com/Mehdi-H/agent-smith/commit/734badaa3c32784c741ca971a85dd6e0bc814d36))

- Install the published CLI from PyPI 📝
  ([`a6a8614`](https://github.com/Mehdi-H/agent-smith/commit/a6a8614da5c115d417864caa527dbad7ed5ea593))

- Show Codecov and PyPI badges and refresh demo 📝
  ([`654eb16`](https://github.com/Mehdi-H/agent-smith/commit/654eb16bf623d88e7be6538752b1f02efbceead7))

### Features

- Require Python 3.11 or newer ✨
  ([`6863cc9`](https://github.com/Mehdi-H/agent-smith/commit/6863cc9dea458404a27536c5761aedbaeb9d6689))

### Testing

- Exercise lock refresh after every release ✅
  ([`4b0441a`](https://github.com/Mehdi-H/agent-smith/commit/4b0441abccddeae9e76f54111936f8a3eda5123c))

### Breaking Changes

- Python 3.10 is no longer supported. Upgrade to Python 3.11 or newer to install future releases.


## v0.3.1 (2026-09-12)

### Build System

- Automate zero-major versions and release operations 📦
  ([`e4442ff`](https://github.com/Mehdi-H/agent-smith/commit/e4442ff74292140e03ed0e77884922be874ebc86))

- Name the PyPI distribution agent-smith-cli 📦
  ([`5eae764`](https://github.com/Mehdi-H/agent-smith/commit/5eae7644d2303b157820445ddda2d0b2efbf4469))

### Continuous Integration

- Publish verified releases from main with PyPI OIDC 🔧
  ([`396b4dd`](https://github.com/Mehdi-H/agent-smith/commit/396b4dd4a70670ef5c8941a08273d229955ef3dc))

### Documentation

- Refresh the demo with release operations 📝
  ([`12dd2c8`](https://github.com/Mehdi-H/agent-smith/commit/12dd2c8c30341d5a9c68c268512f4c481f671612))

- Refresh the product introduction 📝
  ([`1ec4e1b`](https://github.com/Mehdi-H/agent-smith/commit/1ec4e1b23f2c4f6c62300e4aa33db46b1a1e6824))


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
