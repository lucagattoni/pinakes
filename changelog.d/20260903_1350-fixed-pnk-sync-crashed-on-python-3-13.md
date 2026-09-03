- **`pnk sync` no longer crashes on Python 3.13, the oldest version `pinakes` says it supports.**
  A symlink whose target sits under a directory the process cannot traverse made the source walk
  raise `PermissionError` instead of reporting the link — a raw traceback, and no index written.
  `Path.is_file()` and `Path.exists()` swallow that error on 3.14 and propagate it on 3.13, so the
  crash depended entirely on which interpreter you installed with; `requires-python` is `>=3.13`,
  and every published release from at least 0.25.0 to 0.32.2 crashes there. The six affected call
  sites — the document walk, its unresolvable-symlink guard, the sidecar walk, the unindexed
  neighbour probe, and two in pairing — now use spellings whose answer does not depend on the
  interpreter, and CI runs one leg on 3.13 so it cannot come back unnoticed.
- **The reason a sidecar could not be read is now the same sentence on both interpreters.** A
  sidecar behind an unreadable directory reported `SidecarError` with a remedy on 3.14 and a bare
  `PermissionError: [Errno 13]` on 3.13, because the guard inside the function that names the
  reason raised before it could name it. Both now print the remedy. The document is still refused
  rather than indexed, which is deliberate: its stored id is unreadable, and minting a second one
  is the failure that refusal exists to prevent.
