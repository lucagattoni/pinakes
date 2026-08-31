- **A rename Pinakes cannot apply is now a recorded failure with a remedy, not a raw traceback.**
  `documents.path` is `UNIQUE`, so a move onto a path another row still holds is refused by the
  database. Ordering a rename chain fixed the common case, but two cases still collided: **a cycle**
  — two documents exchanging names, which no order can apply — and **a chain whose earlier member
  failed to index**, because a caught failure rolls back and that document keeps its old path for
  the next action to land on. Both surfaced as `sqlite3.IntegrityError: UNIQUE constraint failed:
  documents.path`, which escaped `_apply`, `sync()` and the CLI's own handler alike: no remedy, no
  ledger row, and `pnk doctor` still answering `failures: none recorded` over it. `pnk sync` now
  records a `PathStillHeldError` naming the temporary-name remedy, and `pnk doctor` reports it. The
  exit status is unchanged — still non-zero — and **the cycle is contained, not resolved**: rows are
  left at paths no longer on disk and the user has to act. What changed is that they are told.
- **Only that one collision is caught.** `sqlite3.IntegrityError` also covers the
  `chunks(doc_id, ordinal)` and `nodes(kind, key)` UNIQUEs, the `links` and `edges` primary keys and
  the CHECKs on `documents.state`, `links.origin` and `nodes.kind` — every one of which fires when
  Pinakes is wrong, not when a user's tree is. Those still escape loudly rather than being filed as
  one document's failure.
