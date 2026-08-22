- **`pnk serve` runs on `mcp` 2.x, and tells a client which Pinakes it is.** `serve.py` moves from
  `mcp.server.fastmcp.FastMCP` — removed outright in `mcp` 2.0.0 — to its successor
  `mcp.server.mcpserver.MCPServer`, and the requirement moves from `mcp>=1.28,<2` to `mcp>=2`. The
  cap was 0.27.2's outage fix and was always going to be lifted by the increment that ported the
  code; nothing takes its place, because what catches a dependency's next major is resolving fresh
  and running the thing, not a guess about a release nobody has seen.

  **The four `pinakes_*` tool schemas are byte-identical across the move** — captured from a live
  session on each library and diffed before anything landed — so no client sees a different tool.
  The one wire difference is `serverInfo.version`: `FastMCP` took no `version=` and filled the
  field with the *`mcp` library's* own version, so every release up to 0.27.2 told a client asking
  which Pinakes it was talking to that it was `1.28.1`. It now carries Pinakes' version.
