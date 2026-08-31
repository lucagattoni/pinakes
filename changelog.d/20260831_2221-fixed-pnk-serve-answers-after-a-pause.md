- **`pnk serve` no longer fails on the first request after a pause.** The server cached one
  `sqlite3.Connection` per KB and handed it to whichever thread asked next, and `sqlite3` refuses a
  connection used off the thread that opened it. Nothing in `serve.py` starts a thread — the MCP
  transport does: a sync tool runs under `anyio.to_thread.run_sync`, on a pooled worker retired
  after ten idle seconds. So a burst of calls shared one worker and worked, and the first call after
  a lull got a fresh worker and raised `sqlite3.ProgrammingError: SQLite objects created in a thread
  can only be used in that same thread` — **the shape that made this invisible to every test in the
  suite, all of which call back to back.** Each thread now opens its own read-only connection.
- **Those handles are reaped rather than accumulated.** A worker is retired every ten idle seconds,
  so one connection per thread over a long-lived server is one file descriptor per thread over a
  long-lived server. Handles whose thread has exited are closed at the next open, and `close()`
  takes the rest at shutdown. That is what `store.connect_ro`'s new `owning_thread_only=False`
  buys — shutdown runs on a *different* thread from the workers, and with `sqlite3`'s check left on
  it could not close a single descriptor it had opened. It does not make a connection shared: one
  thread owns each, by construction.
