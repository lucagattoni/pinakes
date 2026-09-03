- **`pnk doctor` no longer offers to prune the sidecar of a document that is still on disk.** The
  orphan check asked whether the document was a *readable* file, so a document the process could
  not reach — a symlink under a directory without `+x` — was reported as an orphaned sidecar, with
  `Remove with pnk doctor --prune` printed beneath it. Taking that advice deletes the document's
  stored ULID, which is permanent and cannot be minted again: the identifier survives a move, a
  rename and a re-index precisely so that links to it keep resolving. The check now asks whether
  the path exists at all, without following the link, so *absent* and *unreachable* stop being the
  same answer. This one did not depend on the interpreter — it was wrong on both.
- **One unreadable directory inside a partner KB no longer discards the whole partner's links.** On
  Python 3.13 the cross-KB sidecar walk raised, and both of its callers caught the error coarsely:
  `pnk links --check` reported the entire partner as unreachable, and `pnk doctor`'s cross-KB check
  skipped it in silence. Only the one candidate it cannot read is skipped now, which is what 3.14
  already did.
