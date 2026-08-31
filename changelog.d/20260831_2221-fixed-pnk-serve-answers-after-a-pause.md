- **`pnk serve` answers concurrent requests, and shuts down cleanly.** The server cached one
  `sqlite3.Connection` per KB and handed it to whichever thread asked next, and `sqlite3` refuses a
  connection used off the thread that opened it. Nothing in `serve.py` starts a thread — the MCP
  transport does: a sync tool runs under `anyio.to_thread.run_sync`, on a pooled worker. Measured
  end to end through the real dispatch, **six concurrent tool calls left two answering and four
  raising `sqlite3.ProgrammingError`**, and **`pnk serve`'s shutdown raised every time**, because
  `cli.py` closes the server from the main thread and the handle belonged to a worker. Each thread
  now opens its own read-only connection.
- **Handles are reaped rather than accumulated.** A worker is retired after ten idle seconds, so one
  connection per thread would otherwise be one file descriptor per thread over a long-lived server.
  Handles whose thread has exited are closed at the next open, and `close()` takes the rest. That is
  what `store.connect_ro`'s new `owning_thread_only=False` buys — shutdown runs on a *different*
  thread from the workers, and with `sqlite3`'s check left on it could not close a single descriptor
  it had opened. It does not make a connection shared: one thread owns each, by construction.
- **A connection is no longer opened and abandoned.** The old code tested and assigned one shared
  slot with no lock, so threads arriving together each opened one and only the last was kept. The
  losers stayed open, unreferenced and unclosable — and a thread that won that race was answering
  from a connection it had opened itself, which is why some concurrent calls succeeded at all.
