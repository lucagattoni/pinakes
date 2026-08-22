- **`pnk serve` no longer dies on a fresh install — it had, on every one since the first PyPI
  release.** `mcp` 2.0.0 removed `mcp.server.fastmcp`, which `serve.py` imports at module scope,
  so a freshly-resolved `pinakes` raised `ModuleNotFoundError` the moment the command started.
  `pyproject.toml` declared `mcp>=1.28` with no upper bound; `uv.lock` pins 1.28.1 and all 37 `uv`
  invocations in `.github/workflows/ci.yml` carried `--frozen`, so **no job in this repository had
  ever resolved that dependency**. `mcp` is now capped below 2.0. The cap is the outage fix, not
  the answer: porting `serve.py` to the 2.x API is its own increment and lifts it.
- **CI now resolves dependencies the way a user's install does, and imports everything.** The
  `build` job is the only one that resolves fresh, and it exercised `pnk --version`, `pnk init`,
  two `find_spec` calls and two data files — `grep -c 'pinakes.serve' ci.yml` returned **0**. It
  now drives a real MCP handshake against the freshly-resolved wheel (`initialize`, then
  `tools/list`, asserting both), and runs `tools/wheel_import_gate.py`, which discovers every
  module in the *installed* package and imports it, on the bare wheel and again with `[pdf]` and
  `[claude]`. A module added later is covered without anyone remembering the step exists, which is
  the thing that did not happen for `pinakes.serve`.
- **The other two lower-bound-only requirements were measured rather than capped by reflex.**
  `anthropic` 1.0.0 and `sentence-transformers` 6.0.0 — what a fresh resolve takes today — both
  keep every symbol and constructor parameter Pinakes calls, so neither is capped: a cap on the
  default embedding backend would change the install contract for every user to prevent a break
  that does not exist.
