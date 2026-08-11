---
category: lesson
---

## A Ctrl-C voided a call that may have billed — in both paid clients, for as long as either existed

**Found by working an exit criterion nobody had tested.** E4's plan asks that *"interrupting
mid-loop leaves a reservation `pnk budget` reports as `unknown outcome`, never a lost record"*.
Nothing asserted it, so it was probed with a transport that raises `KeyboardInterrupt`, and the
ledger came back `voided` — EUR 0 recorded for a request that had already been sent.

**Why it was invisible.** Every deliberate branch was right. `billed_call` classifies a timeout as
billable-unknown, voids a 429 that never billed, and — in the deep client — catches `Exception` for
anything unclassified and leaves it unresolved. A `KeyboardInterrupt` is not an `Exception`, so it
fell past all of it into `ledger.paid_call`'s `finally`, whose job is to close an unfinished call
and whose default is to void. **Every layer behaved as written.** The extractor was worse and had
been since I7b: no catch-all at all, so an ordinary defect voided too.

**Three things worth keeping:**

* **The likely interrupt is the one nobody models.** A paid run is slow, visible and cancellable;
  Ctrl-C during one is the *normal* way it ends when a user changes their mind. It was the only
  exit path with no test.
* **A safe default one layer down is not a safe default.** `close_unfinished` voids because most
  unclosed calls never billed. That is correct there and wrong here, and the caller is the only
  place that knows which. `except BaseException` is what says so.
* **The sibling had it too, and fixing one would have been the defect surviving.** One invariant,
  two call sites, two identical clauses — so both moved in the same change, and both tests raise a
  `BaseException` rather than a `RuntimeError`, because a narrower one passes against broken code.
