- **Renaming several documents at once no longer crashes `pnk sync` or leaves the index describing
  the wrong file.** `documents.path` is `UNIQUE`, and the sync plan was built by walking paths in
  sorted order — a fine order for deciding what each file *is*, and an arbitrary one for deciding
  *when* to write it. So an ordinary `git mv` of three notes (`a → b`, `b → c`, `c → d`) produced a
  plan in exactly reverse of the only order the database accepts: `pnk sync` exited 1 with a raw
  traceback carrying no remedy and writing no failure row, `pnk search` then answered from a path
  that no longer existed on disk, and `pnk doctor` exited **0** with every row `OK`, including
  *failures: none recorded*. The plan is now ordered so every move lands on a free path, and every
  document keeps its id — a re-mint would have synced just as cleanly and broken every inbound
  `pnk://` link.
- **Swapping two documents' names is a cycle and is still refused.** No order of a swap can be
  applied — whichever moves first writes onto a path the other still holds — and resolving it needs
  a temporary path the planner cannot create. It fails exactly as before, deliberately and with a
  test pinning it *as* deferred, so that a fixed rename chain cannot be mistaken for fixed renames.
- **A leftover `.pnk.yaml` can no longer cost a live document its id.** A sidecar whose own document
  is gone claims an id for nothing; counted as a claim, it made an untouched document beside it read
  as *an identity that has moved*, so the document was re-minted under a fresh id, the original was
  retired, and every inbound `pnk://` link to it died. Guarded since 0.4.1 and untested until now —
  found by a mutation run rather than by reading.
