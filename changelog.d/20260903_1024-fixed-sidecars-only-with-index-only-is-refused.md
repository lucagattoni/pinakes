- **`pnk sync --sidecars-only --index-only` is refused instead of silently writing into `docs/`.**
  The two flags are the halves of one sync and each names what the other does — *"write into
  `docs/`, never touch the index"* against *"update the index, never write into `docs/`"*. Passed
  together, `--sidecars-only` simply won: it returns before the index is opened, and the sidecar
  writer never read `index_only` at all. So the run created sidecars in `docs/` — the one thing
  `--index-only` exists to promise it will not do — and reported `0 indexed, 0 renamed, 0
  metadata-only, 0 unchanged, 0 removed` at exit 0. Every number in that line was truthful; the
  line was still a lie, because the count of files written into `docs/` was not among them.
