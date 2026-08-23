### Fixed

`tools/release_order_gate.py` now checks a **seventh** sequence: the **Published versions** row of
`docs/STATUS.md`'s PyPI table. It had fallen four releases behind — 0.27.0, 0.27.2, 0.28.0 and
0.28.1 — through green runs of every gate in this repo, after being repaired once for exactly this.

The gate could not see it. Its sixth sequence reads the *Published on PyPI* **prose**; the row is a
table cell forty lines below, in the same file under the same heading. So the gate reported those
releases present, and they were — in the sequence next door. That arrangement is the most
misleading one available, because the check and the list it cannot see look like the same check.

Reaching it needed a new mechanism. The row is the one sequence that is not a run of lines: the
whole enumeration is a single table cell, and the rest of that cell carries about twenty more
version numbers in prose. A line-anchored pattern cannot reach inside the line, and an unanchored
one would match the prose too and read a sorted list as unsorted. A `Sequence` may now declare a
`within` anchor — one regex capturing the region the pattern is then run inside. A `within` that
matches nothing yields an empty sequence and trips the floor; one that matches **twice** is refused
outright rather than resolved to the first match, which would splice two lists into a sequence that
is sorted only by accident.

Verified against the defect rather than against a fixture alone: run over the documents as they
stood at `2bff5e4`, the new sequence is the **only** one that fails, reporting 0.27.0 missing from
the middle and three releases past the declared lag.

The row also may not fall behind the *Published on PyPI* prose beside it. Both lists record the
same event — a release verified from the index — so `newest_may_lag` grants latency against the
release documents while a new `not_behind` withdraws it against a list recording that same
verification. This matters because the lag bound alone leaves a two-release window in which the row
is wrong and every gate is green, and **both recorded drifts escalated through that window** rather
than starting past it: measured across every commit on `main` carrying both lists, 29 sit inside it.
The relation has no such window and no false positives — 53 commits with the row at or ahead of the
prose, 14 behind, and all 14 inside the two drifts. It first goes red at `c4b52abd` on 20260812, 11
commits before the lag bound reaches three and fires.
