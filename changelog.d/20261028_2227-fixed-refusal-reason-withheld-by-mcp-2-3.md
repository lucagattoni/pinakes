- **An MCP refusal says why again under `mcp` 2.3.0.** 2.3.0 sorts what a tool raises into two
  kinds: a `ToolError` is a failure the tool meant and its text goes to the client; anything else is
  a crash and its text stays on the server. 2.0.0 sent every exception's text. A `PinakesError` is
  the first kind but is not a `ToolError`, so on a fresh install (`mcp>=2`, uncapped, resolves 2.3.0)
  an agent that mistyped `source_type` was told `Error executing tool pinakes_search` and nothing
  else — the empty answer the refusal was added to prevent, one layer down, since the agent cannot
  tell a typo from a crashed server. Measured 20261028: `tests/test_serve.py`'s one case on this
  failed against 2.3.0 and passed against the locked 2.0.0. The four tools are now registered
  through a wrapper that re-raises a `PinakesError` as a `ToolError` carrying the same message, which
  is the text 2.0.0 sent; `remedy` was never part of it and is not added. The tool schemas are
  unchanged (the snapshot test still passes). A new test holds the wrapper where it is applied —
  `pinakes_search`, `pinakes_get` and `pinakes_links`, an unknown KB and an unknown document each —
  and fails if any one tool is left out. An exception that is not a `PinakesError` is still a crash
  to `mcp`, and 2.3.0 still keeps its text on the server.
