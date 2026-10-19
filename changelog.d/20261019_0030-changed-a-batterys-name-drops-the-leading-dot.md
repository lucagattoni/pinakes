- **A battery's name drops the leading dot of its target's path.** `.claude/workflows/x.js` would
  have flattened to `.claude-workflows-x.toml`, a hidden file that `ls` and the
  `tools/batteries/*.toml` glob in the README's own lookup commands skip — so the next increment
  would have asked which battery claims the file, heard none, and started a second.
  `test_no_battery_is_a_hidden_file` holds it. Developer tooling.
