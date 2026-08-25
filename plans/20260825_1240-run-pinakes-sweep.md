# Running Pinakes found fifteen defects that reading it did not

**Written 20260825 12:40 UTC against `main` at `c2c69cb`.** Produced by a coder session sweeping seven
command surfaces with fourteen agents, each finding re-run from a clean directory by a verifier
prompted to **refute** it. **Five findings were refuted and dropped. One came back with no verdict at
all and was recovered.** What follows is what survived.

**This file proposes work. Its two decisions are NOT taken.**

## Why it exists, and the sentence that produced it

`CLAUDE.md` says to read an empty `plans/` list as *"nobody has run Pinakes lately"*, never as
*finished*. That was acted on. **Every finding below came from running the tool; none came from reading
it**, and the same day's earlier work — seven findings from gates, indexes and probes — likewise came
from asking rather than reading. **Reading found none of these.**

## Provenance, per finding, because it is not uniform

| Marker | Means |
|---|---|
| **†** | Reproduced independently by the planner, by execution, on `c2c69cb` |
| **‡** | Found and confirmed by the coder's adversarial verifier, re-run from a clean directory |
| **✱** | Verifier returned **no verdict**; the coder verified it by hand afterwards |

**A verifier returning nothing is not a refutation.** One finding was classified into the refuted
bucket by a default branch and would have been buried. It is real. **Whatever consumes a verifier's
output must distinguish *refuted* from *unverified*** — that is a defect in the harness, not in the
finding, and it is written down here so the next sweep does not repeat it.

## High — three

### S1 ‡† `pnk sync` aborts the entire index on one unreadable file

`sync.py:519 hash_file` lets `PermissionError` escape. A raw Python traceback reaches the user and the
walk stops.

**Verified by the planner, and it is worse than "the walk aborts":** with three documents and one
`chmod 000`, `pnk sync` exits 1 with an unhandled traceback and **no index database is created at all**
— the walk dies before anything is indexed, so *no other document in the KB is reachable*. The control
matters: the same KB with permissions restored fails on a *different* cause (a missing embedding
backend) with a clean, remedied error message. **This repository handles that case gracefully and this
one with a stack trace.**

### S2 ‡ `pnk doctor` reports a KB fully healthy after a sync silently dropped a document

A `sqlite3.IntegrityError: UNIQUE constraint failed: documents.path` during sync leaves the row at
`state='deleted'` while the sidecar and the source file sit intact on disk. The document is
unfindable. **`doctor` exits 0.**

**Rank this first.** Silent index loss behind a green diagnostic is this repository's worst recorded
shape, and it is *the same shape as X1* — a check that answers a question adjacent to the one that
matters.

### S3 ‡ `pnk serve` reuses one `sqlite3.Connection` across OS threads

MCP tool calls fail with a SQLite cross-thread error.

**The verifier corrected the reproduction, and the correction is the finding.** Back-to-back calls do
**not** trigger it — 0 failures in 10. The deterministic trigger is **any pause longer than ~10 s
between calls**, which is the normal shape of an agent session. A repro that fires only under the
access pattern nobody tests under is why this survived.

## Medium — six

| # | Surface | Finding |
|---|---|---|
| **S4** ‡† | `init` | **A KB name that is not valid TOML bricks the KB at creation, silently.** `init` exits 0 and prints *created*; every later command exits 1; `pnk init` refuses to repair it (*"already a KB"*), so **the remedy surface is empty** and recovery is hand-editing TOML. Three classes: `"`, `\`, and control characters **other than tab** (tab is legal in a TOML basic string — an earlier four-class claim was wrong). **No flag is needed** — the directory name reaches the same path via `root.name` (`init.py:355`). **The verifier widened it usefully: `--name 'C:\notes\kb'`** — a Windows-style path as a KB name — **is far more plausible than a quoted name.** The hole is in the mechanism: `template.py:_render` has no notion of TOML escaping, so any future variable carrying user text inherits it |
| **S5** ‡ | `sync` | `--sidecars-only` together with `--index-only` **writes a sidecar** while reporting `0 indexed, 0 renamed, 0 metadata-only, 0 unchanged, 0 removed` |
| **S6** ‡ | `sync` | *"moved without its sidecar, so a new id was minted"* fires on **ordinary deletion**, naming a file that no longer exists. The verifier corrected the finder: it **does** also fire on a genuine move, so the original title's second half was wrong and was dropped |
| **S7** ‡ | `doctor` | The failure ledger **never clears**, and its own remediation text is wrong. **The verifier strengthened this**: it does not clear when the document is *repaired* either, which is the normal user path |
| **S8** ‡ | `search` | Negative `-k` is passed through as a **raw Python negative-slice bound**: `-k -1` returns 19 passages, `-k -100` prints `no passages matched.` at **exit 0** |
| **S9** ‡ | `ask` | `pnk ask -k -1` raises an **unhandled traceback** from `deep/estimate.py:456`. Held at medium because it is loud and immediate rather than silent |

## Low — five

Symlink loop invisible to both `sync` and `doctor` (**verifier downgraded high → low**: a loop resolves
to no content, which is ordinary Unix semantics); `-k 0` silently ignored on both `search` and `ask`;
`--source-type` accepts any string unvalidated, so a typo reads as an empty KB; `confidence_reason`
reports *"nothing matched the filters"* **when no filters were given**.

## Two genuine decisions — NOT taken

### D-36 — `pnk link` detaches a trailing comment from an alias-reference line ✱

`sameTags: *commontags      # alias reusing the anchor above` becomes two lines, the comment orphaned
onto its own line with 27 spaces of padding. Reproduced byte-for-byte.

**It is not on the bounds table.** `docs/MANIFEST.md:307-319` lists ten exclusions and none covers it:
the anchor carries a real value, nothing is deleted, the name is not reused, it is not self-referential.
`MANIFEST.md:303` says plainly *"Comments … all survive a rewrite"*, and `docs/VERIFICATION.md:282`
pins that promise. All six anchor/alias tests in `tests/test_sidecar.py` were checked — **none covers a
comment on an alias reference.**

**So it is either a defect to fix, or a missing bound row plus a pinning test.** The row would be
`docs/MANIFEST.md` (planner); the test is the implementer's. **This bears on the sidecar byte-identity
invariant, so it is not a free choice** — read `docs/INVARIANTS.md` before taking it.

**The sibling claim was correctly killed** and the contrast is instructive: a block-style-reflow finding
was refuted against `MANIFEST.md:314` (*"Indentation follows the writer"*), pinned by
`test_a_two_space_indented_sequence_is_reindented`. The finder had cited `INVARIANTS.md` without
following its own pointer to the bounds list.

### D-37 — what should S6's state *mean*?

The message is wrong, but the right message depends on what the repository wants *"source gone,
sidecar present"* to mean — a move whose other half has not been seen yet, or a deletion. **Choosing the
wording is implementation; choosing the meaning is not.**

## What held up under adversarial testing

**The paid-path invariant survived.** The `ask` agent wrote its own subprocess harness, ran
`pnk ask --json` and `pnk budget` in a fresh interpreter with **both** key variables stripped, and
inspected `sys.modules`: no `anthropic`, no `anthropic.*`, no `pinakes.deep.client`.
`pinakes.deep.estimate` present as designed. `pnk ask --deep` refused cleanly for the missing key and
**named `PINAKES_ANTHROPIC_API_KEY` specifically**, never the SDK's own variable. Nothing spent.

## Build order

**The coder proposed S2, S3, S1 and that order is adopted** — silent loss before loud crash, because a
green `doctor` over a lost document is the failure nobody can see.

| # | Item | Blocked on | Owner |
|---|---|---|---|
| 1 | **S2** — silent index loss behind a green `doctor` | nothing | coder |
| 2 | **S3** — the per-thread connection in `serve` | nothing | coder |
| 3 | **S1** — `PermissionError` aborts the whole walk | nothing | coder |
| 4 | **S4** — escape at render in `template.py` | nothing | coder |
| 5 | **S5-S9** | nothing | coder |
| 6 | **D-36** — fix, or bound row plus test | the decision | user, then split |
| 7 | **D-37** — what the state means | the decision | user, then coder |
| 8 | The five low findings | S1-S9 | coder |

**S4's fix is escape at render, not reject at `init`.** Settled between the two sessions: it repairs the
mechanism where the defect actually is, changes no `init` contract, and `name = "Bob's \"Special\" KB"`
round-trips. Rejecting fixes one call site and leaves `_render` unescaped for the next variable that
carries user text. **Rejecting raw control characters as well is a nicety**, worth folding in only if it
stays cheap and does not grow a decision of its own.

**S1, S5, S6, S8, S9 all share one shape** — an input the tool accepts and then mishandles, rather than
refuses. Whoever builds them should say whether that is one fix or five; this plan does not assume.

## The corpus rule does not apply

Nothing here touches chunking, fusion, reranking or the confidence signal, so no golden-set eval is
owed. `confidence_reason`'s wording (low findings) is a message, not a signal change.
