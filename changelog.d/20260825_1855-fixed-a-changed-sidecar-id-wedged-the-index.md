- **A sidecar whose id no longer matches the row at its path stops wedging the index.** The stale
  row is retired and keeps its `path`, `documents.path` is UNIQUE, and the `ON CONFLICT (id)` clause
  cannot see a conflict on the path — so the adoption collided with the row it was replacing and
  `sqlite3.IntegrityError` escaped as a raw traceback. The retired row survived the failure, so
  every later `pnk sync` hit the same wall (measured: three consecutive runs, same error, row still
  retired), `pnk search` could not see the document, and `pnk doctor` reported the KB healthy at
  exit 0. Reached with no hand edit at all by a merge conflict, a `git checkout <sha> -- <file>.pnk.yaml`,
  or a sidecar copied between KBs.
