- **A release missing from one of the six sequences is now a gate failure.** Order is a property of
  the pairs and membership a property of the set: delete a row and every surviving pair is still
  sorted, so no ordering check can see it. `tools/release_order_gate.py` now requires every release
  at or after a sequence's **declared** start to appear in it. The start is a constant, never the
  sequence's own oldest entry — deriving it would let a deleted *first* row move the start and hide
  itself, which is the gate electing its own answer in the one place it matters. The reference set
  is the union of the six sequences rather than `git tag -l`, because reading tags needs an unshallow
  clone and every CI checkout here is shallow but one; the limit — a release absent from all six is
  invisible — is stated in the tool. A sequence permitted to lag must be complete up to **its own**
  newest entry, so the hold-back window cannot excuse a hole underneath it.
