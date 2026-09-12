#!/bin/sh
# Record the real installed CLI in this checkout and verify generation succeeded.
set -eu
for program in vhs ffmpeg less ttyd watch; do
    if ! command -v "$program" >/dev/null 2>&1; then
        printf 'Missing %s; see the terminal demo setup in CONTRIBUTING.md.\n' "$program" >&2
        exit 1
    fi
done
if [ ! -x .venv/bin/agent-smith ]; then
    printf '%s\n' 'Run just setup before recording the demo.' >&2
    exit 1
fi
scratch=$(mktemp -d)
completed=false
if [ -e AGENTS.md ]; then
    cp -p AGENTS.md "$scratch/AGENTS.md"
fi
cleanup() {
    if [ -S "$scratch/tmux.sock" ]; then
        tmux -S "$scratch/tmux.sock" kill-server || :
    fi
    if [ "$completed" = false ]; then
        if [ -f "$scratch/AGENTS.md" ]; then
            cp -p "$scratch/AGENTS.md" AGENTS.md
        else
            rm -f AGENTS.md
        fi
    fi
    rm -rf "$scratch"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
export AGENT_SMITH_DEMO_SOCKET="$scratch/tmux.sock"
export AGENT_SMITH_DEMO_SUCCESS="$scratch/success"
glow_binary=$(mise which glow)
tmux_binary=$(mise which tmux)
PATH="$PWD/.venv/bin:$(dirname "$glow_binary"):$(dirname "$tmux_binary"):$PATH"
export PATH
mise exec -- vhs --output "$scratch/agent-smith.gif" --output "$scratch/agent-smith.mp4" docs/demo/agent-smith.tape
if [ ! -f "$AGENT_SMITH_DEMO_SUCCESS" ]; then
    printf '%s\n' 'The recorded agent-smith command failed; inspect the recording and fix generation.' >&2
    exit 1
fi
for artifact in "$scratch/agent-smith.mp4" "$scratch/agent-smith.gif"; do
    if [ ! -s "$artifact" ]; then
        printf 'Recording export is missing or empty: %s\n' "$artifact" >&2
        exit 1
    fi
done
mv "$scratch/agent-smith.mp4" "$scratch/agent-smith.gif" docs/demo/
completed=true
printf '%s\n' 'Recorded docs/demo/agent-smith.mp4 and docs/demo/agent-smith.gif.'
