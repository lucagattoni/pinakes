- **The README and the Guide pin `--python 3.13` on their `[light]` lines where `uv` might choose
  CPython 3.15, and the Guide's `.mcp.json` snippet names the absolute path of `pnk`.** Both were
  found by the dogfooding on-ramp's first measurement (findings F5 and F4, 20261019 12:13 UTC,
  against 0.32.7, on a machine whose newest Python was 3.15). `uvx --from "pinakes[light]" pnk
  --version` exited 1 with *`onnxruntime>=1.24.2` has no wheels with a matching Python ABI tag
  (e.g., `cp315`)*, and `uv init --bare` wrote `requires-python = ">=3.15"`, so the `uv add
  --no-sync` after it did not resolve; with `--python 3.13`, the declared minimum, both worked. The
  newest `onnxruntime` on PyPI, 1.31.1, still had no `cp315` wheel when it was read (20261030 19:49
  UTC), and `pinakes[st]` resolved on a 3.15 project (20261030 20:01 UTC), so the `[st]` examples
  stay unpinned. It is not universal: the unpinned `uvx` resolved on one machine measured after
  20261029 18:53 UTC, so it depends on which interpreter `uv` picks. The post-publish check in
  `docs/RELEASING.md` carries the pin too, as the 0.32.7 and 0.32.8 sweeps ran it. For F4, a bare
  `"command": "pnk"` was found on no `PATH` tried (a project install keeps `pnk` in `.venv/bin`, and
  `uv tool install`'s directory may not be on the `PATH`), so the first snippet shows
  `/absolute/path/to/pnk` and says how to find it; whether a live agent launches the entry with your
  `PATH` was not tested. `README.md` is also the package's description on PyPI, so that page changes
  only with a release. **Not done:** capping `requires-python` below 3.15, and the unpinned `uvx`
  line in the workflow `pnk init --ci` writes (`src/pinakes/ci.py`) — a packaging decision and a
  code change, both left open.
