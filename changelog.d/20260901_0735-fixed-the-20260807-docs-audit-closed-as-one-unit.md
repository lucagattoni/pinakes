- **Every remaining finding of the 20260807 documentation audit is fixed** — 34 findings across ten
  files, landed as one unit rather than 34 rows. Two were already cured by other work
  (`c770c0f`, `ec73b1f`) and are closed unworked; the rest were re-measured against `f3303fc`
  before a single character was changed.
- **Three published output fences now match what the commands print.** `docs/GUIDE.md` showed
  `pnk sync` output with the structural-graph `0 edge(s) derived …` line missing, in three places
  on a site published on every push to `main`. Each was re-run as a control first — and the
  unmatched-`.pdf` case and the `--scan-links` case put that line in **different** positions
  (second and third respectively), which reading could not have told apart.
- **`docs/CLI.md`'s `--offline` row no longer states a guarantee the code does not make.** It
  claimed `--offline` never reaches for model weights. True on `sentence-transformers`, which
  passes `local_files_only`; on `fastembed` the refusal fires only when no cache directory exists
  at all, so an existing cache missing *this* model downloads 1.1 GB under `--offline` and the
  search succeeds. The row now says both halves, and lists `links` among the commands that take
  the flag.
- **The root `README.md` no longer tells readers to hand-edit `pinakes.toml` for a `[light]`
  install.** `pnk init --backend light` has done it since 0.22.0. The commit that shipped the flag
  is titled *"three copies of a false sentence"* and fixed `docs/CLI.md`, `docs/GUIDE.md`,
  `docs/ROADMAP.md` and `docs/STATUS.md` — the fourth copy was in `README.md`, out of that sweep's
  `docs/` scope, and survived 21 days in the most-read file of a public repository.
- **`docs/DESIGN.md` §6.1 no longer shows a runnable command for a template that does not ship.**
  `pnk init research --template research-papers` exits 1 — `notes` is the only template. The tree
  stays as the contract a template satisfies, now named as the shape the template release fills in.
- **Nine rotted code citations were re-derived by reading the lines**, not by pasting the values a
  register recorded in 20260826 — which had themselves drifted again in the interim.
- **Two stale row counts came out of `docs/VERIFICATION.md` rather than being corrected.** They had
  been restated once and had drifted a second time by 20260901, two paragraphs below the file's own
  standing instruction that a counted claim goes stale in silence.
