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
  them. Measured over 613 review agents here: 87% leave some artifact, but 58% of 6,015 redirect
  targets are relative paths inside the worktree the procedure then removes, so losing them is the
  median case rather than bad luck. Exit `0` only when every agent returned content; `2` when the
  run is still being written to, because a gate that calls a live run dead is one people learn to
  ignore.
