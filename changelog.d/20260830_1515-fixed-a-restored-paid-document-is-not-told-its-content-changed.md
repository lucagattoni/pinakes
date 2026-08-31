- **A paid document deleted and restored unchanged is no longer told its content changed.** Deleting
  a document retires its row and drops its chunks with it, so restoring the file genuinely does need
  a paid re-extraction — but `pairing.py` spelled *retired* as *changed hash* so both could share
  one branch, and the refusal a user read said `...was extracted with the paid backend, but its
  content changed.` **The file had not moved a byte**, and the remedy asked them to pay for a change
  that never happened. `docs/DESIGN.md` forbids that conflation by name for the neighbouring case
  ("never conflated with 'content changed'") and `PaidExtractionUnavailableError`'s own docstring
  calls it a false claim. The refusal stays and only its reason changed: `PaidExtractionRequired`
  now carries `CHANGED` or `RETIRED` and `pnk sync` says which, with `CHANGED` winning when both
  hold, since a retired document whose file also came back different really did change. **A warm
  extraction cache still cannot rescue it** — that needs provenance `pair()` cannot see, and routing
  there without it would let a revived document be silently re-extracted by a free backend.
