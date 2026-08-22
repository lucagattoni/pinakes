- **A shipped release filed under *What is not built* is now a gate failure.** `0.27.1`'s
  per-release section landed inside `# Part 5` of `docs/ROADMAP.md` because the script inserting it
  looked for the next `## ` heading and stepped over the `# ` that bounds the Part — and **all six
  release sequences stayed green**, because a sorted sequence says nothing about *location*.
  `0.25.3` did the same and `0.25.4` fixed it once already. `tools/release_order_gate.py` now
  requires every per-release section to sit under the Part whose declared range holds its version,
  reading those ranges (`` `0.1.x` ``, `` `0.2.0` → `0.4.1` ``, `` `0.8.0` onward ``) **out of the
  `# Part N` headings themselves** rather than from a mapping kept beside them. A Part that declares
  no range may hold no release section, which is the case that fires on the defect above.
