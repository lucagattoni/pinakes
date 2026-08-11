- **E1's spec now says what it must *not* build.** The deep-release plan gained three constraints
  worked out while starting the increment: **E1 adds no `--deep` flag** — one that parses and then
  refuses is the same defect `0.20.1` fixed, where `vector_tier = "sqlite-vec"` was accepted for a
  tier that was not built — so its escalation block describes how much work answering would take
  and never prints a command to run; **`pnk ask` must state plainly that no answer was
  synthesised**, because passages are not an answer and someone typing `ask` expects one; and the
  `unknown` remedy is **one sentence covering all three branches**, since `confidence_reason`
  already discriminates them and re-checking the conditions in the CLI would be a second copy of
  `_confidence`'s logic that can disagree with it.
