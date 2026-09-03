## The tag points at a commit CI never finished (20260903 13:18)

**MEDIUM — a release tag can name a commit whose CI legs were cancelled, and nothing in the release
procedure looks.** `v0.32.2` points at `f23b602`. That commit's `CI` run was cancelled 88 seconds
later, when the next landing superseded it, and **three of its jobs never completed**: `check
(light)`, `check (light pdf)` and `check (light pdf claude)` — the three that actually run the test
suite. The run's other eleven jobs succeeded, so `gh run list` shows it as `cancelled` rather than
as anything alarming, and `docs` at the same sha is a clean green.

**The release was already published by then.** Nothing in `docs/RELEASING.md` reads CI at the
release commit: the gate before the push is `make release-check`, which asks about the tag, and the
verification after it asks about the artifact. Both are right and neither covers this.

**What made it safe was measured, not assumed.** The successor commit `058df49` merges that tree and
its own `CI` run is green on **all three** `check` legs — checked per job, because a run's top-line
conclusion says nothing about which legs ran. And the specific risk was nameable: this release moved
`src/pinakes/budget/prices.toml`, and the last release that moved that file took **both** `[pdf]`
legs red for 44 minutes. Locally those legs skip — `pinakes[pdf]` is not installed in the primary
checkout — so a green `./check.sh` on the release branch could not have seen it. `058df49` carries
the re-stamped `as_of` and ran both legs green, which is what closes it.

**Two things generalise.**

**A cancelled run is not evidence, and neither is a successor's green *run*.** The successor tests a
*different tree* — yours plus whatever superseded you. It is good evidence only when you have said
what the difference is and why it cannot mask your defect. Here the difference is another session's
row-8 work in `cli`, `search`, `serve`, `sync`, `chunk` and `eval`, and the leg at risk was a money
trace in `tests/test_pdf_trace.py` that none of them touches.

**The window that produces this is the same window the procedure deliberately uses.** Landing and
publishing are separate steps here, and `docs/RELEASING.md` § *A fragment that arrives after the
release commit but before the tag* treats the gap as a feature. A peer landing inside that gap is
therefore normal, and cancelling the release commit's CI is what a peer landing inside it does.

*Lesson: after pushing a release tag, read the CI run at the tagged commit per job, not per run. If
its `check` legs were cancelled, name the commit whose green run covers the same tree and say what
differs between them — and say which leg the release's own diff put at risk, because a local
`./check.sh` skips whatever extras the machine lacks.*
