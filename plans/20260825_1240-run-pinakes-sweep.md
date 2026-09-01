# Running Pinakes found defects that reading it did not

**This title deliberately carries no count, and neither do the section headings — because the counts
in this file have never reconciled.** The title said *fifteen*; S16 falsified it in both entry points,
S17 falsified it again, and checking the arithmetic on 20260826 03:55 found the section headings were
already wrong independently of that: *High — three* stood over **four** entries (S16 was filed there
without updating it), and *Low — five* is a prose sentence naming **four** classes.

**What is countable, and is therefore all this file asserts: thirteen numbered findings — S1–S9,
S16, S17, S18, S19.** There is no S10–S15; the Low section describes its findings in prose rather
than numbering them, which is why no total in this file has ever been reproducible. **Do not quote a
total from here, and do not add one** — count the numbered findings, or say "the Low section's
classes" and leave them uncounted. Fixing the taxonomy properly means deciding whether an unnumbered
prose class is one defect or several, and **that is a decision nobody has taken.**

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

## High

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
                                         #   raised by _index_document's INSERT (line moved twice; grep it)

**RE-REPRODUCED 20260826 06:49 UTC by the planner, and this second run is the one that matters.** The
reproduction above ran on `main` at `32442db` — **20260825 18:18, which is *before* S2's fix landed**
(`3876b57`, 20260826 04:06). That mattered because **S2's fix cured S17 as a side effect**, so
whether it also cured S16 was an open question that nobody had asked and no record answered.
`CLAUDE.md` meanwhile claimed *"reproduced on `main` 20260826"*, which **nothing in this file
supported**.

It is still live. Re-run against a `src/` tree **byte-identical to `origin/main` at `a4a754a`**
(`git rev-parse HEAD:src` equal on both), free path, `light` backend, scratch KB outside the repo,
all three failures intact:

- `pnk sync` — **exit 1**, raw traceback, `sqlite3.IntegrityError: UNIQUE constraint failed:
  documents.path`, raised at `src/pinakes/sync.py:2411` in `_index_document`
- `pnk search "Beta gadgets"` — **exit 0**, first hit `docs/b.md — Beta` quoting *"Beta content about
  gadgets"*, while `b.md` **on disk** begins `# Alpha`
- `pnk doctor` — **exit 0**, every row `OK`, including **`OK failures: none recorded`**

**The lesson is S17's, and it is why this was checked rather than assumed:** a defect recorded
against a moving tree needs its sha, and *"still live"* written on one day is a claim about that day
only. This one survived; S17 did not, and both were recorded the same way.

**Three separate failures, and the third is the worst.**

| | |
|---|---|
| `pnk sync` | **exit 1**, raw Python traceback — no remedy, no failure ledger entry |
| `pnk search` | returns **`docs/b.md — Beta`** while `b.md` on disk contains **Alpha**. The index describes the wrong file and answers queries from it |
| `pnk doctor` | **exit 0**, `OK` on every row |

**This is the S2 shape reached from a different direction** — the index and the disk disagree, and the
diagnostic command says the KB is healthy. It is **live in the published release**, which is **`0.31.0`** — verified against the index itself, `pypi.org/simple/pinakes/` carrying `pinakes-0.31.0-py3-none-any.whl`, with `refs/tags/v0.31.0` on `origin` and `__version__ = "0.31.0"`. **This read `0.30.2` until 20260831 22:36**, which would let a reader tell a user to *upgrade past 0.30.2* as though that escaped the defect. It does not — the defect is live on the newest release.

**Why an ordinary action reaches it**, from the coder's analysis of `pair()`: a swap emits
`[SoftDelete(X), Adopt(Y@a.md), SoftDelete(Y), Adopt(X@b.md)]`. The `UNIQUE` constraint on
`documents.path` fires because the first `Adopt` writes a path the second document still holds.
**`git mv` of two files past each other is not an exotic input** — renaming a pair of notes is.

**Not to be folded into S2 without care.** S2's first fix made this *worse*, not better: a scoped DELETE
turned this crash into a **green sync that silently loses a document**. The coder's rework moves the fix
into `pairing` — do not emit `SoftDelete(id)` when the same plan `Adopt`s that id — which is a pure
function and testable exhaustively. **Read S2's status before touching this.**

## Medium

| # | Surface | Finding |
|---|---|---|
| **S4** ‡† | `init` | **A KB name that is not valid TOML bricks the KB at creation, silently.** `init` exits 0 and prints *created*; every later command exits 1; `pnk init` refuses to repair it (*"already a KB"*), so **the remedy surface is empty** and recovery is hand-editing TOML. Three classes: `"`, `\`, and control characters **other than tab** (tab is legal in a TOML basic string — an earlier four-class claim was wrong). **No flag is needed** — the directory name reaches the same path via `root.name` (`init.py:355`). **The verifier widened it usefully: `--name 'C:\notes\kb'`** — a Windows-style path as a KB name — **is far more plausible than a quoted name.** The hole is in the mechanism: `template.py:_render` has no notion of TOML escaping, so any future variable carrying user text inherits it |
| **S5** ‡ | `sync` | `--sidecars-only` together with `--index-only` **writes a sidecar** while reporting `0 indexed, 0 renamed, 0 metadata-only, 0 unchanged, 0 removed` |
| **S6** ‡ | `sync` | *"moved without its sidecar, so a new id was minted"* fires on **ordinary deletion**, naming a file that no longer exists. The verifier corrected the finder: it **does** also fire on a genuine move, so the original title's second half was wrong and was dropped |
| **S7** ‡ | `doctor` | The failure ledger **never clears**, and its own remediation text is wrong. **The verifier strengthened this**: it does not clear when the document is *repaired* either, which is the normal user path |
| **S8** ‡ | `search` | Negative `-k` is passed through as a **raw Python negative-slice bound**: `-k -1` returns 19 passages, `-k -100` prints `no passages matched.` at **exit 0** |
| **S9** ‡ | `ask` | `pnk ask -k -1` raises an **unhandled traceback** from `deep/estimate.py:456`. Held at medium because it is loud and immediate rather than silent |

### S2's abandoned first attempt — what it established, preserved before the branch is deleted

**`origin/20260825_1243-s2-silent-index-loss` was superseded: none of its code landed, and the S2
fix on `main` was written from scratch.** Its tip `508c61d` is a DO-NOT-LAND note carrying nine
review findings. **Code that never landed leaves no trace in the tree, so this is transcribed here
20260826 04:12 rather than lost when the branch is removed.** The defects it lists are fixed or
irrelevant; what is kept below is only what a future session would otherwise **re-derive**.

**Why the branch was condemned, in one line:** its fix turned a loud crash into **silent index
loss** on an ordinary `git mv` swap — `sync` exited 0 reporting *"2 renamed, 2 removed"* while
`docs/a.md` ended `state='deleted'` with zero chunks. **`check.sh` was green.** That is the whole
argument for the note: a fresh session reading a green gate would have landed a regression.

**🔁 WHAT SURVIVED ADVERSARIAL ATTACK — do not re-derive these.** All still true of the landed fix:

- **The scoped `DELETE` destroys nothing irreplaceable.** `links` has no FK to `documents`; the
  dangling-link check and the coverage ratio already join `state='active'`, so a soft-deleted row
  and an absent row are **indistinguishable to them**. The `chunks` CASCADE is a no-op — a
  soft-deleted row has no chunks. The extraction cache is content-hash keyed and untouched, and the
  ledger is append-only.
- **Paid-extraction provenance lives in the SIDECAR**, not the row, and survived every sequence
  tried.
- **Resurrection is intact:** delete-then-return keeps the same id, **because the sidecar is the
  identity and the row is not.**
- **No false positive** on: a never-synced KB, nested or multiple `[sources]` roots, an excluded
  `drafts/`, an orphaned sidecar before re-sync, or a broken-symlink document.

**⚠️ Two methodological findings worth more than the defects, both now landed as practice:**

1. **A test can pass with the entire fix removed.** `test_an_active_row_holding_the_path_under_another_id_still_conflicts`
   never called `_index_document` — it hand-inserted a row and asserted a raw SQL `UPDATE` raised.
   **That tests SQLite, not Pinakes**, and it was green against the mutant it existed to kill.
2. **A published timing number failed re-measurement twice.** The first attempt was measured at
   **2.25×** slower; the replacement was reported as *free* (0.822 s → 0.818 s) and, on re-running
   with the two builds **alternated against one KB** instead of once each in separate worktrees,
   is **+12.1% and +16.8%**. **Sequential runs across two worktrees drift by more than the effect.**

**Not preserved here:** the four `doctor` defects and the rework plan, all of which landed and are
therefore readable in `main`'s history and in `retro.d/`'s S2 fragment.

> ### 🧹 ✅ DONE — the branch is gone, and only the record of it was missing
>
> **Verified 20260831 22:36: `20260825_1243-s2-silent-index-loss` exists in none of the three
> places.** `git ls-remote origin` lists only `main` and the live branches; `git branch -a` shows
> no local or tracking copy; `git worktree list` shows no worktree. The precondition below was
> discharged too — `git grep -c "S2's abandoned first attempt" origin/main` on this file returns
> 2 — so the task was carried out and **only this box went unticked.** Kept, not deleted: a
> checkable precondition that was checked is the point of the box. The state it describes was:
>
> **`20260825_1243-s2-silent-index-loss` was on `origin`, local and remote both at
> `5917886`**, holding four commits that are not on `main`:
>
>     5917886  The lesson from the fifth test: per-test, never per-run
>     508c61d  DO NOT LAND THIS BRANCH AS IT STANDS — adversarial review failed it
>     f59f52f  S2 fragments: the changelog entry and what the sweep taught
>     96dae64  S2: a retired row blocked its own path, and doctor called it healthy
>
> **It is to be deleted — but not until the section above is on `main`.** None of its *code* landed
> (the S2 fix was rewritten from scratch), so this repository's rule — *confirm the content actually
> landed before deleting a branch that is not an ancestor of the default branch* — is discharged by
> **this section**, not by the S2 commits. Until it is on `main`, the record exists only on a feature
> branch that could be reworked or abandoned.
>
> **The precondition is one command**, so this is a task rather than a thing someone must remember:
>
>     git grep -c "S2's abandoned first attempt" origin/main -- plans/20260825_1240-run-pinakes-sweep.md
>
> **Non-zero → delete all three copies**, in this order: remove the worktree, `git worktree prune`,
> delete the local ref, delete the remote ref, `git remote prune origin`, then **verify with
> `git branch -a` that nothing survives**. **Zero → do nothing yet.** A stale branch ref costs
> nothing; deleting the only copy of a record costs everything.

### S17 ✅ **FIXED on `main`** — `pnk sync` printed a remedy that never worked, and the document stayed out of the index

> ### ✅ FIXED, and this row was WRONG about it for four hours
>
> **Verified fixed by the planner 20260826 04:40, with a control**, on a scratch KB outside the repo:
>
>     main 03e6f86   sync fails: SidecarError, docs/c.md NEVER INDEXED, three retries identical
>     main 325ab9e   sync EXIT=0, "1 indexed, 1 renamed, 1 unchanged", docs/c.md ACTIVE
>
> **Nobody set out to fix it.** The **moved-sidecar guard**, which came out of S2's *second*
> adversarial pass, fixes S17 as a side effect — S17 is the same *one id, two paths* shape: the
> sidecar travels to the new path while the index still says the id lives at the old one. The guard
> stops the old path emitting anything, so adoption carries the id across and the new file mints.
>
> **🔁 THE REUSABLE ERROR, and it is why this row is kept rather than deleted.** S17 was measured
> against a *moving branch* and reported as a property of the defect. **It was true when taken and
> false four commits later, and nothing in the report could show that — because the report carried no
> sha.** A finding measured against a branch needs the sha it was measured at, or it silently becomes
> a claim about a tree that no longer exists. This row is one message away from having sent someone
> to rebuild a two-part fix for a defect that already works.
>
> **It still belongs in a changelog**: it shipped broken in 0.30.2 and is fixed in whatever cuts next.

**The record of the defect, as it was:**

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

### S18 ✅ **FIXED on `main`** — a restored paid document was refused forever, and the reason it printed was false

> ### ✅ FIXED 20260830 (`a2f5b86`), and this heading read `†` OPEN for a day after it shipped
>
> **Caught 20260831 by the coder's entry-point audit, not by any gate.** `pnk sync` no longer tells
> a restored, byte-identical paid document that its content changed: the outcome is a `failures`
> row naming **`RETIRED`**, which [`docs/DESIGN.md`](../docs/DESIGN.md)'s paid-drift table now
> specifies rather than leaving to the code. The fuller answer — reviving it free from a warm
> extraction cache — is **deliberately not taken**: `_paid_survivor_in_current_index` requires
> `state = 'active'` and `WalkedSidecar` carries no provenance, so `pair()` can see neither fact it
> would need. **The cost is recorded rather than hidden: a warm cache still pays.**
>
> **This is the third time a section in this file outlived its own fix** — S17 and S2 were both
> closed-but-reading-live before it. **A heading is not a gate**, and `plans/` has none.

**Found by the coder 20260826 while adversarially reviewing S2. Severity **MEDIUM**.** The
diagnosis that closed it was a *static reading of six sites* — `pairing.py:298`, `sync.py:1322`,
`:1363`, `:2190-2208`, `DESIGN.md:1036`, `errors.py:380` — and it found that `pairing.py:298`
**pre-empts a decision `sync.py:2190` already makes correctly**, one layer up and with less
information. `DESIGN.md:1036` had forbidden by name the exact string the tool printed.

**⚠️ Cite it by symbol, not by line.** It was `pairing.py:244` when first recorded and `:298`
after the S2 rework, and it has moved twice more since — which is why **no number is written
here any more**. Find it with `grep -n 'hash_changed = ' src/pinakes/pairing.py`.

> **🔁 The same failure as S17, one level out — and having both here is the point.** S17 was a
> *finding* measured against a moving tree and reported without its sha; this is a *line number*
> measured against a moving tree and recorded without one. **A citation is a measurement.** Both were
> correct when taken and false within hours, and in neither case could the record show it. The
> remedy differs by kind — a finding carries the sha it was measured at, a citation names a symbol
> or a heading instead of a line — but the failure is identical, which is why this repository keeps
> re-deriving it under two different names.
>
> **And a third instance the same day, in a different register:** the predicate `a table cell begins
> with ">"` flags `> ~2M` (*greater than two million*) as a swallowed blockquote. **The signal has to
> be a function of the property, not of something correlated with it** — the defect is that a
> swallowed blockquote leaves the row's *remaining cells empty*, and that is what a gate must test.
> Same family as `check.sh | tail` reporting `tail`'s exit status, and as `mkdocs --strict` exiting
> 0 on both the broken and the fixed form. **If any of this reaches a gate, that sentence belongs in
> its comment.**

**Provenance, stated because this file's own § *Provenance* says the markers are not uniform.** The
planner **verified the code claim directly on `origin/main`** and did *not* reproduce it end to end —
that requires a paid-extracted document and a paid backend. **The end-to-end behaviour is the coder's
reproduction, not the planner's.** Weigh it accordingly.

`src/pinakes/pairing.py`'s same-path branch **read, before S18's fix** — it does not now, and
grepping for this line finds nothing:

    hash_changed = document.content_hash != file.content_hash or document.state == DELETED

**On `main` today it separates the two:** `content_changed` and `retired` are computed apart,
`hash_changed` is their `or`, and the reason is `CHANGED` or `RETIRED` accordingly. The analysis
below is why that split exists; it is not a defect still in the tree.

**The second disjunct forces `hash_changed` True for any retired row, including one whose file is
byte-identical to what was indexed.** If that row's `extraction_backend` is paid and the run is free,
the `recorded_is_paid and not effective_is_paid and not override` branch below it then emits `PaidExtractionRequired` — so **a paid document deleted and restored unchanged
is never resurrected**, and `src/pinakes/sync.py`'s refusal message told the user it was extracted with the paid backend *"but its content changed."* **It did not.** **[Fixed by S18: `sync.py` now selects the wording from the reason, and the retired case reads *"and its content is unchanged, but the document was retired and that extraction's text was discarded with its chunks."* The false sentence about the user's own file is gone; the original wording survives only where it is true.]** The remedy the tool prints asks them to spend
money re-extracting a file that has not moved a byte.

**Why the disjunct is there matters for the fix**: its *"Decision 9's paid-protection clauses"* comment states the intent —
*"never silently keep indexing text a changed file no longer matches"* — which is about a **changed**
file. A retired row is being treated as a changed file to reuse one branch. The fix must keep the
paid-protection clause and stop conflating *retired* with *changed*, so this is not a one-token edit.

### S19 † — `pair()` produces an inapplicable order for renames that are NOT cycles

**Found by the coder 20260826. Severity **MEDIUM**, and it changes the scope of S16 rather than
sitting beside it. STILL OPEN — the planner reproduced the cycle half 20260826 04:40 on `main` at
`325ab9e`**: swapping two documents' names still exits **1** with
`sqlite3.IntegrityError: UNIQUE constraint failed: documents.path`, and the index still shows both
paths `active`, so the swap is rejected wholesale rather than applied wrongly.

**What the planner did NOT reproduce**, stated because S17 has just shown what an unverified report
costs: **the non-cyclic half.** The claim that the same error fires on rename walks which are *not*
cycles and *do* have a valid order is the coder's measurement, read against `pairing.py` and
consistent with the cycle behaviour above — **but it is the half that carries the rescoping, and it
deserves its own control before S16 is built to it.**

**S16's known-deferred case is a *cycle*** — a swap, where no ordering works without a temporary
path. **This is different and worse-scoped: the same `IntegrityError` fires on rename walks that are
not cyclic and for which a valid order does exist. `pair()` simply does not compute one.** The
same-path loop emits its `Adopt` at each surviving path in walk order (sorted by path) while the
adoption loop emits the moves afterwards, so **an `Adopt` onto a freed name can be emitted before the
`Adopt` that frees it** — an ordering the database rejects and a correct implementation would have
avoided.

**🛑 CONSEQUENCE FOR THE S16 INCREMENT, and this is why it is filed here rather than later: fixing
cycles alone does not fix this class.** A build-order row reading *"make swaps work"* **under-scopes
it**. S16's fix must **order the applicable plans**, not only detect and break the inapplicable ones.

**Provenance — SUPERSEDED 20260826 07:18 UTC. It now reproduces, on both sides, run by both sessions
independently.** This paragraph used to say the planner had *not* reproduced S19 and that the
ordering argument was read against `pairing.py` rather than measured. **Both halves have since been
run**, and the control was built before the fix, which is what S17 cost us the last time it was not.

**The end-to-end reproduction (coder), `src/` byte-identical to `origin/main`**
(`git rev-parse HEAD:src` → `db34cd8125b69c29234fbcc9575b8260b2700fad`), `light` backend, scratch KB
outside the repo. The walk is **not** a cycle and a valid order exists — `b.md → c.md` then
`a.md → b.md`, freeing `b.md` first makes the whole plan applicable. **Four symptoms, and the fourth
is new:**

| | |
|---|---|
| `pnk sync` | **exit 1**, raw traceback, `sqlite3.IntegrityError: UNIQUE constraint failed: documents.path` at `src/pinakes/sync.py:2411` in `_index_document` |
| `pnk doctor` | **exit 0**, every row `OK` — including `OK retired documents: none` and **`OK failures: none recorded`** |
| `pnk search` | **exit 0**, `[1] docs/b.md — Beta` quoting Beta's body while `b.md` **on disk** begins `# Alpha` |
| `pnk search`, second hit | **`[2] docs/a.md — Alpha`, and `a.md` does not exist on disk at all.** The index answers from a path that is **gone**. The other three say the index describes the *wrong* file; this one says it describes a file that is not there |

**The plan itself, driven directly — measured twice, independently.** The coder drove `pair()` and
the planner re-ran it from a separately written probe. **Three rows matched exactly.**

**🛑 THIS TABLE IS THE *BEFORE* STATE, at the `src/` tree named above.** It is a measurement, not a
description of `pair()` today, and it stays true as that. **The ordering fix changes the two
non-cycle rows** — the chain comes out *strictly reverse*, which is the applicable order — and the
**cycle row is unchanged, deliberately.** The after column is added when the fix lands and its
values are measured, not before.

| Walk | `pair()` emits | Applicable? |
|---|---|---|
| **Cycle** — `a ↔ b` | `Adopt(B→a.md)`, `Adopt(A→b.md)` | **No order works.** Each target is held by the other; needs a temporary path. This is S16's known-deferred case and it is genuinely different |
| **Non-cycle, two** — `b→c`, `a→b` | `Adopt(A→b.md)`, `Adopt(B→c.md)` | **A valid order exists and this is not it.** Reversing the two is applicable |
| **Non-cycle, chain of three** — `a→b`, `b→c`, `c→d` | `Adopt(A→b.md)`, `Adopt(B→c.md)`, `Adopt(C→d.md)` | **Emitted in exactly the wrong order**; the valid order is strictly reverse |
| **Non-cycle onto a free name** — `b→z` | `Adopt(B→z.md)`, plus `Skip`/`RefreshMetadata` for the untouched document | **Yes. Green today.** The two runs differ here only by construction — an unchanged sidecar hash gives `Skip`, a changed one `RefreshMetadata` — and the row is green either way |

**🛑 USE THE CHAIN OF THREE AS THE PINNING TEST, not the two-file shift.** The coder's reasoning, and
it is the reason this row exists: **the valid order is *strictly reverse*, so no accident of
path-sorting can produce it, and a fix that merely reorders two adjacent actions passes the two-file
case while failing this one.** A control is only worth writing if it kills the plausible-but-wrong
fix.

**The mechanism, confirmed rather than inferred:** the same-path loop emits its `Adopt` at each
surviving path in walk order (sorted by path), and the adoption loop emits the rest afterwards.
**Neither loop knows that a target path is still held by a row this same plan is about to move.**
`documents.path` being `UNIQUE` is the only reason anything notices — and it notices by crashing.

### The cycle's price — found by building it and backing it out (20260826 07:30 UTC)

**Recorded because no plan had it, and because a build-order row reading *"make cycles work"* would
under-scope the cycle exactly as *"make swaps work"* under-scoped the chain.**

The obvious remedy for the cycle class is a clean refusal — `pair()` raising before anything is
applied, rather than emitting a plan that crashes halfway. **The coder built it, it worked, and it
was backed out**, because it breaks **five committed tests**, three of which are guards that exist
*only while a cycle still produces a plan*:

| Guard | What it can only observe by watching a plan be applied and fail |
|---|---|
| `tests/test_pairing.py::test_a_name_swap_never_retires_an_id_the_same_plan_adopts` | the plan does not retire an id it also adopts |
| `tests/test_pairing.py::test_a_three_way_rename_cycle_adopts_every_id_and_retires_none` | every id survives a three-way cycle |
| `tests/test_sync.py::test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row` | **the silent-loss shape S2 exists to prevent** — no live document loses its row when the second half fails |

**So refusing the cycle cleanly is a decision about behaviour, not an implementation detail**, and
its price is denominated in **S2's coverage**. It is not taken here, and it was correctly not taken
inside an ordering fix. Whoever settles the cycle starts from this cost rather than rediscovering
it. **The same reasoning must land in `src/pinakes/pairing.py`'s docstring alongside S16's ordering
fix, where the person reaching for it will look.** *Verified 20260830: it is not there yet —
`grep -ci cycle src/pinakes/pairing.py` is `0` on `main`, and the text exists only on the unlanded
branch `20260826_0712-s16-s19-rename-ordering`. This sentence used to assert it as already true.*

**And one of those three guards contradicts itself, which will block exactly that person.**
`test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row`'s docstring says **"The sync's
own outcome is deliberately not asserted… what this test pins is that no live document loses its
row, which must hold *however that defect is settled*."** Its body implements that with
`contextlib.suppress(sqlite3.IntegrityError)` inside
`tests/test_sync.py::test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row` — **not** the
second, unrelated occurrence of the same suppress in
`test_no_pure_rename_ever_leaves_the_index_half_written` — which **pins the
exception type**. A cycle settled by raising anything else fails a test whose docstring promises it
would not. **Intent portable, code not.** Verified 20260826 07:30. Owner: **coder**, unscheduled — it blocks
nobody until the cycle is settled, and it blocks that person completely.

**So the two classes are now measured, not argued, and they need different fixes:** ordering the
applicable plans fixes the **entire chain class**; **cycles remain** and need a temporary path. When
the chain class is fixed, **the cycle case must be shown still failing, deliberately and in the
commit message** — otherwise *"swaps still crash"* becomes *"swaps are fixed"* in someone's summary
and the next session builds on it. That is S17's failure exactly.

## Low

Symlink loop invisible to both `sync` and `doctor` (**verifier downgraded high → low**: a loop resolves
to no content, which is ordinary Unix semantics); `-k 0` silently ignored on both `search` and `ask`;
`--source-type` accepts any string unvalidated, so a typo reads as an empty KB; `confidence_reason`
reports *"nothing matched the filters"* **when no filters were given**.

## Two genuine decisions — ✅ **BOTH TAKEN 20260825 18:16**

### D-36 — `pnk link` detaches a trailing comment from an alias-reference line ✱

`sameTags: *commontags      # alias reusing the anchor above` becomes two lines, the comment orphaned
onto its own line with 27 spaces of padding. Reproduced byte-for-byte.

**It is not on the bounds table.** `docs/MANIFEST.md`'s table under *"Bounds on that…"* lists ten exclusions and none covers it:
the anchor carries a real value, nothing is deleted, the name is not reused, it is not self-referential.
`MANIFEST.md:303` says plainly *"Comments … all survive a rewrite"*, and `docs/VERIFICATION.md`
pins that promise in its row *"comments survive a rewrite through `pnk link`"* (L6,
`tests/test_cli_link.py::test_comments_survive_a_rewrite_through_pnk_link`). **The citation was
`:282` until 20260831 22:36 and had rotted twice** — quote the row, never the line: this file's own
rule is that a citation names a symbol or a heading rather than a line. All six anchor/alias tests in `tests/test_sidecar.py` were checked — **none covers a
comment on an alias reference.**

**So it is either a defect to fix, or a missing bound row plus a pinning test.** The row would be
`docs/MANIFEST.md` (planner); the test is the implementer's. **This bears on the sidecar byte-identity
invariant, so it is not a free choice** — read `docs/INVARIANTS.md` before taking it.

**The sibling claim was correctly killed** and the contrast is instructive: a block-style-reflow finding
was refuted against `MANIFEST.md`'s bounds row *"Indentation follows the writer"*, pinned by
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

**🔍 Audited 20260901 11:35 UTC — and the result is the opposite of what the parked table below shows.**
Every row here that read open was measured against the tree, one agent per row, plus an independent
spot-check of two verdicts. **Six of seven were correctly open.** The exception is **row 3 (S3)**,
which read open for **nine days** after `e526e29` landed the fix on 20260831 — found by a peer reading
`src/`, not by any gate.

| Register | Rows checked | Stale | Rate |
|---|---|---|---|
| This build order | 7 | 1 | **14%** |
| *Decided work with an owner and no build order* (below) | 8 | 4 | **50%** |

**The difference between those two rates is readership, not discipline.** This table is the one an
implementer opens to pick up work, so a stale row here meets a reader who can falsify it. The parked
table exists precisely so that nobody has to read it, and it rotted at three and a half times the
rate. **A register decays at the speed of its neglect** — so the fix below is a liveness command per
row, and the fix here is that every open row now carries a **dated measurement** with the citation
that settles it. A dated measurement of something that happened once does not decay; a count of what
is in the tree today does.

**The coder proposed S2, S3, S1 and that order is adopted** — silent loss before loud crash, because a
green `doctor` over a lost document is the failure nobody can see. **S16 takes the first unbuilt slot
on that same reasoning**, and the reasoning is stated rather than assumed: it is the only live finding
that is *both* halves at once — `sync` raises, **and** the index is left describing the wrong file
while `doctor` exits 0 — and it was **reproduced on `main` 20260826**, after S2's fix had landed.

**Reconciled against the tree 20260826 06:19 UTC at `c1125ef`, re-verified at `a36f0e6`** — which
landed while this pass was being written and changed no file in `plans/` or `docs/`. Every row below was
re-derived by command rather than carried forward, and the rows for S16, S18 and D-36's schedule did
not exist before that pass. **Where this table and the *Actionable* table in
[`20260825_1252-plans-sweep-findings.md`](20260825_1252-plans-sweep-findings.md) disagree, this one
wins.** That one is a dated snapshot, not a queue: eleven of its rows — eight reading *LIVE*, three
*UNCLEAR* — were falsified by dispositions stamped between **20260825 12:52 and 20260826 04:35**,
and none of them reached it. It said *S2 · LIVE · blocked on nothing* from S2's landing at **04:06**
until this pass at **06:19**.

| # | Item | Blocked on | Owner |
|---|---|---|---|
| 1 | ~~**S2** — silent index loss behind a green `doctor`~~ — **BUILT.** Landed `3876b57` 20260826 04:06 UTC; text corrections `325ab9e` 04:35. Verify by opening `src/pinakes/doctor.py:463 _retired_documents`, not by reading this row | — | coder |
| 2 | ~~**S16**~~ — **✅ BUILT 20260831, landed `926bc43`.** ~~a two-file rename swap crashes `sync` and leaves the index describing the wrong file. **Re-reproduced 20260826 06:49 UTC against `origin/main`'s exact `src/` (`a4a754a`), after S2's fix — all three failures intact.** **Scoped by S19: the fix must *order* the applicable plans, not only detect and break the inapplicable ones.** **S19's non-cyclic half now reproduces — measured on both sides 20260826 07:19 UTC, by both sessions independently**, so the scope is settled rather than argued: **ordering the applicable plans fixes the entire chain class; cycles remain and need a temporary path.** **Pin it with the chain of three** (`a→b`, `b→c`, `c→d`), not the two-file shift — the valid order there is *strictly reverse*, so a fix that merely swaps two adjacent actions passes the small case and fails the real one. **Show the cycle case still failing in the commit message** | — **the decision it was held on was answered by the user 20260831 21:38 UTC** and is recorded in `docs/VERIFICATION.md`'s rename section, not here: `sqlite3.IntegrityError` is caught **narrowly**, on `SQLITE_CONSTRAINT_UNIQUE` naming `documents.path` only, so a cycle becomes a `PathStillHeldError` with a remedy while a CHECK or PK breach still escapes. **Contained, not resolved** — `pnk sync` still exits non-zero, and both new tests assert `not report.ok` for exactly that reason. **Two lessons the build produced, kept because neither is about S16:** (a) *three negative cases that agree with each other are not coverage* — the witness's PK, CHECK and `chunks` cases all failed on the **column** substring, so deleting the `sqlite_errorname` clause left it green; `NOT NULL constraint failed: documents.path` is the only breach carrying the right column under the wrong code, and it is what makes both clauses die individually. (b) **the adversarial pass, not the build, found that nothing pinned the exit code** — `report.ok` is `not self.failures`, so an edit to `ok` could have turned a contained failure into a silent exit 0 with every test green. Battery: **22 mutants, 22 killed** — run, not inferred from anchors. **S19's cycle half stays open**: contained now, still not resolved | done |
| 3 | ~~**S3** — the per-thread connection in `serve`~~ — **✅ BUILT.** Landed `e526e29` 20260831 22:22 UTC, *"S3: pnk serve answers after a pause instead of raising"*. `src/pinakes/serve.py:107-153` holds one `_ThreadConnection` per thread, reopened when the file signature changes; five tests pin it, including `test_a_search_from_a_second_thread_answers_instead_of_raising` — S3's own symptom. **This row read open for nine days after the work landed**, and a peer found it, not a gate | nothing | coder |
| 4 | **S1** — `PermissionError` aborts the whole walk · **✓ measured still open, 20260901 11:35 UTC** — `sync.py:693` calls `hash_file` inside a `try` that catches `PinakesError` only, and `PermissionError` is an `OSError`; `cli.py` `main()` catches only `PinakesError`. The one `PermissionError` test (`test_sync.py:1727`) exercises `create_sidecar` on the *write* path, not the walk | nothing | coder |
| 5 | **S4** — escape at render in `template.py` · **✓ measured still open, 20260901 11:35 UTC** — `template.py:209-223` `_render` interpolates raw through Jinja with no escaping; `templates/notes/pinakes.toml.j2:2` is `name = "{{ name }}"`; no test constructs a name containing a quote | nothing | coder |
| 6 | **S5–S9** — the accept-then-mishandle batch. **D-37 is what was stopping it**, at S6, and D-37 is answered · **✓ measured still open, 20260901 11:35 UTC** — all five unfixed: `cli.py:333` `-k` is `type=int` with no positivity check (S8/S9); `sync.py:1108` short-circuits on `sidecars_only` before `index_only` is read (S5); `sync.py:283` comments that nothing ever deletes from `failures` (S7) | nothing | coder |
| 7 | ~~**S18** — a restored paid document is refused forever, and the reason it prints is false~~ **✅ BUILT 20260830 `a2f5b86`**, with its `docs/DESIGN.md` row in `8bb4be0`. **This row outlived the section heading's fix by a day** — the heading was ticked and the queue was not, and the queue is the register that wins | — | done |
| 8 | **D-36's build** — **ANSWERED 20260825 18:16, option E** (derive the bound from a generative round-trip corpus; set the free `ruamel` options). *This row used to name two options; option E replaced both, and **the adversarial pass invented it** — read the decision, never a memory of the options.* **Scheduled here as of 20260826**; until then this row read *build unscheduled*, which is an owner with no queue position · **✓ measured still open, 20260901 11:35 UTC** — no generative round-trip test exists in `tests/test_sidecar.py` — option E's first half | nothing — answered | coder |
| 9 | **D-37's build** — **ANSWERED 20260825 18:16, option E**: gate the move hint on the **orphaned sidecar**, not the mint count. Also invented by the adversarial pass · **✓ measured still open, 20260901 11:35 UTC** — `pairing.py:481-483` still keys `moved_without_sidecar` on path-absence alone, ungated on the orphaned sidecar; `sync.py:406` prints the hint unconditionally | nothing — answered | coder |
| 10 | The Low section's findings (**four classes; the count of five is retracted in this file's header**) · **✓ measured still open, 20260901 11:35 UTC** — `cli.py:395-402` `final_k` is unguarded, and no class has a pinning test | S1–S9 | coder |
| 11 | **The FX guard, in two parts that must not be collapsed into one.** (a) Pin the rate at the **one call site** in `tests/test_cli_ask.py` with `monkeypatch.setattr`, **never** by widening `tests/conftest.py`'s `prices_never_age` — that fixture's commitment is that every model price and the FX rate stay *real*, and widening it is the defect wearing the fix's clothes. **No bound at the call site**: the assertion exists to discriminate €0.21 from €0.26, and a bound admits both. (b) Separately, bound the committed `usd_per_eur` in `src/pinakes/budget/prices.toml`, where the property being asserted is *somebody refreshed this*, not *it equals X*. **The commit message must say the limit out loud: a bound cannot catch stale-but-plausible** — `1.08` was plausible for the entire month it was wrong, `docs/RELEASING.md` § *Before you start* step 3 is the mechanism, and this is a backstop against a typo or a seed value left in place. **A row that reads as though it solves staleness is worse than no row**, because it retires the attention the procedure depends on. Found 20260831 by running step 3; 0.31.1 moved the literal `"0.21"` → `"0.20"` and **deliberately took nothing else**, because the choice is test design | nothing | coder |
| 12 | **A gate that a `retro.d/` fragment opens with a `## <title> (YYYYMMDD HH:MM)` heading.** `tools/fragments.py`'s retrospectives stream **synthesises no heading** — `render()` joins fragment bodies — so a heading-less fragment's bullets splice silently under the *preceding* fragment's heading, filed under a different incident. Nothing catches it: the assembled-document checker forbids only **adjacent duplicate** headings, and the rule that a section opens with a bullet is **changelog-only by design**, because retrospectives are free-form prose. **Place it beside `document_problems`, not inside it** — this is a property of a *pending fragment*, which is what `--check` reads, while `document_problems` reads the assembled result. **Three occurrences in one evening, 20260831**, by three different sessions; the third was found by running a draft of this very gate against the real `retro.d/` tree rather than against fixtures, which is also the lesson about where to point it | nothing | coder |
| 13 | **`tools/verify_rfc_golden_set.py` passes vacuously.** `--kb` is `required=True` (`:62`), `problems` starts empty (`:70`), the loop that fills it (`:72`) can add nothing for a KB with no golden set, and `:107`'s `if problems:` is then false — so `:112` prints the **positive** claim and `:113` returns `0`. A verifier that cannot fail is not a verifier. **Pin it with a test that asserts the empty-input case is non-zero**, in the shape of `tests/test_review_pass_gate.py::test_an_empty_journal_is_not_a_clean_bill`, which is the same defect already caught once in this repo | nothing | coder |
| 14 | **`tools/markdown_link_gate.py` fails a cross-fragment anchor that is correct.** It resolves a `#…` target against `anchors_of(path)` — the one fragment — but a `retro.d/`/`changelog.d/` fragment's real destination is the spliced document, where the anchor does resolve: `docs/RETROSPECTIVES.md:4034` links to `:3945` in exactly this form and `mkdocs --strict` passes. So the gate is red about a link that is right, and `retro.d/README.md` *instructs* writers to write it. It turned `main` red at `b6be317` (14 green, 1 red) and, because `check.sh` runs it under `set -e`, blocked three branches and left the checks after it unrun. The gate already models the fragment's **disappearance** at `:296-305` (`--apply` deletes it mid-release) and not its **destination** — half the same mechanism. **The framing is the coder's and it is better than "the gate contradicts a convention":** the gate exists to close *green on the branch, broken after splice* — the 0.12.0 incident `retro.d/README.md` records — and it closed that direction while **inverting the other** into *red on the branch, correct after splice*. One seam, two signs, and fixing one sign broke the other. **Resolve a fragment's `#…` against (itself ∪ pending siblings ∪ the splice target)**, the only resolution that gets both signs right at once, because both are the same question: *which document is this fragment a piece of?* **Both arms, one increment** (scope granted 20260901 11:30 UTC): also gate the inverse — a fragment linking a sibling by **filename** is green under both gates today and dead after splice, which is the 0.12.0 failure itself, recorded and never pinned. Then restore the two code-spanned links and delete the caveat from both fragment READMEs — those deletions dictated by the planner and pasted unchanged into the coder's commit (*Content mine, keystrokes yours*), because a landing that restores the links while the READMEs still say to code-span them is incoherent in the tree | nothing | coder |

**Rows 11 and 12 are not sweep findings and are in this table anyway.** Both were found on
20260831 — one by running `docs/RELEASING.md` step 3, one by three sessions tripping over the same
splice in one evening — and neither has an owning plan. Parking them in § *Decided work with an
owner and no build order* below would have reproduced exactly what that section exists to record:
**the G5 gate re-run aged 21 days there**. A queue position is the cheap half; giving them one here
costs two rows and nothing else.

**Row 12 includes the stamp — planner ruling, 20260831 23:40 UTC.** The coder asked whether the
gate should check the heading's timestamp as well as its presence, on the ground that *"a stamp gate
as `retro.d/README.md` states it would reject 14% of the corpus, including fragments nobody thinks
are defective"*. **It is a fair objection aimed at the wrong population, and the answer is yes,
build both halves.** Three findings settle it:

- **`retro.d/` is emptied at every release, so the gate never reads the corpus.** `--check` reads
  *pending* fragments. The 100 historical fragments live in `docs/RETROSPECTIVES.md` and in git
  history; not one of them is a file this gate will ever open. **The tree holds exactly one
  unconsumed fragment today and it passes both halves.** A rejection rate computed over consumed
  fragments describes a retrospective audit nobody proposed.
- **The denominator is 84, not 100.** Sixteen fragments predate the `YYYYMMDD_HHMM-` naming rule and
  are named for their increment instead (`i8-page-citations.md`, `l5b-the-library-swap.md`, …).
  The rule is *"the heading's stamp is a **copy** of the filename's prefix"* — **undefined on a file
  with no prefix**, so those sixteen cannot fail a check that cannot be evaluated on them. The
  coder's numerator is sound and its denominator was borrowed from a wider set, which is the
  third time in twenty-four hours; see [`20260830_0927-main-is-red-and-a-review-that-half-ran.md`](20260830_0927-main-is-red-and-a-review-that-half-ran.md)
  §§ *A seventh instance*, *An eighth instance*.
- **The defect is recurrent and currently caught only by luck.** Census, selector stated: the 81
  prefixed fragments whose add-commit is directly resolvable (3 more are lost to rename detection,
  and are not counted rather than guessed). **18 of 81 were wrong at the moment they were
  committed** — 8 with no stamp, 8 with a stamp that is not the filename's, 2 with no heading at
  all. **Four of the 18 were repaired by a later review pass** before a release consumed them, and
  the other fourteen were not. Review catches this defect sometimes; that is the argument for a
  gate, not against one.

**What the gate must accept is the rule as written, and nothing looser.** `(YYYYMMDD HH:MM)`
trailing the heading, equal to the filename's prefix — not an em-dash form, not a date without a
time, not *"UTC"* appended. All three variants exist in the history and each one is the composed
stamp the rule exists to stop. **The README needs no change; it already says exactly this.** The
fourteen historical fragments that would fail are not touched: they are spliced, published, and
correcting a stamp now would invent a precision nobody measured — the same reason pre-20260804
timestamps stay local.

**S19 gets no row of its own, deliberately.** It is a constraint on S16's fix, not a separate build —
giving it a row would licence someone to "do S19" and leave S16's ordering unfixed, which is the
opposite of what S19 says. **S17 needs no row either: it is ✅ FIXED**, as a side effect of the
moved-sidecar guard from S2's second review, verified with a control.

**S4's fix is escape at render, not reject at `init`.** Settled between the two sessions: it repairs the
mechanism where the defect actually is, changes no `init` contract, and `name = "Bob's \"Special\" KB"`
round-trips. Rejecting fixes one call site and leaves `_render` unescaped for the next variable that
carries user text. **Rejecting raw control characters as well is a nicety**, worth folding in only if it
stays cheap and does not grow a decision of its own.

**S1, S5, S6, S8, S9 all share one shape** — an input the tool accepts and then mishandles, rather than
refuses. Whoever builds them should say whether that is one fix or five; this plan does not assume.

## Decided work with an owner and no build order

**These are not sweep findings.** They are parked here because they have **nowhere else**, and that is
the point of the section rather than an accident of it: each was decided, each has an owner, and none
had a queue position anywhere in the repository. **The G5 gate re-run aged 21 days in exactly this
state** — handed to the planner by a retrospective, filed in no build order, invisible to every sweep
that reads headings.

**Why they are here and not each in their owning plan.** Three homes were possible: a new repo-wide
queue file (a fourth register, and this file already documents what happens when two registers of the
same facts diverge); a `## Build order` added to each owning plan (correct by ownership, but it makes
a coder read four plans to find out what is next, which is the cost that produced the 21-day seam);
or this section (one place a coder already reads, each row linking to the plan that owns the
decision). **The third was chosen** — it is the only one that neither duplicates a register nor
scatters the queue. Each row names its owning plan, and **that plan, not this table, owns the
decision's content.**

**🛑 Measured 20260901 11:17 UTC: four of these eight rows were already done.** The docs audit, the
`KB-UPDATES.md` §3 citations, the `test_review_pass_gate.py` rows and the `--questions` flag were all
finished — two of them **before this table was written**. **This section exists to stop work ageing
in a register nobody reads back, and it had become one**, at a 50% rate.

**So every row now carries a command that says whether it is still live, and you run it first.** Not
because a row lies, but because a row is a claim about the tree made on the day it was written, and
nothing re-checks it. The four that were spent each took under a minute to falsify — a `grep` for the
flag, a `comm` of rowed names against defined tests, a `git log` on the file. **The cost of the check
is a minute; the cost of skipping it is rebuilding landed work**, which this repository has come
within one message of twice.

| Item | Owning plan | Blocked on | Owner |
|---|---|---|---|
| **`_toml.py`'s unknown-key remedy** · **Live?** `grep -c 'requires_pinakes' src/pinakes/_toml.py` → **0** means still open (the second hypothesis is not offered yet) — offer the second hypothesis (*this manifest may have been written by a newer Pinakes: upgrade, or ask its author to declare `[kb] requires_pinakes`*) and repoint from `docs/DESIGN.md §2.1` — which delegated its field tables to `docs/MANIFEST.md` in 0.2.1 — to `docs/MANIFEST.md`. **Pin the new sentence with a test.** Forward-only, and that is its honest cost: it changes the *reading* build, so no window already open is helped | [`20260805_1313-decisions-init-titles-and-grammar.md`](20260805_1313-decisions-init-titles-and-grammar.md) | nothing — answered 20260825 18:16 (E+F) | coder |
| **The re-extraction loop's deferral trigger** · **Live?** `grep -c 'trigger' src/pinakes/extract/audit.py` on the module docstring — **0** means the planner still owes the text — ⏸ DEFERRED 20260825 18:16 **with a trigger**, and the trigger's home is `src/pinakes/extract/audit.py`'s **docstring**, read by whoever would build it, rather than a roadmap row read by a sweeper. **The text is dictated by the planner and pasted unchanged** (§ *Content mine, keystrokes yours*). **Verified 20260826: the docstring does not carry it yet** | [`20260727_1543-v0.2.md`](20260727_1543-v0.2.md) decision 12 / I7c | nothing — the planner owes the text, then the coder pastes it | planner → coder |
| ~~**`docs/VERIFICATION.md` rows for `tests/test_review_pass_gate.py`**~~ **✅ SPENT — closed 20260831, and this table never learned.** Re-measured 20260901: the module defines **16** tests and `docs/VERIFICATION.md` rows **16** unique names, `comm` empty in both directions. The row was already paid when it was written here. Original text: — it landed in `a36f0e6` **carrying no row**, and under D-34 *a gate's own correctness is a promise*, so it owes them. **No gate catches this**: `tests/test_verification.py` fails on a name that does not resolve, never on a module that is absent, so the denominator moved from 74 to 75 in silence. Not the coder's narrow exception — that covers only the row a test **you wrote** requires, and the session that wrote this one has ended | this file (§ *Decided work…*), raised 20260826 | nothing | planner |
| **The G5 gate re-run** · **Live?** `grep -rn 'G5' docs/STATUS.md docs/ROADMAP.md` — no verdict recorded means still open — its own three-leg gate, **no immediate-parent eighth leg**, ~2.4 h unattended CPU. **Split into halves that are separately ownable**: the coder clones the corpus, adds `headings = "numbered"`, runs `pnk sync --rebuild`, then `tools/graph_matrix.py`'s seven legs and `tools/graph_gate.py`'s three-leg gate; **the planner writes the verdict into `docs/STATUS.md` and `docs/ROADMAP.md`**. Expected result is another null, and `expand` stays `off` either way — it is worth running because a **shipped default** rests on an index where three of seven edge kinds derived zero. **Last: it blocks nothing.** If session time rather than CPU is the binding constraint, declining it is a legitimate outcome and the decision brief says so | [`20260825_1803-open-decisions.md`](20260825_1803-open-decisions.md) decision 7 | nothing | coder, then planner |
| ~~**The 20260807 docs audit's remaining findings — as ONE unit, not 34 rows.**~~ **✅ DONE 20260901 07:32 UTC** — all 34 closed in one landing, plus two findings nobody had raised; the plan's § *✅ CLOSED 20260901* is the disposition. **The three fences were done first, as this row instructed, and each was re-run as a control before its fix was written** — the `--scan-links` and unmatched-`.pdf` fences put the `edge(s) derived` line in *different* positions, which is why running beat reading. Original text: 34 documentation findings are open and each was re-verified against the tree by re-grepping its quoted string (20260826), not its line number. Five filed under `# Low` are **medium** by the file's own re-verification — `docs/CLI.md:468`, `GUIDE.md:190/285/535`, `VERIFICATION.md:27` — and three of those are `GUIDE.md` output fences that do not match what the commands print, **on a site published on every push to `main`**. Six findings are closed and five of those say so nowhere in their own section. **Start with the three fences**: a published page showing output the command does not produce is the only part of this that reaches a user | [`20260807_2143-docs-audit-findings.md`](20260807_2143-docs-audit-findings.md) | nothing | planner |
| ~~**Four rotted code citations in `docs/KB-UPDATES.md` §3**~~ **✅ DONE 20260901** — re-derived by reading each line, not by pasting this row's 20260826 values, which had themselves drifted again (`store.py` 250→**267**, `doctor.py` 236→**238**, `sidecar.py` 54/304→**304/564**). `_toml.py` has not moved since; its cite is **`:213`**, the `raise`, matching how the row's siblings point at the operative line. Original text: — assigned to T4, which shipped in 0.20.0 without them. Wrong: `store.py:205` at lines 37 and 78, `doctor.py:205` at 63, `sidecar.py:35,106` at 76, `_toml.py:184` at 77. Right today: `store.py:250 _check_schema_version`, `doctor.py:236 _template`, `sidecar.py:54/304`, `_toml.py:214` (verified 20260826 — **re-derive before pasting**, this citation has now rotted twice). F3's headline claim is separately closed: `KB-UPDATES.md:56-61` withdraws it, so the heading no longer names what is open | [`20260804_1016-template-release.md`](20260804_1016-template-release.md) F3 | nothing | planner |
| ~~**A `--questions` flag for `tools/reachable_ceiling_probe.py`**~~ **✅ SPENT — built and landed** `d35bfcc` → `657da0b` → `2d62cd1`. **Check before believing this row is live:** `grep -n 'args\.questions' tools/reachable_ceiling_probe.py` → hits at `:1064-1068`. Original text: — a live re-run hazard: `tools/build_rfc_corpus.py:434-451 write_golden_set` overwrites `<out>/eval/questions.yaml` unconditionally on every build (called at :505), and the probe hardcodes `root / "eval" / "questions.yaml"` at :1030 with no way past it (argparse at :991-1012 defines only `--kb`, `--fake`, `--drop`, `--json`). The flag is the named better fix; the wider conversion rewrite the section originally governed is **done**, and its *if the run is re-scoped* wording keeps the rest proposed rather than scheduled | [`20260803_2239-corpus-probe-run.md`](20260803_2239-corpus-probe-run.md) | nothing | coder |
| **The deferred `docs/ROADMAP.md` review, whose trigger fired at 0.18.0.** · **Live?** `grep -c 'defers a full review' docs/README.md` → **1** means still owed The audit defers a full ROADMAP review *until after T2*; T2 shipped in 0.18.0 and `docs/README.md` still records the review as *still owed* (**grep `defers a full review`, do not trust a line number — this citation read `:58` and the sentence is at `:68` as of 20260901**). **It lives in an audit header rather than a section, which is why every section-by-section sweep has missed it** — the same shape as the 21-day G5 seam above | [`20260807_2143-docs-audit-findings.md`](20260807_2143-docs-audit-findings.md) | nothing — the trigger fired at 0.18.0 | planner |

**The probe row's wording stands — planner ruling, 20260831 23:40 UTC.** The coder read the row as
claiming the probe *"silently measures a question set a rebuild overwrote"*, and correctly objected
that it has never been silent: since `a6a931b` (**authored 20260804 04:13 UTC, committed 05:01
UTC** — both stamps, because `--date=format-local` without `TZ=UTC` renders a third number and this
is the wrong night to quote one; three days before the runbook warning was written and 27 days
before this row) the probe records the golden set's resolved
path, `sha256`, question count and multi-hop count — `reachable_ceiling_probe.py:1078-1085` for the
JSON payload, `:1168-1169` for the text output, **both formats**, with a comment at `:1075` saying
it reads them *"while the file is certainly still there"*. **Verified here, not taken on report.**

**But neither this row nor the runbook ever said that.** This row says the probe has no flag to
point elsewhere — *"no way past it"*, which is the framing the objection claimed was missing — and
cites argparse at `:991-1012`. The runbook
([`20260803_2239-corpus-probe-run.md`](20260803_2239-corpus-probe-run.md):34) says a conversion left
at that path *"is silently clobbered by the next build"* — and the silent party there is
`build_rfc_corpus.py`, which overwrites unconditionally and tells no one. **Correcting a document to
answer a sentence the document does not contain is how a correction becomes the error**, which this
repository did once tonight already. **Nothing in the row or the runbook changes.**

**The sentence came from a handoff table, and the coder found that itself.** *"Stops a probe
silently measuring a question set a rebuild overwrote"* was a one-line summary in the previous coder
session's handoff, pasted into the next session at its start. It was then attributed to a plan **as
a verbatim quotation**, and that attribution reached a retrospective fragment, a commit message and
a message to the planner before anyone opened the row. Two review lenses caught the fabricated
quotation independently; the coder verified it against the row itself rather than accepting them,
and found the substantive half — **the correction was wrong, not just the citation.** It is retracted
in a fix commit on the same branch, with the wrong version deliberately left visible in `1d5e7ac`.

**This is the 20260823 shape a third time: a claim relayed between two agents and escalated before
anyone read the file.** What is new is where the claim came from. **A handoff table is a lossy
summary of a document, and the next session cannot tell its rows from quotations** — which is an
argument for handoffs that cite `file:line` rather than paraphrase, and the reason this ruling
records the provenance instead of only the verdict.

**One sentence is added to the runbook, and it is an addition rather than a correction:** the
copy-over dance the runbook prescribes is *verifiable*, because the probe stamps the `sha256` of
what it actually read. A runner can diff that against the converted file and know which set was
measured. **The residual defect is exactly as narrow as the coder scoped it** — no route to
re-measure a replaced set except to put the old file back where the next build overwrites it — and
`--questions` remains the fix, three lines and no guard.

## The corpus rule does not apply

Nothing here touches chunking, fusion, reranking or the confidence signal, so no golden-set eval is
owed. `confidence_reason`'s wording (low findings) is a message, not a signal change.
