- **`tools/mcp_handshake_gate.py` — a real MCP session, and the four tool schemas committed.** The
  handshake in `ci.yml` and `release.yml` was three JSON-RPC lines piped into `pnk serve` with stdin
  closed immediately. `mcp` 1.28.1 drained that queue before shutting down; 2.0.0 does not. Measured
  on the same three lines, ten runs each: **`tools/list` answered 10/10 under 1.28.1 and 2/10 under
  2.0.0.** It was never a gate — it was a coin flip that landed the same way for a year, and it
  would have gone red four runs in five on a server that works. The gate drives `mcp`'s own client,
  which holds the session open until it has its answers (8/8) and negotiates the protocol version
  itself, so the leg tracks the dependency instead of rotting against it.

  It also checks two things the piped version could not: that `serverInfo.version` is the version
  the built **wheel's filename** says — never `pnk --version`, which asks the install under test and
  would agree with itself — and that the tools listed match `tools/mcp_tool_schemas.json` exactly.
  Against a fresh resolve, that snapshot is what turns a future `mcp` quietly reshaping the
  published tool contract into a red run instead of a silent change to every client's view.
