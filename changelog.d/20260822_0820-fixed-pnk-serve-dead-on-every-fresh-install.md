- **`pnk serve` no longer dies on a fresh install — it had, on every one since the first PyPI
  release.** `mcp` 2.0.0 removed `mcp.server.fastmcp`, which `serve.py` imports at module scope,
  so a freshly-resolved `pinakes` raised `ModuleNotFoundError` the moment the command started.
  `pyproject.toml` declared `mcp>=1.28` with no upper bound; `uv.lock` pins 1.28.1 and all 37 `uv`
  invocations in `.github/workflows/ci.yml` outside the one job that resolves fresh carried
  `--frozen`, so **no job in this repository had ever resolved that dependency** — and the job
  that could never imported `pinakes.serve`. `mcp` is now capped below 2.0. **The cap is the
  outage fix, not the answer**: porting `serve.py` to the 2.x API is its own increment and lifts
  it. The other two lower-bound-only requirements were measured rather than capped by reflex —
  `anthropic` 1.0.0 and `sentence-transformers` 6.0.0, what a fresh resolve takes today, both keep
  every symbol, constructor parameter and response field Pinakes reads — because a cap on the
  default embedding backend would change the install contract for every user to prevent a break
  that does not exist.
- **`check.sh`'s extras-not-core gate no longer reads the comments around a requirement.** It
  greps a *range of lines*, so a comment inside `[project.dependencies]` that merely mentioned
  `anthropic` reported it as a core dependency. Comments are stripped first, and both directions
  are pinned: a mention must not fire it, a real entry must.
