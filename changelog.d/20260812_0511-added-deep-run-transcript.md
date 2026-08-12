- **Every paid `pnk ask --deep` run now writes a transcript, and says where it went.**
  `.pinakes/deep/<operation_id>.json` holds what the run was asked — the question, the filters as
  you typed them, the confidence reading that chose the branch, the model and prompt version — and
  the answer with its citations. **The ledger deliberately stores no query text**, so without this
  nothing on disk says what a `pnk budget` row was *for*, and a cron run's `--json` is gone the
  moment the pipe closes. The filename is the `operation_id` the ledger groups its calls by, so a
  row and its transcript meet without searching. It is written for a run that *returned*: a budget
  refusal, a declined confirmation and an `on_exceed = "abort"` halt write none — `abort` discards
  the rounds already paid for, and a file holding what it discarded would hand back exactly what
  the setting withholds.
- **`pnk sync --clear-cache=transcripts` is what removes them, and the only thing that does.** A
  transcript is protected exactly as a paid cache entry is (INVARIANTS): nothing sweeps it,
  `--rebuild` leaves it, and `--clear-cache` — bare or `=paid` — clears the extraction cache whole
  and does not touch it. The new value names a **store** rather than an authorisation, because a
  spelling that also emptied the cache would destroy more than it names. It asks before it removes,
  with a different sentence from the cache's: an extraction can be bought again, and the record of
  what a particular run was asked cannot.
- **`pnk ask --json` gains two keys**: `answer.call_ids`, the ledger's join key, so a script can
  price a run against `pnk budget` without re-deriving anything; and a top-level `transcript` naming
  the file relative to the KB root — `null` when nothing was paid for, like `answer`. The stored
  `answer` object and the printed one are now produced by one renderer, so what a script reads off
  stdout and what it reads back off disk cannot drift.
