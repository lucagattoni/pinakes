- **A test holds `CLAUDE.md` to the 150 lines and 2,700 words it states.** Three slimming passes
  each grew the file back within days, and the regenerated file states a ceiling that nothing
  enforced. `tools/claude_md_size_gate.py` counts the way `wc -l -w` does — the file's own intro
  names that command as the measure, so own-line HTML comments are counted — and
  `tests/test_claude_md_size.py` runs it on the real file, so a push that takes the file past
  either ceiling turns the suite red. The failure says to move a rule to the document that owns it
  and not to delete it; a file that cannot be read fails rather than passes; and a second test
  holds the gate's two numbers to the ones the intro states, so neither can change alone. Run
  against the file as it was before its regeneration it reports 473 lines and 6,033 words, the
  figures `wc` prints. A 23-mutant battery, `tools/batteries/tools-claude_md_size_gate.toml`, kills
  all 23; ten of those came from a fresh reviewer's own mutants, which the first version of the
  tests did not kill. Developer tooling — it ships in no wheel.
