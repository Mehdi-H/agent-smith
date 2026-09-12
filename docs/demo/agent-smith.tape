# Run from the repository root through just demo.
Output docs/demo/agent-smith.gif
Output docs/demo/agent-smith.mp4

Require agent-smith
Require glow
Require less
Require tmux
Require watch

Set Shell bash
Set FontFamily "monospace"
Set FontSize 18
Set Width 1600
Set Height 1000
Set Padding 16
Set Theme "Catppuccin Mocha"
Set TypingSpeed 100ms
Set Framerate 20

Hide
Type "sh scripts/demo-layout.sh"
Enter
Wait+Screen@10s /No file yet\./
Show
Sleep 2s
Type "agent-smith"
Sleep 500ms
Enter
Wait+Screen@45s /Available commands/
Sleep 4s
# Switch the live preview to a pager without changing the left shell's exit status.
Ctrl+B
Type "g"
Sleep 1s
PageDown
Sleep 2s
# Anchor the final view on the ADR heading even when the command list grows.
Type "/Architecture decisions"
Enter
Wait+Screen /Directory:/
Sleep 4s
Type "G"
Sleep 4s
Hide
# Return to the CLI pane to verify the recorded command's exit status.
Ctrl+B
Left
Type 'test "$?" -eq 0 && touch "$AGENT_SMITH_DEMO_SUCCESS"; echo DEMO_FINISHED'
Enter
Wait+Screen /DEMO_FINISHED/
Sleep 500ms
