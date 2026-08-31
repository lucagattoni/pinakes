## The hazard was real and the word for it was wrong (20260831 23:26)

- **The queued row called this "a probe silently measuring a question set a rebuild overwrote".
  The probe has never been silent about it.** It already recorded the golden set's *resolved* path,
  its `sha256`, its question count and its multi-hop count, in both the JSON and the human output,
  and had done since before the row was written. Reading the code before building the fix is what
  found that. The defect underneath is real but a size smaller: not a run that misreports what it
  measured, but **no route to re-measure a replaced set** except to put the old file back at the
  path the next `build_rfc_corpus.py` run overwrites again. A three-line flag, not a guard.
- **The overwrite it works around is correct, and the fix had to leave it alone.**
  `write_golden_set` clobbers `<out>/eval/questions.yaml` on every build with no mtime check, no
  hash check and no `--force`; its own docstring says why — the repository copy is the source of
  truth, and a corpus carrying an older one would be scored against questions nobody could find.
  **A hazard whose cause is a deliberate design is fixed at the other end**, by giving the reader
  somewhere else to point.
- **Two siblings already carried the flag, so there was no design decision to take.**
  `src/pinakes/eval.py` and `tools/graph_matrix.py` both take `--questions`, both `type=Path,
  default=None`, both resolving with the same `or` expression. The probe was the odd one out. The
  work that remained was the part precedent could not settle: whether the flag joins the
  `--kb`/`--fake` mutually exclusive group (it must not — a golden set is honoured whichever corpus
  is underneath) and what the help string says (**neither sibling has one**, and `<kb>` names a
  flag a `--fake` run never passes).
- **The battery is the first for this file, and the count in `tests/test_batteries.py` moved with
  it** — ten to eleven, eight `tools-` to nine. That docstring is a coverage claim in prose that
  nothing derives, and it had gone stale twice before; it is only correct here because adding a
  battery is the moment somebody is looking at it.
