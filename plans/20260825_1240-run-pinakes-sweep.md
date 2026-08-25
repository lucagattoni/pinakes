# Running Pinakes found defects that reading it did not

**This title deliberately carries no count.** It said *fifteen*, then S16 arrived and falsified it in
both entry points, then S17 arrived and falsified it again — twice inside two days. **The live tally
is the section headings below** (High, Medium, Low), and as of 20260825 23:06 it is **seventeen**.

**Written 20260825 12:40 UTC against `main` at `c2c69cb`.** Produced by a coder session sweeping seven
command surfaces with fourteen agents, each finding re-run from a clean directory by a verifier
prompted to **refute** it. **Five findings were refuted and dropped. One came back with no verdict at
all and was recovered.** What follows is what survived.

**This file proposes work. Its two decisions — D-36 and D-37 — were TAKEN by the user 20260825 18:16**, both on options the adversarial pass invented rather than the first-pass ones: [`20260825_1803-open-decisions.md`](20260825_1803-open-decisions.md). **Read that file, not the options below, before building either.**

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
| **†‡** | Found by the *review of another fix*, then reproduced independently by the planner on `main` |

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

### S16 †‡ — swapping two documents' names crashes `sync` and leaves the index describing the wrong file

**Found 20260825 18:24 while reviewing S2's fix; independent of that branch and reproduced with the fix
removed.** Not from the original seven-surface sweep — it came out of the adversarial review of S2, which
is itself the point: *the review of a fix found a defect the fix was not about.*

**Reproduced end to end by the planner on `main` at `32442db`**, free path, scratch KB outside the repo:

    pnk init <kb> --backend light        # two documents, a.md and b.md, synced clean
    # swap both names, sidecars travelling with them, as a `git mv` pair leaves them
    pnk sync                             # exit 1, sqlite3.IntegrityError:
                                         #   UNIQUE constraint failed: documents.path
                                         #   at src/pinakes/sync.py:2331

**Three separate failures, and the third is the worst.**

| | |
|---|---|
| `pnk sync` | **exit 1**, raw Python traceback — no remedy, no failure ledger entry |
| `pnk search` | returns **`docs/b.md — Beta`** while `b.md` on disk contains **Alpha**. The index describes the wrong file and answers queries from it |
| `pnk doctor` | **exit 0**, `OK` on every row |

**This is the S2 shape reached from a different direction** — the index and the disk disagree, and the
diagnostic command says the KB is healthy. It is **live in `0.30.2`**, which is what `pip install pinakes`
serves today.

**Why an ordinary action reaches it**, from the coder's analysis of `pair()`: a swap emits
`[SoftDelete(X), Adopt(Y@a.md), SoftDelete(Y), Adopt(X@b.md)]`. The `UNIQUE` constraint on
`documents.path` fires because the first `Adopt` writes a path the second document still holds.
**`git mv` of two files past each other is not an exotic input** — renaming a pair of notes is.

**Not to be folded into S2 without care.** S2's first fix made this *worse*, not better: a scoped DELETE
turned this crash into a **green sync that silently loses a document**. The coder's rework moves the fix
into `pairing` — do not emit `SoftDelete(id)` when the same plan `Adopt`s that id — which is a pure
function and testable exhaustively. **Read S2's status before touching this.**

## Medium — seven

| # | Surface | Finding |
|---|---|---|
| **S4** ‡† | `init` | **A KB name that is not valid TOML bricks the KB at creation, silently.** `init` exits 0 and prints *created*; every later command exits 1; `pnk init` refuses to repair it (*"already a KB"*), so **the remedy surface is empty** and recovery is hand-editing TOML. Three classes: `"`, `\`, and control characters **other than tab** (tab is legal in a TOML basic string — an earlier four-class claim was wrong). **No flag is needed** — the directory name reaches the same path via `root.name` (`init.py:355`). **The verifier widened it usefully: `--name 'C:\notes\kb'`** — a Windows-style path as a KB name — **is far more plausible than a quoted name.** The hole is in the mechanism: `template.py:_render` has no notion of TOML escaping, so any future variable carrying user text inherits it |
| **S5** ‡ | `sync` | `--sidecars-only` together with `--index-only` **writes a sidecar** while reporting `0 indexed, 0 renamed, 0 metadata-only, 0 unchanged, 0 removed` |
| **S6** ‡ | `sync` | *"moved without its sidecar, so a new id was minted"* fires on **ordinary deletion**, naming a file that no longer exists. The verifier corrected the finder: it **does** also fire on a genuine move, so the original title's second half was wrong and was dropped |
| **S7** ‡ | `doctor` | The failure ledger **never clears**, and its own remediation text is wrong. **The verifier strengthened this**: it does not clear when the document is *repaired* either, which is the normal user path |
| **S8** ‡ | `search` | Negative `-k` is passed through as a **raw Python negative-slice bound**: `-k -1` returns 19 passages, `-k -100` prints `no passages matched.` at **exit 0** |
| **S9** ‡ | `ask` | `pnk ask -k -1` raises an **unhandled traceback** from `deep/estimate.py:456`. Held at medium because it is loud and immediate rather than silent |

### S17 † — `pnk sync` prints a remedy that never works, and the document stays out of the index

**Found 20260825 by the coder while adversarially reviewing S2; a dead agent's probe file recovered it.
Pre-existing on `main`, unrelated to S2 and unfixed by it. Reproduced end to end by the planner** on a
scratch KB outside the repo, free path, against `main` at `03e6f86`:

    pnk init <kb> --backend light      # a.md and b.md, synced clean
    git mv docs/b.md docs/c.md         # an ordinary rename, sidecar travelling with it
    git mv docs/b.md.pnk.yaml docs/c.md.pnk.yaml
    printf '...' > docs/b.md           # a NEW, unrelated document at the freed path
    pnk sync                           # exit 1

    failed: docs/c.md: SidecarError: c.md.pnk.yaml appeared after the walk had
            already read this directory.
    Run `pnk sync` again — the second pass will pick it up.

**The remedy is wrong, and it is wrong in a way that loops.** I ran `pnk sync` three more times: the
identical failure each time, `0 indexed`, and **`docs/c.md` never gets a row at all** — `select path,
state from documents` returns only `a.md` and `b.md`. `pnk search` cannot reach its text. The
document's published ULID sits in the sidecar on disk and in no index. Following the printed advice
literally never terminates.

**What I established that neither the finder nor the first reading had, and it lowers the severity:**

| | |
|---|---|
| `pnk sync` | **exit 1** — this is loud, not silent |
| `pnk doctor` | **`WARN failures: 4 recorded: docs/c.md (index)`** — it *is* surfaced… |
| …but | `doctor` **exits 0**, and **`OK orphaned sidecars: none`** — the check whose name sounds like it would catch a sidecar whose document is absent from the index does not catch this one |
| **`pnk sync --rebuild`** | **RECOVERS IT COMPLETELY** — `3 indexed`, `docs/c.md` active. Nothing is lost |
| `touch docs/c.md` then `pnk sync` | does **not** recover it — `0 indexed, 3 unchanged` |

**Severity: MEDIUM, and the reasoning is stated because both earlier readings guessed differently.**
It is not the S2 shape — nothing is silent, sync exits non-zero and doctor WARNs. **And the data is
not lost: a working remedy exists and is one flag away.** What is broken is that the tool names the
*wrong* one and sends the user into an unbounded loop. Weighted the other way it would be HIGH,
because a document is unreachable from search until somebody guesses `--rebuild` — the printed advice
will never get them there.

**The fix is two-part and the second half is the real one:** correct the message to name
`pnk sync --rebuild`, **and** make the second pass actually pick the sidecar up, since the message is
only wrong because the behaviour it promises does not exist. Fixing only the string leaves an ordinary
`git mv` pair requiring a full rebuild.

**Root cause is the walk's directory-read ordering, not pairing** — so it is *not* foldable into S2 or
S16 and needs its own increment. Each failed sync appends another identical failure row (4 after four
runs), so the ledger grows without bound while the state never changes.

## Low — five

Symlink loop invisible to both `sync` and `doctor` (**verifier downgraded high → low**: a loop resolves
to no content, which is ordinary Unix semantics); `-k 0` silently ignored on both `search` and `ask`;
`--source-type` accepts any string unvalidated, so a typo reads as an empty KB; `confidence_reason`
reports *"nothing matched the filters"* **when no filters were given**.

## Two genuine decisions — ✅ **BOTH TAKEN 20260825 18:16**

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
