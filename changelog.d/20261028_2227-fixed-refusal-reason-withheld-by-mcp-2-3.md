- **An MCP refusal says why again under `mcp` 2.3.0, and still says nothing about the machine.**
  2.3.0 sorts what a tool raises into two kinds: a `ToolError` is a failure the tool meant and its
  text goes to the client; anything else is a crash and its text stays on the server. 2.0.0 sent
  every exception's text. A `ServeError` is the first kind but is not a `ToolError`, so on a fresh
  install (`mcp>=2`, uncapped, resolves 2.3.0) an agent that mistyped `source_type` was told `Error
  executing tool pinakes_search` and nothing else — the empty answer the refusal was added to
  prevent, one layer down, since the agent cannot tell a typo from a crashed server. Measured
  20261028: over a real stdio session the client saw only that line on the published 0.32.7 with a
  fresh resolve, and the full reason on this build, identically under `mcp` 2.0.0 and 2.3.0. The
  four tools are now registered through a wrapper that re-raises a `ServeError` or a
  `TraversalError` — the refusals about what the caller asked, built from its own selector, a KB's
  name or a path inside a KB — as a `ToolError` with the same message, which is the text 2.0.0 sent;
  `remedy` was never part of it and is not added. **Only those two cross.** `StoreError`,
  `IndexSchemaError` and `EmbeddingError` carry the absolute path of the index or the model cache,
  so a wrapper over all of `PinakesError` would have handed an agent a user name and a directory
  layout whenever an index was stale; they stay crashes, and 2.3.0 keeps their text on the server.
  Failures that depend on the KB's state and not on the request — `CoherenceError`,
  `IncompleteIndexError`, `ExtractionCoherenceError`, the backend errors — carry no absolute path
  (checked 20261028) but are not about what the caller asked either, so they stay withheld too:
  an agent on 2.3.0 is told only that the tool failed, as it was on 0.32.7. Whether to tell it that
  the index is stale is a decision about the boundary and is one line in `CALLER_FACING`. On the
  locked 2.0.0 the library still sends every exception's text, as 0.32.7 did, and nothing here
  changes that. The tool schemas are unchanged (the snapshot test still passes). The tests read
  what the tool itself raised, which is why they fail with the wrapper removed on 2.0.0 — the
  version CI runs, where the message alone is sent either way — as well as on 2.3.0, and a test
  pins the allowlist's exact membership. A mutation pass (wrapper off, one tool left out, a blanket
  `PinakesError`, the wrong class, each member dropped, `IndexSchemaError` or `CoherenceError`
  added) was killed on both versions; the one survivor, `pinakes_list_kbs` left unwrapped, is
  equivalent, since it swallows `PinakesError` and has no refusal to carry. Anything else a tool
  raises is still a crash to `mcp`: that is its rule, read from its source, and no test here pins
  it.
