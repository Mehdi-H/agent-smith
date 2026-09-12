#!/bin/sh
# Open an isolated two-pane terminal for the recorded scenario.
set -eu
tmux -S "$AGENT_SMITH_DEMO_SOCKET" -f /dev/null new-session -d -s demo -x 160 -y 45 "env PS1='$ ' bash --noprofile --norc"
tmux -S "$AGENT_SMITH_DEMO_SOCKET" set-option -g status off
tmux -S "$AGENT_SMITH_DEMO_SOCKET" set-option -g pane-border-status top
tmux -S "$AGENT_SMITH_DEMO_SOCKET" set-option -g pane-border-format ' #{pane_title} '
tmux -S "$AGENT_SMITH_DEMO_SOCKET" select-pane -t demo:0.0 -T 'Run agent-smith'
tmux -S "$AGENT_SMITH_DEMO_SOCKET" send-keys -t demo:0.0 'rm -f AGENTS.md' Enter
tmux -S "$AGENT_SMITH_DEMO_SOCKET" split-window -h -l '68%' -t demo:0.0 'TERM=xterm-256color watch --color --no-title --interval 0.5 sh scripts/demo-preview.sh'
tmux -S "$AGENT_SMITH_DEMO_SOCKET" select-pane -t demo:0.1 -T 'AGENTS.md | watch glow (0.5s)'
tmux -S "$AGENT_SMITH_DEMO_SOCKET" select-pane -t demo:0.0
tmux -S "$AGENT_SMITH_DEMO_SOCKET" attach-session -t demo
