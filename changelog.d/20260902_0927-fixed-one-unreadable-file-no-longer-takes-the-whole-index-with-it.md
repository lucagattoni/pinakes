- **One unreadable document no longer aborts the entire index.** `hash_file` let `PermissionError`
  escape `walk_sources`, so a single file the process could not open ended `pnk sync` with a raw
  Python traceback and **no index database at all** — every other document in the KB unreachable
  because of one. The path is now carried out of the walk, and the run reports it as a per-document
  failure with a `chmod +r` remedy. `report.ok` is `not failures`, so the sync still exits non-zero:
  the file is not quietly dropped.
- **An indexed document that becomes unreadable is held, never retired.** This is the half that
  makes the first one safe. `pair()` reasons from absence — a path the walk stops reporting is a
  path that is gone — so a walk that merely *skipped* the file would have emitted a `SoftDelete`,
  dropped its chunks and printed `1 removed`. A permission change would have deleted a document
  from search. The walk therefore carries the unreadable paths to `pair()`, which holds each row as
  a `Skip` before any loop that reasons from absence runs.
- **An unreadable document's sidecar is never listed as orphaned.** That list is printed with
  `pnk doctor --prune` beside it, so counting a document that is sitting on disk hands the user a
  command that destroys a permanent ULID.
- **`--sidecars-only` reports it too** — the half that runs in a pre-commit hook, and the last place
  an unreadable document should pass in silence.
- **`pnk doctor` no longer dies on the same condition.** `_extraction_backend_drift` hashed the
  source of every paid-recorded row through the same unguarded read, so the command `pnk sync`'s own
  remedy sends you to ended in a traceback on exactly the state it exists to diagnose. A fourth
  drift check, `paid extraction unreadable`, now names the document whose staleness could not be
  decided — recorded rather than swallowed, because `paid extraction stale: none` would otherwise be
  a claim about a file nothing could read.
