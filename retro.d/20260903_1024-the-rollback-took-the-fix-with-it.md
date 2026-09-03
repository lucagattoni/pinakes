## The rollback took the fix with it (20260903 10:24)

**HIGH — a fix that unit-tests green and does nothing, because a transaction boundary ate it.**
S7's clearing was written where it reads best: at the top of `_apply`, once, before a path is
re-attempted. Repair a document and the row goes. That much was true and the test proved it.

Then running the real thing three times against one broken document produced **three rows**. The
failure paths in `sync` call `connection.rollback()` before recording, and the rollback discards
the `DELETE` sitting uncommitted in the same transaction. The clear was written, then silently
undone, then a fresh row appended — for every sync, forever. **The half of the defect the fix was
also supposed to cure survived it completely**, and no unit test I had written could have shown
that, because each one exercised a single sync.

**What found it was running the command three times and counting rows** — not reasoning about the
code, which had already concluded the fix was complete. The repo's own rule says a seam removes an
inch of the real path from coverage and that defects concentrate there; a transaction boundary is
exactly such a seam, and it is invisible in the source line where the bug appears to live.

**Two lessons, and the second is the sharper one.** A write inside a block that may roll back is
not a write. And **"the test is green" answers a narrower question than "the defect is gone"** —
here they differed by an entire half of the finding.

**A third came free, from the same habit.** The first version cleared on every action *except*
`Skip`, on the reasoning that a skip means nothing was attempted. Running it showed `Skip` carries
two unrelated meanings: an unreadable document being **held**, and an ordinary **unchanged** one.
They want opposite answers — and repairing a hand-edited sidecar back to its original bytes changes
neither content nor sidecar hash, so **the repair a user is most likely to perform arrives as
"unchanged"**, and the fix missed precisely the case it was written for. `Skip` now says which it
is. **One name quietly serving two states costs nothing until something has to tell them apart.**
