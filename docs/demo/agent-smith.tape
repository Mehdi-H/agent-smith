# Run from the repository root through just demo.
Output docs/demo/agent-smith.gif
Output docs/demo/agent-smith.mp4

Require agent-smith
Require glow
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
Hide
Type 'test "$?" -eq 0 && touch "$AGENT_SMITH_DEMO_SUCCESS"; echo DEMO_FINISHED'
Enter
Wait+Screen /DEMO_FINISHED/
Sleep 500ms
