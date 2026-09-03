- **A `[sources]` directory Pinakes cannot read no longer deletes the documents under it.** The
  walk enumerated nothing from such a directory, and `pnk sync` reads nothing as *gone*: a root at
  `chmod 000` reported `N removed`, dropped those documents' chunks, took the index to `0 active
  documents`, exited `0`, and left `pnk doctor` reporting OK — `pnk search` then answered nothing
  with no surface saying why. Every document already indexed under an unreadable directory is now
  **held** exactly as it was, the run names the directory and exits non-zero, and the remedy is
  `chmod +rx`. Restoring the permission is the whole repair; nothing is recorded that a later sync
  has to undo. Three shapes reach this and are all covered: a root symlinked into an ancestor this
  process may not traverse, a directory that cannot be listed, and a directory that lists but
  cannot be entered. The last two of the three also ended `pnk sync` — and, for the first, `pnk
  doctor` — in a raw `PermissionError` traceback on Python 3.13, the declared minimum.
