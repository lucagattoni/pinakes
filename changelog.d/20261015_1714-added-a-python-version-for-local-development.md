- **`.python-version` pins local development to 3.13, the declared floor.** A fresh worktree used
  to take the newest installed interpreter (3.14) while the primary checkout kept the 3.13 its
  `.venv` was created with, so one commit could pass the branch gate and fail the merged one. `uv`
  now resolves 3.13 in every directory of a checkout. `UV_PYTHON` and `--python` outrank the file —
  measured in a scratch project, including under `--isolated --no-project` — so CI's 3.14 legs and
  `minimum-python` are unchanged. The two workflows with no pin of their own, `release.yml` and
  `docs.yml`, follow the file and now run on 3.13: `release.yml`'s wheel-import and MCP-handshake
  gates and the `--strict` docs build were replayed on 3.13 first and pass. Developer tooling — it
  ships in no wheel.
