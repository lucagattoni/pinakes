# The `.pinakes/` exposure question, and the status claims nothing gates

**Audience: the planner and the user. Goal: decide.** This file **proposes and does not take** four
decisions. Three are E5's, reserved since 20260812 and unchanged by the two increments that have
since touched the code; the fourth is new. Each carries pros, cons, a comparison and a marked
recommendation. **The precedent is
[`20260811_0720-decisions-gates-and-corrections.md`](20260811_0720-decisions-gates-and-corrections.md),
where this same class — an open correction that had converged on a fork — was taken by the user.**

**What this file supersedes.** Where
[`20260731_1202-open-corrections.md`](20260731_1202-open-corrections.md) § *`pnk init`'s gitignore
warning* says the required text is undecided, it still is — but its framing is now incomplete, and
§ X1 below is the reason.

---

## What was measured first — and one measurement inverts the recommendation

**None of these is inferable from the item that needs it**, which is why they lead. The
recommendation in D-31 was drafted the other way and rewritten after M2.

| # | Question | Answer, and how |
|---|---|---|
| **M1** | Does adding a correct `.gitignore` untrack a `.pinakes/` that is already committed? | **No.** Built a repo, committed `.pinakes/{deep/op1.json,ledger.jsonl,index.db}`, then added `.gitignore` holding `.pinakes/`. `git ls-files` still lists all three. Edited the transcript, ran `git commit -a`: **the verbatim question was committed again.** |
| **M2** | What does the **shipped** detector say about that repository? | **`_ignored_by_git(...)` → `True`. Protected.** The KB is committing the user's questions on every commit and Pinakes reports it safe. |
| **M3** | Why? | The probes are **opaque random tokens** (`init.py:_probe_paths`), chosen so no realistic pattern targets them. That also guarantees they are **never in the index**. `git check-ignore` consults the index by default: on the *tracked* `.pinakes/deep/op1.json` it answers **not ignored**; with `--no-index` on the same path, **ignored**. The probes can only ever ask the `--no-index` question. |
| **M4** | Does Pinakes say anywhere that ignoring does not untrack? | **No.** `grep -rniE "rm --cached\|untrack\|already[ -]tracked\|already in the index"` across `*.py *.md *.toml *.sh *.yaml`. Every hit is `tools/template_drift_gate.py`, `tools/mutate.py` or a retrospective about the **wheel**, none about a user's `.pinakes/`. No `git rm --cached` guidance exists in the repository. |
| **M5** | How much of the suite does `docs/VERIFICATION.md` name? | **2023 tests defined, 1106 named, 917 with no row — 54.7%.** Method: every `^def test_*` in `tests/test_*.py`, matched as `::<name>` in the document. |
| **M6** | Does `grep '^## '` reveal the status of every item in the open-corrections file? | **No.** `## Live` at :67, `## Closed` at :156. The item at :94 carries **`CLOSED 20260824 00:35`** at :120 — inside its body, twenty-six lines below its own `**Decided.**` line. |

**M5 carries a caveat that is the point of this file.** A peer counted the same population and got
1094/929 against my 1106/917. Neither is wrong; the matching rules differed. **Two honest counts of
one population differ by twelve, and nothing in either number says which rule produced it.**

---

# Part 1 — E5: what Pinakes promises about `.pinakes/`

## X1 — ✅ BUILT and on `main` (`35cdc79`, unreleased): the detector cannot see an already-tracked KB

**Built 20260825. What the increment changed relative to what this section asked for**, recorded
because two of the three were corrections to *this plan* rather than to the code:

| This section asked for | What shipped |
|---|---|
| an absolute pathspec, pinned by a test run **from a subdirectory** | the pathspec, in `_index_pathspec` — but **reclassified as defensive**: `_ask_git` pins git's cwd to `root`, so the behavioural test could not fail. The assertion moved onto the pathspec itself, which the relative form does kill |
| `rc=128` → `None`, asserted through `init` | asserted against **`_tracked_by_git`** instead: the reported field is a `bool`, so `None` and `False` collapse into it and an implementation returning `False` passed every end-to-end test |
| the remedy, ordered ignore-line-first | shipped, **plus an absolute path this section did not anticipate** — with the KB at `repo/kb/`, the relative form printed `fatal: pathspec did not match` from the repo root and left the KB tracked |

**Symbols rather than line numbers, because these lines have already moved once:**
`_index_pathspec`, `_tracked_by_git`, and the `pinakes_tracked` assignment — which sits **outside**
the adopted gate, as constraint #2 required.

**This is not a defect in the 0.30.2 detector. It is a boundary the 0.30.2 design chose, and nobody
wrote down.**

The regression caught on 20260825 was that three *named* probes (`index.db`, `ledger.jsonl`,
`deep/transcript.json`) were covered by an ordinary `*.db` / `*.json` pair while `index.db-wal` —
megabytes of verbatim document text — stayed exposed. The fix was to stop naming real files and
probe **opaque tokens** instead. That fix is correct and should not be undone.

**But a path that does not exist cannot be tracked, and `git check-ignore` reports a tracked path as
not-ignored.** So the current check answers exactly one question:

> *If a new file appeared under `.pinakes/`, would git ignore it?*

and is structurally incapable of answering the other one:

> *Is anything under `.pinakes/` in the index right now?*

**These come apart in the case that matters most.** A user runs `pnk init`, misses the warning,
runs `pnk sync` and `pnk ask`, then `git add -A && git commit`. Later they add `.pinakes/` to
`.gitignore` — prompted by the warning they finally read, or by a second KB. From that moment the
repository is, by Pinakes' own report, **protected**, while every `git commit -a` continues to
publish the deep transcripts. **Silent false reassurance, which is the class the 20260825 review
already judged worse than the noisy defect it replaced.**

**Fix (no decision needed — it is a correctness gap with one right answer).** Ask git the second
question with a second command, not a different probe: `git ls-files -- <root>/.pinakes`, where a
non-empty result means tracked.

### ⚠️ The obvious form of that fix is itself defective, and it fails in the same direction

**Reviewed and reproduced twice, independently, before this plan landed.** The first draft of this
section said `git ls-files -- .pinakes`, with a **relative** pathspec. Measured:

| State | `rc` | rows | Consequence |
|---|---|---|---|
| from the KB root, tracking 3 files | 0 | **3** | correct |
| **from a subdirectory, relative pathspec, same repo** | **0** | **0** | ⚠️ **silent false clean** |
| from a subdirectory, **absolute** pathspec | 0 | **3** | correct |
| genuinely clean repo | 0 | 0 | correct — **and identical to the false clean above** |
| staged, never committed | 0 | 1 | caught |
| outside any repository | **128** | — | must read as *unknown*, never *clean* |

**`pnk init` can be run from anywhere, so this is reachable rather than theoretical** — and a
genuinely-clean repository and a mis-scoped query produce **the same `rc` and the same row count**.
There is no exit status to lean on, so pathspec correctness cannot be left to the caller.

**Therefore, three binding constraints on the implementation:**

1. **The function takes the already-resolved KB root and builds the pathspec itself** —
   `:(literal)` + absolute. **⚠️ CORRECTED 20260825 08:30, after the increment measured it: this is
   defensive, not a bug fix, and the behavioural test prescribed here could not have failed.**
   `_ask_git` passes `cwd=root` to `subprocess.run` (`init.py:94`) and every call site passes
   `root`, so the *process* cwd never reaches git and a relative `.pinakes` resolves against `root`
   anyway. Measured from a subdirectory: relative, absolute and `:(literal)`+absolute all return the
   same three rows; only running git itself with `cwd=<subdir>` — which this code never does —
   reproduces the empty result. **With the pathspec mutated to the relative form, 68 of 69 tests in
   `test_init.py` still pass**, so the "run it from a subdirectory" test this plan asked for would
   have been green against the exact form it existed to forbid. **The assertion belongs on the
   pathspec itself** — `:(literal)` prefix, absolute, ending in `.pinakes` — which *is* killed by
   the relative form. Keep the absolute+literal form for the reasons above; describe it as defence,
   never as coverage.

   **The correction is the same failure as the plan's own subject, one level up.** The property was
   real and the argument for it was sound; the *instrument* was never examined. A shell
   reproduction was promoted to a claim about a code path without checking that path's cwd. **A
   prescribed test is a claim about a failing test, and nobody had watched this one fail.**
2. **`rc=128` maps to `None`, not to `False`.** This mirrors `_all_probes_ignored`'s existing
   discipline: an exit code arriving with `fatal:` on stderr is a guess wearing an exit code.
   **⚠️ And it cannot be asserted through `init`**: the reported field is a `bool`, so `None` and
   `False` collapse into it and an implementation returning `False` outside a repository passes
   every end-to-end test. Assert it against the tracked-check function directly. Found by the same
   mutation pass, 20260825.
3. **Read git's status bare.** The first sweep of this table reported the outside-a-repo case as
   `rc=0` because it read the status through `... 2>&1 | head -3` — the pipe's status, not git's.
   **This is the repository's own recorded hazard, met again within the hour by someone who had read
   the entry.** Knowing it is not what avoids it; running the command bare is.

**That the *fix* for X1 fails in X1's own direction is the finding, not a footnote.** A check that
answers *clean* when it was asked the wrong question is precisely what 0.30.2 existed to remove.

### ⚠️ And it must not go where the surrounding code invites it

**Found on review, before this plan landed — the third instance of X1's own shape in one evening.**
`init.py`'s `if gitignore in adopted:` (line 392 as of `35cdc79`) gates the existing *ignore* warning,
and `adopted` receives `.gitignore` **only when it already existed**. When `init` writes a
fresh one, every check in that block is skipped — `tests/test_init.py`'s
`test_a_gitignore_written_by_init_is_not_re_examined` (line 379 as of `35cdc79`) pins exactly that.

**Cross that with the state table and the natural placement is silent in the state it exists for.**
A KB whose `.pinakes/` is already tracked and has no ignore rule is, most commonly, a repository
with **no `.gitignore` at all**. `init` writes one, so `gitignore in adopted` is `False` and the
block never runs. *(Precisely: after `init` writes it the repository is ignored-going-forward and
still tracked — state row two, remedy `git rm -r --cached` then commit. The label changes; the
silence does not.)*

**So the `git ls-files` question goes OUTSIDE that block.** It is not a question about the
`.gitignore`'s provenance. **It is a question about the index, and the index does not care who wrote
the ignore file.** Ask it whenever `init` is inside a repository at all.

**The test that catches this is not the obvious one.** It needs a repository that tracks `.pinakes/`
**and has no `.gitignore`**, then asserts `init` still reports tracked. Every existing gitignore test
in `tests/test_init.py` was shaped around an *adopted* file,
so the natural test to write passes while the defect ships. **A test written in the shape of the
existing tests inherits their blind spot.**

**⚠️ RESOLVED — that comment is gone.** X1 rewrote it; the sentence below is quoted from the version
that existed before `35cdc79` and no longer appears in the tree. It narrowed the check's scope and
justified it partly with *"what widening it did reach was a path already in the index, where
`check-ignore` reports not-ignored"*. It identified the right phenomenon and drew the wrong
conclusion: **a path already in the index is not a reason to narrow the check — it is a second
question that was never asked.** Rewriting that comment is part of the increment and belongs to the
implementer; it is `src/`.

### The remedy, and its order is load-bearing

Report tracked-ness as its own state, never folded into the ignore verdict. The remedy cannot reuse
the existing wording:

| State | Remedy |
|---|---|
| not ignored, not tracked | add `.pinakes/` to `.gitignore` |
| ignored **and** tracked | `git rm -r --cached .pinakes`, **then commit** — the ignore line alone changes nothing |
| **not ignored *and* tracked** | ⚠️ **add the ignore line FIRST, then `git rm -r --cached .pinakes`, then commit** |
| ignored, not tracked | nothing |

**The third row's order is not stylistic.** Measured: in a repository with no ignore line, running
`git rm -r --cached .pinakes` and then any ordinary `git add -A` **puts the file straight back in
the index**. The reverse order looks like it worked and silently reverts on the user's next `add`.
**A remedy whose steps are correct but whose order is not is a remedy that fails quietly**, which is
this plan's subject twice over.

**Verified about `git rm -r --cached`, by running it**: the files remain on disk and byte-readable
(`find` before equals after; the transcript still `cat`s). So *"removes it from git's index, not
from your disk"* is an observation. **Nothing has been verified about already-pushed history and
the printed text must not imply it unpublishes anything.**

**This satisfies a rule the repository already set and, before X1, broke.** `init.py`'s
`remedy_already_present` docstring (line 296 as of `35cdc79`) states it:
*"the printed remedy must never instruct an action that would not change the verdict."* Today, for a
tracked-and-unignored KB, *"add this line"* **does** flip the verdict to protected — and changes
nothing about the exposure. The rule was written against a narrower case (`remedy_already_present`)
and X1 is the same rule one layer deeper.

**⚠️ `git rm -r --cached` is a destructive-shaped instruction printed to a user.** It removes from
the index, not from disk, and it rewrites nothing already pushed. Whatever is decided below, the
printed text must say both of those things, and must not imply it retroactively unpublishes
anything. **Content is the planner's; wording ships with the increment.**

## D-31 — Does `pnk doctor` carry a recurring `.pinakes/` check?

**Reserved by the previous planner. M2 changes the argument on both sides, so it is restated whole.**

| | **A. `init` only (status quo)** | **B. `doctor` carries it** |
|---|---|---|
| **Pros** | Nothing new can nag. Fires when the user is already thinking about setup. Zero cost on every other run. | Catches the **only case that actually loses data** — a KB that became exposed *after* creation (M1). `doctor` is where a user already goes to ask "is this KB healthy". Catches the tracked case, which `init` structurally cannot see because `init` refuses to run on an existing KB. |
| **Cons** | **Cannot ever see X1.** `init` runs once, before any of `.pinakes/` exists; the exposure in M1 is created later, by the user's own `git add -A`. Status quo means the measured hazard is never reported to anyone. | A permanent WARN is a real cost — the heading-coverage item in the open-corrections file records what an un-actionable one buys. Inherits `GIT_TIMEOUT_SECONDS = 5` and a subprocess on every `doctor` run. Needs a defined answer when git does not respond. |
| **Cost if wrong** | The user's verbatim questions are in a repository they may push. **Unbounded and unrecoverable — a push cannot be taken back.** | Noise. Recoverable by changing a severity. |

**The previous framing was "a correct detector is a better candidate for firing every run than a
broken one", and that is true but no longer the deciding fact.** The deciding fact is M2: the
recurring check is not a *strengthening* of the `init` warning, it is **the only place the tracked
case can be detected at all.**

> ### ✅ Recommendation: **B — `doctor` carries it**, and the check is X1's *two* questions, not one.
> The asymmetry decides it. Option A's failure mode is silent, permanent and unrecoverable; option
> B's is an annoying line. **A check that only ever runs before the hazard can exist is not a check.**

## D-32 — WARN, or OK-with-a-note?

**The original fork assumed one verdict. X1 splits it, and that dissolves most of the disagreement.**

| Verdict | Proposed status | Why |
|---|---|---|
| `.pinakes/` **tracked** | **`WARN`** | Actionable, specific, and terminates: the user runs `git rm -r --cached .pinakes`, commits, and it never fires again. This is not the un-actionable permanent WARN the file warns about. |
| **not ignored**, not tracked | **`WARN`** | Same as `init` reports today. Actionable and terminating. |
| ignored, not tracked | **`OK`** | Ordinary healthy state. One `OK` row, no note. |
| **git did not answer** (timeout / no git) | **`OK` with the note "not checked"** | ⚠️ **Never `WARN`.** A machine without git, or a slow one, is not an exposed KB. A `WARN` a user cannot act on and cannot clear is the exact cost the heading-coverage row measured. |

> ### ✅ Recommendation: **WARN only where there is an action that clears it; `OK`-with-a-note when the answer is unknown.**
> The rule generalises beyond this check and is worth stating as one: **severity tracks
> actionability, not alarm.** Every WARN above terminates on a command the row itself prints.

**This repository has already paid for the other answer, and the receipt is in the same file.** The
`## Closed` table records the heading-coverage check, which *"WARNed forever on `code` and `pdf`,
which can never carry a heading path — so a KB holding one `.py` file warned on every run with a
remedy amounting to a limit of the format"*. It had to be withdrawn. **That is the precedent, and it
is not an argument against a recurring check — it is an argument against a WARN nothing can clear.**
The four rows above are built so that every WARN has a command that ends it, and the one state with
no such command (git did not answer) is deliberately not a WARN.

## D-33 — "ignored *here*", or "ignored *for everyone*"?

The previous planner settled the `init` case — semantics stay **"is it ignored here"**, so
`.git/info/exclude` and `core.excludesFile` count as protection, because reporting otherwise would
make `init` lie about the machine in front of the user. **That decision stands and is not reopened.**

**What is genuinely open is whether `doctor` should say the same thing.** A KB protected only by
`.git/info/exclude` is protected on this machine and exposed for every collaborator who clones it —
and `.git/info/exclude` is never committed. RESUME.md is itself an instance: excluded that way, and
therefore invisible to every other checkout.

| | **A. Same semantics as `init`** | **B. `doctor` distinguishes them** |
|---|---|---|
| **Pros** | One definition of "protected". Nothing to explain. | Names a real and currently invisible exposure: protected-for-me, exposed-for-the-team. |
| **Cons** | A shared repository can be exposed for everyone while every local `doctor` says OK. | A second concept in the output. Requires deciding what `core.excludesFile` means for a solo user, where the distinction is noise. |

> ### ✅ Recommendation: **A for the verdict, B for the detail line.** One notion of protected —
> but when protection comes *only* from an uncommitted source, the `OK` row says so
> (`ok — ignored via .git/info/exclude (local to this checkout)`). No new severity, no new verdict,
> and the fact stops being invisible. **If this is judged scope creep, cut it and keep A; D-31 and
> D-32 do not depend on it.**

---

# Part 2 — The same skeleton, in documents: a status claim nothing gates

**These are here rather than in their own plan because they are one failure, not three.** Every item
in Part 2 is a *true sentence over a population nobody stated*, and each has now cost real work.

## X2 — The open-corrections file has produced the same collision twice in two days

**M6 is the mechanism.** A `###` item's closure lives in its body; `## Closed` is sixty lines below;
`grep '^## '` returns *Live* and stops.

**It fired again during the writing of this plan.** A coder session — freshly cleared, acting
correctly — read the `tools/fragments.py` item as live and specified, and offered to build it. Both
of its checks had shipped on 20260824. **It is on record as having cost a near-rebuild once before,
which makes today the second.** Nothing was rebuilt either time, and both times the save was a peer
message, not a gate.

**The repository already contains the convention to conform to**: `T6`/`T8` in
[`20260804_1016-template-release.md`](20260804_1016-template-release.md) carry
`· **CLOSED <date>, <disposition>**` **in the `###` heading itself**. So this is conformance, not
redesign.

**Two things make it more than a move**, both recorded by the previous planner and both confirmed:

1. The E5 item is **partial, not closed** — *"Left open deliberately: widening the body rule"*,
   *"Neither is taken."* Filing it under *"Closed — recorded so nobody reopens them"* would put an
   undecided design question under a heading promising the opposite.
2. The header's bolded **"None live."** is contradicted by its own `## Live` section 27 lines later,
   and its rule *"if an item reads as a question, that is a defect in this file"* is violated by E5,
   which is a question. **The precedent for relocating a question out of this file is
   [`20260811_0720-decisions-gates-and-corrections.md`](20260811_0720-decisions-gates-and-corrections.md)
   — which is what this file does for E5.**

**Proposed repair, in one increment**: closure disposition into every `###` heading; `## Live`
holding only genuinely live items; the header's *"None live"* rewritten to whatever is then true;
E5's remaining decisions pointing here.

## X3 — The sweep that justifies the `plans/` repair read 11 of 20 files

**The classifier read each `##` section's *heading* and sent only LIVE/MIXED headings for a real
read. Nine files were dropped unread**, at least one wrongly:
`20260804_1844-decision-parent-child-arity.md`'s `## The decision`, which holds that file's only
outstanding work.

**Do not close this with a second vocabulary pass — that is how the hole was made.** A heading is a
status *claim*; X2 is the proof that the claim can be false. **Sections get classified by being
read.** Nine files, read.

Two findings from that sweep were **withdrawn after checking** (Decision 19 / ruamel, and D-18), and
the most strongly worded one was the wrong one. **Check a row before acting on it.**

## X4 — `docs/VERIFICATION.md`'s scope is undecided, and its scope paragraph is stale

**I produced this section's own defect while writing this plan**, which is why it is stated plainly.
I told a coder that 36 unrowed `test_fragments.py` tests were a gap it should fill. It counted the
population instead and declined: **917 tests have no row (M5), and the document says that is its
design** — it maps *promises to tests*, and names `test_chunk.py`, `test_ids.py`, `test_lock.py`,
`test_pairing.py`, `test_uri.py`, `test_embed.py` as predating the table. A gap of 917 cannot all be
holes. **A sound argument over an unexamined domain, made by the planner, hours after the lesson.**

**The decision (D-34, deferred to a later pass rather than taken here):** does the table map *every
test*, or *promises only*? It changes what a 917-row gap means and whether it is work at all.

**Independent of that decision, one thing is simply wrong and should be fixed either way.** Line 27:
*"It stopped there: 0.13.0 through 0.16.0 added no rows. The gap is now four releases wide."* The
document today carries rows for `test_cli_upgrade.py` and the `test_deep_*` modules, all post-0.16.
**The paragraph telling a reader where the table stops describes a tree that no longer exists — and
it is the first thing anyone deciding D-34 would read.**

## X5 — Three conventions this repository has re-derived and never written down

| # | The convention | Where it belongs | Evidence it is needed |
|---|---|---|---|
| **X5a** | **Content-mine, keystrokes-yours.** When a planner-owned document must change *atomically* with an implementer's code, any split ordering leaves `main` red or wrong at some commit. The planner decides the content and says so; the implementer pastes it into their branch. | `CLAUDE.md`, beside the ownership table | **Re-derived four times in one session.** Two such edits were authorised into a coder's branch on 20260825 — a `docs/VERIFICATION.md` section and a `tools/batteries/README.md` paragraph — and a future reader has no way to learn why an implementer wrote them |
| **X5b** | **A fragment written after a release commit but before its tag.** `tools/fragments.py --apply` splices after `## [Unreleased]` and has **no notion of an untagged version section**. Answer taken 20260825: the implementer still writes the fragment; the planner splices, moves the entry into the untagged section, and deletes the consumed file in its own commit. Retrospective fragments need no move — `docs/RETROSPECTIVES.md` is chronological. | `docs/RELEASING.md` | The 40-minute untagged window on 0.30.2 is now a *recommended* practice, so this recurs by design |
| **X5c** | **`README.md` in the ownership table is ambiguous.** It sits among root-level paths, so a coder read `tools/batteries/README.md` as covered by the `tools/` row and edited it. The table's own opening sentence — *"the planner owns every document"* — settles it the other way. Say **`README.md` (repository root)** and add **"any `README.md`"** to the planner row. | `CLAUDE.md` | A document generated a collision rather than recording one, twice in one day |

## X7 — NEW: a hold makes some claims false and leaves others true, and the sweep does not know which

**Found 20260825 08:42, in this repository's own published documentation, by a peer.** The 0.30.3
release commit landed with the tag deliberately held. The release sweep stamped `docs/STATUS.md`
line 3 as **"Latest release: 0.30.3"** and ticked its surface row **✅**, while PyPI's
`info.version` was **0.30.2** and no `v0.30.3` tag existed anywhere.

**`docs/` deploys on every push to `main`, so this was live**: lucagattoni.github.io/pinakes told
the public that 0.30.3 was the latest release. **The only finding of the day that reached anyone
outside the repository.**

**It contradicted the file's own rule, printed five lines below the claim**: *"Shipped below means
**released**; an increment merged to `main` but not yet in a release says so explicitly. Installing
from a tag and installing from `main` are different answers to 'can I use this yet', and this file
is where that difference has to be visible."*

**The hold was right. The sweep was the problem.** *Published on PyPI* and *Published versions* were
correctly held at 0.30.2 — deliberately, because they are facts about the index. Line 3 and the
row's ✅ are **two further release claims in the same file** that got stamped anyway. **A hold
partitions a document's claims into ones it falsifies and ones it does not, and nothing in the
sweep knows the partition.**

**Why no gate could see it.** `tools/release_order_gate.py` reads *sequences* — it is satisfied by
0.30.3 being present and in order, which it was. `mkdocs build --strict` resolves links. **Neither
can compare a sentence to PyPI.** Only asking the index can. `0.27.1` and `0.28.3` are two prior
instances of this same file drifting exactly where no gate reached.

**⚠️ A gate for line 3 already exists, and it enforces the opposite.**
`tools/status_header_gate.py` requires line 3 to name **`__version__`** — so during a hold it
requires the line to say `0.30.3`, the very claim PyPI contradicts. Its docstring states the
premise: *"The invariant holds with **no exception window**. On `main`, `__version__` is the latest
release… this gate never goes red on a correct tree, and a red run means the tree is wrong, not the
gate."* **The hold is that exception window, and this repository has now created one deliberately
twice in a day.** The gate is not wrong about drift; it is reasoning over a release practice that
changed after it was written — **which is this plan's subject, occurring inside the gate built to
prevent it.**

**Resolved for now without pre-empting D-35 below**: the gate leaves everything after the closing
`**` unconstrained, so line 3 names `0.30.3` *and* says plainly that it is untagged, not on PyPI,
and that `pip install pinakes` still gets `0.30.2`. Gate green, and its negative check still fails
as it should. The public page stops being false.

**Proposed (a task, once D-35 is answered).** A check that queries
`https://pypi.org/simple/pinakes/` — the endpoint the rest of this repository already prefers, since
the `json` one lags an upload by minutes — and reconciles it with what `docs/STATUS.md` claims.
**Three requirements, each from a failure already on record:**

1. **It must not require the network to pass.** A gate that fails offline is a gate people learn to
   skip. No answer from the index is *unknown*, never *wrong* — the same discipline `_tracked_by_git`
   needed for `rc=128`.
2. **It must fail on the claim, not on the version.** *Latest release* naming an unpublished version
   is the defect; `CHANGELOG.md` carrying that version's entry is correct and must stay green, or
   the gate blocks every held release — which is the practice this repository has now used twice to
   its benefit.
3. **Its own test must watch it fail.** Point it at a STATUS naming a version the index does not
   have, and see red. Per X1's constraint #1: a prescribed test is a claim about a *failing* test.

**Owner: the implementer** — it is `tools/`. The coder offered to build it and the offer is
accepted, once someone takes it off this list.

## X6 — The handoff is invisible to everything except this machine

`RESUME.md` is excluded via `.git/info/exclude:18` — a file that is itself never committed. A cloud
run, a scheduled routine, another checkout or a fresh worktree sees **no handoff at all**, and
cannot discover that one exists. `CLAUDE.md` and `docs/README.md` both route the next agent and
neither points at it.

**This is D-33's own distinction, applied to the repository's own state**, which is what makes it
worth an item: protection-for-me versus visibility-for-everyone, and nobody noticed the asymmetry
until it was written into a plan about `.gitignore`.

**Not proposing that `RESUME.md` be committed** — a scratch file with a rewritten-hourly body is a
merge hotspot, and the ownership table would make it planner-only, which is wrong for a file both
roles write. **Proposed instead:** the durable half already belongs in planner-owned documents that
*are* committed (`docs/STATUS.md`, this directory), and the rule to write down is that
**`RESUME.md` may only ever hold what is also recoverable from `main` — which is what it already
claims about itself and what nothing enforces.**

---

## D-35 — NEW DECISION: does `__version__` mean *released*, or *landed*?

**The hold forced a contradiction between two rules this repository already holds, and it cannot
keep both.**

| Rule | Where | Says |
|---|---|---|
| `__version__` **is** the latest release, with no exception window | `tools/status_header_gate.py` | line 3 must name `__version__` |
| *"Shipped means **released**; an increment merged to `main` but not yet in a release says so explicitly"* | `docs/STATUS.md`'s own preamble | line 3 must not claim an unreleased version |
| Landing and publishing are separate steps, and the gap is valuable | `docs/RELEASING.md`, and 0.30.2's forty minutes | the gap will keep happening |

| | **A. `__version__` means *landed*** | **B. `__version__` means *released*** |
|---|---|---|
| **What changes** | Nothing mechanical. The header carries an explicit unreleased qualifier during a hold, as it does now | The version bump moves out of the release commit and into the tag step, or the gate learns a *released-version* source of truth separate from `__version__` |
| **Pros** | Zero churn; the gate keeps working; `make release-check` keeps reading `__version__` | Line 3 is true on its own, with no qualifier to read; the preamble's rule holds literally |
| **Cons** | Line 3's first six words are false during a hold, and a reader who stops there is misled — **which is exactly what happened, publicly, on 20260825** | Touches the release procedure and the gate; a bump outside the release commit is a new step to forget, and forgetting it is silent |

> ### ✅ Recommendation: **A, plus the index check from X7.** The qualifier is what makes the line
> honest, and a gate that reads PyPI is what makes the qualifier *enforced* rather than remembered.
> **B moves a bump into a step that is taken hours later by a human, which is how the 0.5.0–0.7.1
> drift happened in the first place.** But A is only safe with X7 built — otherwise the qualifier
> depends on whoever cuts the release remembering that a hold falsifies it, and that is precisely
> the memory that failed today.

## Build order

**Nothing in Part 1 is buildable until D-31 and D-32 are answered.** X1 is the exception and is
listed first because it needs no decision.

| # | Item | Blocked on | Owner |
|---|---|---|---|
| 1 | **X1** — the tracked-KB question, its own state and its own remedy, in `init` | nothing | coder |
| 2 | **X2** — the open-corrections restructure | X3 (read the nine files first) | planner |
| 3 | **X3** — read the nine unread `plans/` files | nothing | either |
| 4 | **X4** (stale paragraph only) — fix line 27 | nothing | planner |
| 5 | **D-31/D-32** → `doctor` check | the decisions | coder |
| 6 | **D-33** detail line | D-31 | coder |
| 7 | **X5a/b/c**, **X6** — write the four conventions down | nothing | planner |
| 8 | **D-34** — VERIFICATION.md scope | a decision, not scheduled | planner |

**A note on 1 versus 5.** X1 in `init` is worth building even if D-31 comes back **A**, because
`init` can still meet a tracked `.pinakes/` — a KB created outside git, then `git init` and
`git add -A` in the parent, then a second `pnk init` in a sibling directory. It is a smaller case
than `doctor`'s and it is not zero.

**The corpus rule does not apply to any of this.** Nothing here touches chunking, fusion, reranking
or the confidence signal, so no golden-set eval is owed.
