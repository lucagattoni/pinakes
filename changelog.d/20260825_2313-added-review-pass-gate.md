- **`tools/review_pass_gate.py` — a review fan-out that lost agents no longer reports success.**
  A `Workflow` adversarial pass returned `{"confirmed":[],"total_raised":0}` with **four of its seven
  agents dead** on the usage limit; another the same day returned an all-empty result after 800k
  tokens with all six dead. Neither was wrong about what it found — both were wrong about having
  looked. It is documented behaviour rather than a bug: a dying agent returns `null`, and the
  recommended idiom for collecting a fan-out is `.filter(Boolean)`, so the standard script turns a
  dead agent into an absent finding. The gate reads `journal.jsonl`, where a `result` carries its
  `started`'s `key`, and refuses any pass whose agents did not all return — the same rule this repo
  already applies to a mutation run with no kills. It also refuses an agent that returned *empty*,
  which resuming cannot fix because the empty result is what replays from cache, and it lists a dead
  agent's files as **evidence, never findings** — split by whether `land.py --cleanup` will destroy
  them. Measured over 533 review-classified subagent runs: only 41% leave any artifact at all, and
  of the targets that are real files, roughly half land where the worktree cleanup destroys them —
  which argues for enforcing a probe convention rather than exploiting one. Exit `0` only when every agent returned content; `2` when the
  run is still being written to, because a gate that calls a live run dead is one people learn to
  ignore.
