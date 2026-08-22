- **CI now resolves dependencies the way a user's install does, and exercises what it resolves.**
  The `build` job is the only one that resolves fresh, and it asked `pnk --version`, `pnk init`,
  two `find_spec` calls and two data files — `grep -c 'pinakes.serve' ci.yml` returned **0**. It
  now drives a real MCP handshake against the freshly-resolved wheel (`initialize`, then
  `tools/list`, asserting the server answered *and* registered tools), and runs
  **`tools/wheel_import_gate.py`**, which discovers every module in the *installed* package from
  the filesystem and imports it — on the bare wheel, and again with `[light]`, `[pdf]` and
  `[claude]`, plus the libraries `src/` imports lazily and no walk can reach. A module added later
  is covered without anyone remembering the step exists, which is the thing that did not happen
  for `pinakes.serve`. **`[st]` is the one gap and it is deliberate**: a ~2GB torch download CI
  will not take, so the default backend is still never resolved by anything.
- **The release workflow exercises the wheel it is about to publish.** Its pre-publish smoke test
  was `pnk --version` + `pnk init`, which is how all **38** published releases shipped with
  `pnk serve` dead — `mcp` 2.0.0 reached PyPI 3.5 hours before Pinakes' first published
  version did, so there has never been one that worked on a fresh install. The
  import gate and the handshake now run **in front of** `uv publish`, where a failure costs a
  deleted tag rather than a version number PyPI will never release again. `make smoke` runs the
  same two checks locally.
