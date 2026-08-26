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

1. The item is **partial, not closed** — *"Left open deliberately: widening the body rule"*,
   *"Neither is taken."* **(Two corrections, 20260825 18:41. First, this is a mis-attribution: that
   quoted text lives in the `tools/fragments.py` item, not in the gitignore item, which is the one
   E5 raised — the same numbered list uses "E5" correctly four lines later. Second, "Neither is
   taken" is now out of date: the widening is DEFERRED behind a written trigger, with the cheap
   implementation named as the setext-plus-indentation pair.)* Filing it under *"Closed — recorded so nobody reopens them"* would put an
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

**The decision (D-34) — ✅ TAKEN BY THE USER 20260825 18:16: PROMISES ONLY, ratified, plus one
bounded audit of the residue.** Promises only ratifies the reading `db7d1c1` had already operated on
since 20260804 and which had never reached `docs/VERIFICATION.md`'s preamble — which is why every
fresh reader who counted the tree re-derived the question. **A promise is a user-visible guarantee, a
named invariant, or a gate's own correctness** — not a unit test of an internal primitive, and not a
per-surface re-assertion of a promise already rowed. The preamble now says so.

**The audit was run rather than deferred, and it found the closing claim was not safe to publish.**
*"The unrowed population is not debt"* fails at more than n=1: `tests/test_serve.py` carried **14 of
its 31 tests unrowed**, including the MCP path-refusal boundary (`../../etc/passwd`) and the
labelling of retrieved text as evidence rather than instruction — **two security boundaries**. The
cause was structural, not neglect: the server's rows lived under *the links release* and *page
citations*, and **no section owned the boundary itself**. One does now — *The MCP server boundary
(I13)* — all 14 are rowed, and the module has none left.

**What D-34 deliberately did not buy is the direction.** The gate walks from the document to the
tests, so it proves no row is fiction and **cannot** prove no guarantee is unrowed. That
one-directionality is *"not a defect in the gate, it is the shape of the problem, so the answer is
procedural"*.

**Re-open trigger:** a second promise-bearing module found substantially unrowed, or any shipped
guarantee reaching users with no row. Neither would make *every test* correct — each makes the
bounded audit due again.

**Independent of that decision, one thing is simply wrong and should be fixed either way.** Line 27:
*"It stopped there: 0.13.0 through 0.16.0 added no rows. The gap is now four releases wide."* The
document today carries rows for `test_cli_upgrade.py` and the `test_deep_*` modules, all post-0.16.
**The paragraph telling a reader where the table stops describes a tree that no longer exists — and
it is the first thing anyone deciding D-34 would read.**

## X5 — Three conventions this repository has re-derived and never written down

| # | The convention | Where it belongs | Evidence it is needed |
|---|---|---|---|
| **X5a** ✅ **BUILT 20260825 13:00** | **Content-mine, keystrokes-yours.** When a planner-owned document must change *atomically* with an implementer's code, any split ordering leaves `main` red or wrong at some commit. The planner decides the content and says so; the implementer pastes it into their branch. | `CLAUDE.md`, beside the ownership table | **Re-derived four times in one session.** Two such edits were authorised into a coder's branch on 20260825 — a `docs/VERIFICATION.md` section and a `tools/batteries/README.md` paragraph — and a future reader has no way to learn why an implementer wrote them |
| **X5b** ✅ **BUILT 20260825 12:52** | **A fragment written after a release commit but before its tag.** `tools/fragments.py --apply` splices after `## [Unreleased]` and has **no notion of an untagged version section**. Answer taken 20260825: the implementer still writes the fragment; the planner splices, moves the entry into the untagged section, and deletes the consumed file in its own commit. Retrospective fragments need no move — `docs/RETROSPECTIVES.md` is chronological. | `docs/RELEASING.md` | The 40-minute untagged window on 0.30.2 is now a *recommended* practice, so this recurs by design |
| **X5c** ✅ **BUILT 20260825 13:00** | **`README.md` in the ownership table is ambiguous.** It sits among root-level paths, so a coder read `tools/batteries/README.md` as covered by the `tools/` row and edited it. The table's own opening sentence — *"the planner owns every document"* — settles it the other way. Say **`README.md` (repository root)** and add **"any `README.md`"** to the planner row. | `CLAUDE.md` | A document generated a collision rather than recording one, twice in one day |

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

**DECIDED 20260825 12:37 (D-35). Owner: the implementer.** Three layers, not one. Layers 1-2 are
offline and are the load-bearing ones; the index query is layer 3 and is additive.

1. **Layer 1, unchanged.** `line3 == pinakes.__version__` — the only *machine-derived* comparison here:
   Hatch reads that constant to build the wheel (`pyproject.toml:74-76`), it is bumped in the same
   commit, and both facts are inside the checkout. This is why `check.sh:160` can run it unconditionally
   in a script whose own comment (57-62) demands it stay offline-capable.
2. **Layer 2, NEW, offline, hard.** With `R` = the tail of `docs/STATUS.md`'s *Published versions* row,
   read by importing `SEQUENCES` from `tools/release_order_gate.py` rather than duplicating its `within`
   anchor: `line3 > R` → the hold marker is **required**; `line3 == R` → the marker is **forbidden**;
   `line3 < R` → always red; **the row unreadable → hard fail, never skip.** This makes the marker a
   *parsed shape* rather than free text after the closing `**`, and it catches both recorded incidents
   at the release commit *and* a stale marker at the verification commit — using a committed file that
   is present in every shallow CI checkout.
3. **Layer 3 — the index query, its own CI job, soft.** `https://pypi.org/simple/pinakes/`, the endpoint
   the rest of this repository already prefers since the `json` one lags an upload by minutes. **No
   answer is *unknown*, never *wrong*.** It is the only layer that can catch a *premature* row write.

**The three requirements below are unchanged and still bind**, and layers 1-2 satisfy 1 by construction
rather than by careful coding.

**The source sub-choice is settled: the index, never `git tag --list`, and they do not layer.** Two
independent reasons, both already in this repository's record. **A tag is not evidence of publication**:
`docs/RETROSPECTIVES.md:3291` — `v0.9.0` *"tagged, built, smoke-tested, and was refused at the upload:
invalid-publisher"* — and `git tag -l 'v0.9*'` still returns it; `release.yml`'s own header comment makes
this a *supported* mode, since everything before the `PUBLISH_TO_PYPI` gate runs on every tag, *"so a tag
is fully validated even when nothing is uploaded"*. **And tags are unreadable where the gate runs**:
`release_order_gate.py:77-80` already took this decision in writing — every CI checkout here is shallow,
no workflow sets `fetch-tags`, and `ci.yml:347`'s lone `fetch-depth: 0` belongs to the template-drift
job. A tag-based check would report every version as unreleased. Publishing is tag-triggered only, so a
tag is *sound evidence of absence* and unsound evidence of presence — and even the sound direction is
unavailable in CI. **Use the index for layer 3, the row for layer 2, and tags for nothing.**

**Not blocked on anything, and owed regardless of what was decided:** `status_header_gate.py`'s docstring
lines 1 and 10-13 are **already literally false on today's tree** — *"The invariant holds with no
exception window."* There is an exception window, it has been used deliberately three times, and this
plan is the record of it.

**Two couplings that move together or not at all.** The failure string at `status_header_gate.py:88` is
grepped verbatim by `ci.yml:292` and that grep is itself pinned as a command by
`tests/test_check_script.py`; rewording the message without changing `ci.yml` leaves the negative check
asserting only a non-zero exit, which that job's own comment (`ci.yml:285-288`) says is insufficient.
And `check.sh:160`'s invocation must stay byte-identical for the regex pin at
`tests/test_check_script.py:159`.

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

## D-35 — ANSWERED 20260825 12:37: `__version__` means *landed*, and line 3 gets an offline relation

**Taken by the user 20260825 12:37.** `__version__` means **landed on `main`**. Line 3 keeps naming it,
and a **new offline relation** enforces the hold marker in *both* directions. `X7` is built on top as a
third, network layer.

| Layer | Reads | Rule | Where |
|---|---|---|---|
| **1** — unchanged | `pinakes.__version__` | line 3's version must equal it | `status_header_gate.py`, offline |
| **2** — NEW | `R` = the *Published versions* row's tail | `line3 > R` → marker **required**; `line3 == R` → marker **forbidden**; `line3 < R` → always red; row unreadable → **hard fail, never skip** | `status_header_gate.py`, offline |
| **3** — X7 | `https://pypi.org/simple/pinakes/` | reconcile, degrading to *unknown* | its own CI job, network |

**The recommendation this section previously carried — "A, plus the index check from X7" — did not
survive, and the reason is specific.** Its semantics and its anchor were right. Its *enforcement half
cannot be built inside X7's own constraints*: requirement 2 forces X7's rule to be *unqualified +
absent from the index → red; qualified → green*, so **a stale marker after a successful publish is
green by construction, forever** — and green in `status_header_gate.py` too, whose `SHAPE` has no `$`,
and in `release_order_gate.py`, none of whose seven `Sequence` patterns reads line 3's tail. **X7 can
enforce writing the marker. It can never enforce removing it.**

### What was measured, not argued

**The marker is 0-for-2, and the first failure was never recorded.**
`git show f3c6864:docs/STATUS.md | sed -n '3p'` returns
`**Latest release: 0.30.2** · last reviewed 20260825 00:45` — **unqualified** — for the 14 minutes
between 0.30.2's release commit (01:49:42) and its tag (02:03:33), with PyPI at 0.30.1 and `docs/`
deploying on every push. **20260825 08:27 was the second occurrence, not the first.** And
`grep -in 'hold|untagged|not yet tagged|qualifier|⏸' docs/RELEASING.md` returns one unrelated hit at
line 181: **the procedure never asks for the marker at all.** A release cut by following it verbatim
produces the false line.

**Removing the marker lands in a slot that has never done this job.** `git log -L 3,3:docs/STATUS.md`,
then diffing each non-release commit that touches line 3 (`733374e`, `9096350`, `d3546f6`, `06c2acb`,
`78c7dd3`, `fb601a3`): **every one left the version byte-identical** and changed only `last reviewed`.
Plain A therefore invents a new obligation on a commit type that has never carried one — *which is the
identical property this plan gave as its reason for rejecting B.*

**Two options were falsified by execution. Preserve the experiment so nobody re-litigates it.**
Copy `CHANGELOG.md` and `docs/` to a scratch root, append `0.30.3` to the *Published versions* row's
leading bold span, insert a matching `**0.30.3, verified…:**` prose entry, then
`uv run python tools/release_order_gate.py <scratch-root>`. **Exit 0**, reporting `newest 0.30.3` on
both index sequences, with nothing on PyPI. Separately, changing one comma to an em dash in the newest
prose entry drops that sequence 32 → 31 and its max 0.30.2 → 0.30.1, **exit 0** — declared as an
accepted cost in that module's own docstring.

**So the *Published versions* row is a hand-typed sentence with a documented silent-drop failure mode.
It may corroborate the headline. It must never be its source.** That is what rejects the two options
that made it one: an error in it would reach the public headline *with gate certification*, and the
failure message would name line 3 rather than the row that caused it.

**The record on B is corrected even though B loses.** This plan's con — *"a bump outside the release
commit is a new step to forget, and forgetting it is silent"* — is **factually wrong**.
`.github/workflows/release.yml:34-42` refuses a mismatched tag unconditionally, as the first step after
checkout, ahead of `uv build` (`:44`) and ahead of the `PUBLISH_TO_PYPI`-gated `uv publish` (`:96`).
B loses on its real costs instead: `manifest.py:437` would print `(this build is 0.30.2)` while running
0.30.3's code, and B's bump commit touches `docs/STATUS.md`, so `docs.yml` publishes the new headline
*before any tag-triggered gate runs at all*.

### Residuals, stated rather than discovered later

* **Layer 2 is not immune.** A maintainer who writes the row prematurely **and** strips the marker is
  green with a false headline. Only layer 3 closes that. Under layer 2 the premature row *alone*
  produces a red the maintainer must resolve, which is the whole gain.
* **Layer 3 must not be hard-fail until measured.** `docs/STATUS.md:662ff` records 0.16.0, 0.17.0 and
  0.18.0 each reading *unsatisfiable* for 25-30 s after genuinely successful uploads. A gate red on a
  correct tree is one people learn to skip.
* **The marker's shape is undecided and is the implementer's to choose** — the `⏸` now on `main`, or a
  bracketed keyword. **Today the qualified form passes only by accident**: `SHAPE` has no `$`, a
  looseness its docstring says exists for the `last reviewed` date, and *nothing pins that the
  qualified form is legal*. Anyone tightening that regex would silently outlaw it. The build adds a
  test asserting it is legal.
* **No mutation battery exists for `status_header_gate.py`** — six batteries, none for this target — so
  a new file is correct here, and it forces the counted-paragraph edit in `tools/batteries/README.md`
  that `tests/test_batteries.py` asserts.
* **Layer 2 reads `SEQUENCES` from `release_order_gate.py`** rather than duplicating its `within`
  anchor (precedent: `tools/two_leg_gate.py:60`). If that coupling is judged wrong at build time, the
  alternative is two copies of one fact, which this repository has been burned by — come back to the
  planner rather than duplicating.

### The question this did **not** settle

**What line 3 answers** — *"what is the state of this repository"* or *"what can I install right now"* —
was offered and **not** taken. `docs/STATUS.md:9-11` (*"'Shipped' below means **released**"*) is what
makes line 3 false during a hold; changing that sentence would have dissolved the contradiction toward
plain A at near-zero cost. It stands as written, which is what makes layer 2 worth building.

## Build order

**D-31 and D-32 were ANSWERED 20260825 18:16, so Part 1 is buildable** — `pnk doctor` asks both
questions, tracked *and* ignored, **unconditionally** (option C, and **not** the `ls-files`-first
shortcut an earlier pass proposed). X1 was always the exception and is listed first because it needed
no decision. **D-35 was answered 20260825 12:37, so X7 is unblocked** —
read its section above for the decided three-layer shape, which is *not* what this plan first proposed.

| # | Item | Blocked on | Owner |
|---|---|---|---|
| 1 | **X1** — the tracked-KB question, its own state and its own remedy, in `init` | nothing | coder |
| 2 | ~~**X2** — the open-corrections restructure~~ — **BUILT 20260825 13:20.** X3's 53 dispositions, expanded to **100 heading edits across 17 files**, each re-read and then checked by two adversaries. **20 named the wrong file and 5 `old_line` strings are not unique across `plans/`** — a repo-wide replace would have corrupted two of them — so the apply keys on (file, line). **7 dispositions were overturned for writing a false claim.** Residual in [`20260825_1252-plans-sweep-findings.md`](20260825_1252-plans-sweep-findings.md) | — | planner |
| 3 | ~~**X3** — read the nine unread `plans/` files~~ — **BUILT 20260825 12:52.** All **twenty** read, not nine: the dropped nine could not be identified after the fact. **317 sections classified by body, 93 heading/body mismatches.** Findings: [`20260825_1252-plans-sweep-findings.md`](20260825_1252-plans-sweep-findings.md) | — | planner |
| 4 | ~~**X4** (stale paragraph only)~~ — **BUILT 20260825 12:49.** Rewritten to the measured state; `test_init.py` moved out of the unrepresented list (27 rows), and the release-count claim removed rather than restated | — | planner |
| 5 | **D-31/D-32** → `doctor` check — **option C, both questions, unconditionally** | **nothing — answered 20260825 18:16** | coder |
| 6 | **D-33** detail line | **nothing — answered 20260825 18:16**; D-33's *deferred half* (what the line says when protection comes only from an **uncommitted** `.gitignore`) is its own item and is assigned to nobody | coder |
| 7 | ~~**X5a/b/c**, **X6**~~ — **ALL FOUR BUILT.** X5b 12:52 (`docs/RELEASING.md`); **X5a, X5c, X6 at 13:00** — the user chose the slim form for `CLAUDE.md` (a pointer, not the rule inline, since the file is 60% over its own size guideline), so `CLAUDE.md` gained 4 lines and `docs/BUILDING.md` carries the rules: § *Content mine, keystrokes yours* and the `RESUME.md` bound in § *Hand over before you stop* | — | planner |
| 8 | ~~**D-34** — VERIFICATION.md scope~~ — **ANSWERED 20260825 18:16 and BUILT.** Promises only, ratified; the bounded audit run, finding **14 unrowed promises in `tests/test_serve.py`** — two of them security boundaries — now rowed under a new *The MCP server boundary (I13)*; the scope sentence's *62 of the 67* corrected to *63 of 74* | — | planner |
| 9 | **X7** — line 3's three layers (D-35 **answered** 20260825 12:37) | **nothing — unblocked** | coder |
| 10 | **X7 doc half** — `docs/RELEASING.md` sweep row (the hold rule and the marker's shape), `docs/VERIFICATION.md:787` | X7's shape being chosen | planner |

**A note on 1 versus 5.** X1 in `init` is worth building even if D-31 comes back **A**, because
`init` can still meet a tracked `.pinakes/` — a KB created outside git, then `git init` and
`git add -A` in the parent, then a second `pnk init` in a sibling directory. It is a smaller case
than `doctor`'s and it is not zero.

**The corpus rule does not apply to any of this.** Nothing here touches chunking, fusion, reranking
or the confidence signal, so no golden-set eval is owed.
