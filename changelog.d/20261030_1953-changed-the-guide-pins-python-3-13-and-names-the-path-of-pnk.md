- **The README and the Guide pin `--python 3.13` where `uv` might choose CPython 3.15, and the Guide's
  `.mcp.json` snippet names the absolute path of `pnk`.** Both were found by the dogfooding on-ramp's
  first measurement (findings F5 and F4, 20261019 12:13 UTC, against 0.32.7, on a machine whose newest
  Python was 3.15). `uvx --from "pinakes[light]" pnk --version` exited 1 with *`onnxruntime>=1.24.2` has
  no wheels with a matching Python ABI tag (e.g., `cp315`)*, and a plain `uv init` wrote
  `requires-python = ">=3.15"`, so the `uv add` after it did not resolve; with `--python 3.13`, the
  declared minimum, both worked. The newest `onnxruntime` on PyPI, 1.31.1, still had no `cp315` wheel
  when it was read (20261030 19:49 UTC). It is not universal: the unpinned `uvx` resolved on one machine
  measured after 20261029 18:53 UTC, so it depends on which interpreter `uv` picks. The `uv init`,
  `uvx` and `uvx … pnk serve` lines in the README, the Guide's install section and its second `.mcp.json`
  snippet, and the zero-install line in the design document now carry the pin. For F4, a bare
  `"command": "pnk"` was found on no `PATH` tried (a project install leaves `pnk` in `.venv/bin`, and
  `uv tool install`'s directory is on the `PATH` only after `uv tool update-shell`), so the first snippet
  shows `/absolute/path/to/pnk` and says why; whether a live agent launches the entry with your `PATH`
  was not tested. `README.md` is also the package's description on PyPI, so that page changes only with
  a release. **Not done:** capping `requires-python` below 3.15, which is a packaging decision and
  stays open.
