## A register decays at the speed of its neglect, and the rate is measurable (20260901 11:40)

Two registers live in one file. I measured both against the tree on the same morning, with the same
method — one agent per open row, plus a spot-check of two verdicts by hand.

| Register | Rows checked | Stale | Rate |
|---|---|---|---|
| `## Build order` — the table an implementer opens to pick up work | 7 | 1 | **14%** |
| *Decided work with an owner and no build order* — the parked table | 8 | 4 | **50%** |

**Same file, same author, same discipline, three and a half times the rot.** The variable is not care;
it is readership. A stale row in the build order meets a reader who can falsify it, because that table
is what somebody opens when they want work. The parked table's stated purpose is that nobody has to
read it — and half of it described finished work, two rows of it finished *before the table was
written*.

The one stale build-order row is the more interesting half. Row 3 said the per-thread connection in
`pnk serve` was still to do; `e526e29` had landed it nine days earlier, with five tests, one of them
asserting the row's own symptom. It was found by a peer reading `src/`. **No gate saw it, and no gate
can**: a row is a claim about the tree on the day it was written, and nothing re-reads it.

**So the two fixes are different, deliberately.** The parked table got a liveness *command* per row —
one `grep` that says whether the row is still live, because the cost of the check is a minute and the
cost of skipping it is rebuilding landed work. The build order got a **dated measurement** per row,
with the citation that settles it. That distinction is a peer's and it is worth keeping exactly as
they put it: *a count of what is in the tree today decays silently; a dated measurement of something
that happened once does not, because the tree changing cannot make it false.* A row saying "open"
rots. A row saying "measured still open, 20260901 11:35 UTC, `sync.py:693` catches `PinakesError`
only" cannot — it stays true about that morning, and its staleness becomes visible rather than silent.

The general form: **a register nobody reads is not a register, it is a backlog with better
punctuation.** If a list exists so that work is not forgotten, and the list is never read back, then
the list has become the thing that forgets. Either give it a reader or give each row a check that a
reader would have run.
