- **A test holds `CLAUDE.md` to the 150 lines and 2,700 words it states.** Three slimming passes
  each grew the file back within days, because the ceiling was a sentence in the file and nothing
  read it. `tools/claude_md_size_gate.py` counts the way `wc -l -w` does — own-line HTML comments
  included, because the option A plan's decision D4 names `wc` as the instrument, so a person typing
  the command and the test always get the same number — and `tests/test_claude_md_size.py` runs it
  on the real file, so a push that takes the file past either ceiling turns the suite red. The
  failure says to move a rule to the document that owns it and not to delete it; a missing or
  unreadable file fails rather than passes; and a second test holds the gate's two numbers to the
  ones the file's own intro states, so neither can change alone. Run against the file as it was
  before its regeneration it reports 473 lines and 6,033 words, the figures `wc` prints. A
  13-mutant battery, `tools/batteries/tools-claude_md_size_gate.toml`, kills all 13. Developer
  tooling — it ships in no wheel.
