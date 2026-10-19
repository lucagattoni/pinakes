- **`tools/review_pass_gate.py` no longer reads a finished agent as dead because its result quoted a
  Unicode line separator.** It split journals, and the transcripts it enriches a dead agent from,
  with `str.splitlines()`, which also splits on U+2028, U+2029 and U+0085. JSON allows those raw
  inside a string and Node writes them raw, so a result that quoted one was cut into two malformed
  halves, both skipped, and its agent counted as one that never returned — a finished review
  reported as one that lost an agent. Found by the first live run of the review workflow (the lens
  that surveyed 118 real journals counted four such runs, not re-measured here: they are other
  projects' transcripts); both sites now split on a newline only, and two tests build the shape
  once per separator. Developer tooling — it ships in no wheel.
