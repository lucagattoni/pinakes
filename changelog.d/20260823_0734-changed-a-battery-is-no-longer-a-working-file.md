- **`tools/mutate.py`'s docstring no longer says a battery is a per-increment working file, not a
  portable artifact.** That sentence shipped in 0.27.0 as a design statement and had never been
  measured. Measured now, against 81 mutants left in session scratchpads: **78 anchors still
  resolved exactly once** a day to a week later, and the three that did not **refused** — naming the
  anchor and its count, with the target untouched. A stale anchor cannot produce a false `KILLED` or
  a false `SURVIVED`, so the cost of keeping a battery is a maintenance prompt, never a false
  certificate. What keeping one preserves is not the proof, which is re-derivable in an afternoon,
  but the reasoning about **which mutants were worth writing**.
