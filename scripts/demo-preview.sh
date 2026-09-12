#!/bin/sh
# Refresh the generated Markdown inside the demo's watch pane.
set -eu
if [ -f AGENTS.md ]; then
    rendered="$AGENT_SMITH_DEMO_SOCKET.rendered"
    CLICOLOR_FORCE=1 glow -s docs/demo/glow.json -w "${COLUMNS:-90}" AGENTS.md > "$rendered"
    # watch supports SGR colors, but not OSC 8 clickable-link metadata.
    awk '{ gsub(/\033]8;[^\033\007]*(\007|\033\\)/, ""); print }' "$rendered"
else
    printf '\n  AGENTS.md\n\n  No file yet.\n\n  Waiting for agent-smith...\n'
fi
