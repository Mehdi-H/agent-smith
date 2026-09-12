# 18. Record terminal demonstrations with VHS through just demo

Date: 2026-09-12

## Status

Accepted

## Context

The project owner wants an automatically recorded terminal demonstration, similar
to the one displayed in Zizmor's README, saved under docs and reproducible through
just. Agent Smith is silent on success, so the recording must show its generated
file as well as the command itself.

## Decision

Use VHS 0.11.0, Glow 3.0.0 and tmux 3.7c, pinned in mise.toml. Keep the scenario in
`docs/demo/agent-smith.tape` and expose `just demo` in the Documentation group.
The recipe uses the installed development CLI from .venv, runs the actual
`agent-smith` command at the repository root and verifies its exit status.
Use two side-by-side tmux panes to connect the command with its result. The left
pane first runs `rm -f AGENTS.md`, then `agent-smith`. The right pane uses `watch`
to refresh Glow every half second: it starts with a missing-file message and
shows the generated Markdown as soon as it exists. The visible viewport shows
the overview and the beginning of the available commands. A local Glow style
keeps link and image labels without displaying long URL destinations.
Preview output drops OSC 8 hyperlink metadata unsupported by watch and forces
ANSI colors for its pipe. Use indexed ANSI colors in the Glow style because
watch does not support its default RGB sequences. The Markdown itself is unchanged. Setup commands are hidden from the recording.

Use a private tmux socket, close that server on exit and restore the previous
AGENTS.md if recording fails. Successful recording retains the generated file.

Save a real terminal recording as `docs/demo/agent-smith.mp4` and an animated
`docs/demo/agent-smith.gif` for embedding in the README. Commit only the GIF,
its source scenario and Glow style. Keep MP4 exports local and ignore them in
Git, as requested by the project owner. Do not publish to an external recording service.
The capture regenerates the repository's AGENTS.md, so review that diff too.

Recording requires system FFmpeg, ttyd and procps `watch`. They are already installed on the current
development machine; document their installation for contributors and fail early
when absent. System media dependencies are not pinned by mise: exact video bytes are not
promised across platform codecs, fonts or timing. VHS may download its browser
on first use. Recording is an explicit documentation operation, outside
`just check`, pre-commit and CI.

VHS 0.12.0 was tried locally but canceled its render context before encoding,
reporting success without output files. Pin 0.11.0 and explicitly verify both
exports exist and are nonempty.

VHS provides a scriptable scenario and both requested export formats. Asciinema
with a separate renderer and manual screen capture were known alternatives;
no comparative benchmark was performed.

## Consequences

The demo can be refreshed when CLI behavior changes without manually opening or
filming a terminal. Real output is recorded; failed generation makes the command
fail rather than claiming a successful demonstration. The render should be
visually reviewed before committing and can take substantially longer than the
fast feedback loop. Generated media increases repository size.

References: [VHS](https://github.com/charmbracelet/vhs) and
[Glow](https://github.com/charmbracelet/glow).
