# Pinakes — project instructions

Architecture and rationale live in [`docs/DESIGN.md`](docs/DESIGN.md); [`docs/README.md`](docs/README.md)
indexes the rest (which file owns which fact). This file only carries rules that change how you work.

## 🧭 A cleared context does not know its own role — settle that first

**Before any tool call that writes:**

1. **Name your role** — coder, planner, other — from what the **user** said in *this* session.
   Never infer it from the repo, from the previous session, or from the work in flight. **If you
   cannot determine it, ask, and do nothing until they answer.** This one blocks; *Working mode —
   autonomous by default* below does **not** override it.
2. **Ask every live peer theirs** — `ListAgents`, then `SendMessage` — and state your own role and
   file set in the same message. Wait before touching a shared path.
3. **Then act inside the ownership table** in *Documentation has one owner*, re-checking at the
   moment of landing rather than only at the start.

**Both directions fail silently, and both happened here on 20260823**: assuming *planner* collides
with an in-flight land; assuming *coder* leaves a document wrong out of deference. Set by the user
that day. Procedure and the failure record: [`docs/BUILDING.md` § Settle your role
first](docs/BUILDING.md#settle-your-role-before-anything-else).

## 🛑 Land with `tools/land.py` — never `git merge` by hand

    python3 tools/land.py <branch>                  # merge, verify, push
    python3 tools/land.py <branch> --cleanup        # ... and remove the worktree and both branches
    python3 tools/land.py <branch> --cleanup-only   # remove a branch that landed earlier

**`git merge <branch>` from inside that branch's own worktree merges it into itself.** *"Already up
to date"*, *"Everything up-to-date"*, and a tag pointing off-`main` — **three successful commands and
nothing landed.** It has happened repeatedly here, always one `&&` chain beginning `cd <worktree>`.
A branch merged into itself creates no commit, so `pre-merge-commit` never fires: **this is the only
rule here that fails silently, which is why it is the only one with an executable guard.** What
`land.py` refuses, and why `--cleanup` deletes both copies of a branch: [`docs/RELEASING.md` §
Landing a branch](docs/RELEASING.md#landing-a-branch).

## Working mode — autonomous by default

Set by the user 20260808 04:39. It **overrides the global default of stopping to check in.**

- **Run to completion.** Pick the next increment from `plans/`, build it, land it, write the
  fragments, pick the next. Stop when the user takes control back — not at increment boundaries.
- **Cutting the release is the planner's, and so is the handover** — both write documents the
  ownership table below makes planner-only, and that table wins. **An implementer's increment ends
  at the fragments**: it lands, it proposes what a planner-owned document needs, and it does not
  release. Complete work then waits for a planner rather than lingering by accident, which is the
  cost of one owner and is accepted.
- **A choice you can take, you take** — after weighing each option's real pros and cons in the open
  and saying which you chose and why. Needing an answer in order to proceed is the bar for asking;
  "the user might have preferred otherwise" is not.
- **Never assume what the plans have not decided.** An undecided question is a stop, not a guess.
  Choosing *how* to build what a plan specifies is yours; choosing *what* it should have specified
  is not.
- **Iterate: build → adversarially review → fix → re-review, until a pass finds nothing**, with a
  commit per pass. The default shape of an increment, not a debugging-only move.
- **At each increment boundary, judge whether the context should be cleared. If it should be:
  finish the handoff, say so, and stop there.** Strengthened by the user 20260811 15:37 from *offer
  and carry on* to *stop* — clearing is the user's command, so stopping is what makes the offer real.
- **Write the handover before you stop, in the same branch as the work** — context dies with the
  session, and an increment's own work is what falsifies the pointers to it. The five places, and
  how to verify them: [`docs/BUILDING.md` § Hand over before you
  stop](docs/BUILDING.md#hand-over-before-you-stop).

## This repository is PUBLIC

- **Never commit real knowledge-base content.** The repo is the engine. The only KBs here are the
  synthetic corpora under `tests/` (`demo-kb`, `partner-kb`) — written for the purpose, never
  harvested.
- **Every paid path's key is `PINAKES_ANTHROPIC_API_KEY`, never `ANTHROPIC_API_KEY`** — enforced in
  code, because the SDK reads its own variable out of whatever environment it is handed. **Never
  teach Pinakes to load `.env` itself, and never add an `ANTHROPIC_API_KEY` fallback**; both are the
  same defect one layer apart. Why it is enforced in code rather than by machine hygiene, and what
  actually bounds spend: [`docs/INVARIANTS.md` § The paid path's key is its
  own](docs/INVARIANTS.md#the-paid-paths-key-is-its-own).
- Vet every file for PII, credentials, private URLs, and anything copied from memory before staging.
- Never commit model weights or `.pinakes/` state (both are gitignored — keep it that way).

## Documentation has one owner

**The planner agent owns every document in this repo. No other agent edits one — it proposes.**
Decided by the user 20260801 01:24.

| | |
|---|---|
| **Planner-only** | `docs/**`, `plans/**`, **any `README.md`, at any depth** (root, `tools/batteries/`, `changelog.d/`, `retro.d/`), `CLAUDE.md`, `CHANGELOG.md` |
| **Yours to write** | `changelog.d/` and `retro.d/` fragments; docstrings and comments in `src/`, `tests/`, `tools/`. Fragments exist so an implementer records what it changed *without* touching a shared document — that is the mechanism, not an exception to it |
| **One narrow exception** | `docs/VERIFICATION.md`: add **only** the row a test you wrote requires. `tests/test_verification.py` hard-fails on an unresolvable name, so a renamed or new test with no row makes *your own* branch red. Nothing else in that file |

**Propose as `git diff <sha> -- <file>` against a named commit** — never an edit, never "it is one
line". When the planner incorporates it, and why the cost is accepted: [`docs/BUILDING.md` §
Proposing a change to a document you do not
own](docs/BUILDING.md#proposing-a-change-to-a-document-you-do-not-own). **When the text must land in
*your* commit** — a gate's `VERIFICATION.md` section, a counted paragraph a test asserts — the
planner dictates it and you paste it unchanged: **ask, do not draft**
([`docs/BUILDING.md` § Content mine, keystrokes
yours](docs/BUILDING.md#content-mine-keystrokes-yours)).

## 🚫 Unbuilt work is named, never numbered

**A version number belongs to a release when it is cut — never before.** Refer to unbuilt work by
name, and **never write `v0.4` for something unbuilt** — not in docs, `--help`, an error message or
a code comment. Increment IDs (`I7b`, `I8`) stay: they name work inside a plan, not a release.

| Name | What it is |
|---|---|
| **the template release** | Template ecosystem, `pnk upgrade`, the `sqlite-vec` tier |
| **the graph release, staged** | The PPR graph channel and the `[ner]` extra. **Eval-gated, never scheduled** — neither gets a plan, an increment or a number until its gate passes ([`plans/20260804_1016-staged-channel-gates.md`](plans/20260804_1016-staged-channel-gates.md)). **Not the same name as *the graph release***, which left this table at its final cut, 0.11.0 |

A release that cuts more than once **keeps its name in that table until the final cut** — dropping
it at an interim cut deletes a name the later increments still need. The rule's origin, and which
historical records keep the numbers they were written with: [`docs/README.md` §
Conventions](docs/README.md#conventions), which owns the rule — this table is the list.

## Naming (fixed — changing any of these is a breaking change)

| Thing | Value |
|---|---|
| **Project name, in prose** | **`Pinakes`** — capital P. "Pinakes is a portable KB", "a newer Pinakes" |
| Package / command | `pinakes` / `pnk` |
| Repository / docs site | `github.com/lucagattoni/pinakes` · `lucagattoni.github.io/pinakes` |
| Manifest / sidecar | `pinakes.toml` / `<file>.pnk.yaml` |
| Generated state | `.pinakes/` |
| MCP tools | `pinakes_*` — never bare `kb_*`, which collides across servers |
| Cross-KB URI | `pnk://<kb-ulid>/<doc-ulid>` — ULIDs only, never aliases |

**Capital `P` names the project; lowercase `p` names something you can type** — `pinakes.toml`,
`.pinakes/`, `import pinakes`, `src/pinakes/` and every URL stay lowercase inside a sentence that
otherwise says Pinakes. Runtime output names the *command*, so it stays lowercase too. Applied
across the repo 20260804 11:55, history included.

## Invariants that must not be broken

**[`docs/INVARIANTS.md`](docs/INVARIANTS.md)** — ULID permanence, the sidecar byte-identity bound and
its `ruamel`-only rule, `docs/` belonging to the user, `.pinakes/` disposability, the append-only
ledger and what a `void` record needs, the paid-path allowlist, `Decimal` money, `schema_version`.
**Read it before touching a sidecar, the ledger, the index schema, or anything that could import a
paid client.** Each one fails *silently* when broken, which is why it is a list and not a convention.

## Building an increment

**The procedure is [`docs/BUILDING.md`](docs/BUILDING.md)** — own worktree, tests in the same
increment, `./check.sh` green, mutate the assertions, adversarial review, fragments, then
`tools/land.py`. Never batch increments. Read the build order out of `plans/` — **never** "the newest
file" there ([`docs/README.md`](docs/README.md) tells them apart).

**Mutation is a tool, and its batteries are committed:** `python3 tools/mutate.py <battery.toml>`,
and `--check-anchors tools/batteries/*.toml` to ask whether they still hold. **Append a section to
the battery your target already has; never start a second file for it** —
[`tools/batteries/README.md`](tools/batteries/README.md) carries the naming rule and what to do when
an anchor rots, and `tests/test_batteries.py` fails if you get it wrong.

**What is live right now** — the full routing table, with what each closed plan still binds, is
[`docs/README.md`](docs/README.md):

- **🧭 The live build order is
  [`plans/20260901_1148-clear-the-user-facing-list.md`](plans/20260901_1148-clear-the-user-facing-list.md)** —
  its § 3 is the queue. **§ 4 was ANSWERED by the user 20260902 — option E**, no freeze plus a
  written re-measure trigger, so the section is kept for its reasoning and is not a question any
  more. Read § 3 before picking anything up, and **read a row's body, not only its cells**:
  *Blocked on: nothing* speaks about external blockers, and **four** rows carry a choice inside
  them — 9, 23, 25 and 28. **This clause said *two* while the bullet below it said three**,
  which is the shape to distrust: a count in one place and a list in another.
  **Everything below this bullet is background, not a queue.**
- **🛑 EVERY PUBLISHED RELEASE OFFERS TO DELETE A PERMANENT ULID, AND CRASHES ON THE MINIMUM
  SUPPORTED PYTHON. Both are fixed on `main` at `934190c` and in **no published wheel**.** Two
  defects, one condition: a document that is present on disk but that this process cannot reach —
  a symlink whose target sits under a directory lacking `+x`.
  **The worse one is not the crash, and it is interpreter-independent.** `pnk doctor`'s orphan
  check asked whether the document was a *readable* file, so a present-but-unreachable document was
  reported `WARN orphaned sidecars: 1` under the remedy *“Remove with `pnk doctor --prune`”*.
  Taking that advice deletes the sidecar and the stored ULID that
  [`docs/INVARIANTS.md`](docs/INVARIANTS.md) calls permanent. **Verified by the planner against the
  published 0.32.2 on 3.14** — `WARN orphaned sidecars: 1: docs/alias.md.pnk.yaml`, with
  `os.path.lexists` and `os.path.islink` both `True` for that document at the same moment.
  **The crash reached `pnk doctor` too, not only `pnk sync`.** `Path.is_file()` and
  `Path.exists()` raise `PermissionError` on 3.13 and return `False` on 3.14 for that path;
  `os.path.isfile`/`exists` return `False` on both, which is why `src/pinakes/paths.py` now owns the
  spelling (`is_regular_file`, `resolves`) and why its `False` deliberately means three states, not
  one. Sites hit: `sync.walk_sources`, **`doctor.py:420`** and `linkscan`. The coder's fix landed
  after an adversarial review found the second and third — the first attempt was two private
  helpers inside `sync.py` that the other two callers could not reach.
  **A cautionary measurement, mine, 20260903 14:20:** I ran the published `pnk doctor` on both interpreters,
  watched it complete, and wrote into row 28 that `doctor` does not crash on 3.13. **True
  measurement, wrong population** — that KB had no sidecar for the unreachable document, so
  `_sidecars` never entered the loop whose body raises. Re-run against a KB where the document had
  actually been indexed, it dies at `doctor.py:420`. `rglob` itself raises on neither version, so
  the walk looks safe and the `stat` inside it is not. **Do not accept a null result here without
  the sidecar present.**
  **Why nothing caught any of it: no `.python-version`, no `setup-python`, and `uv sync --frozen`
  takes the newest interpreter available — 3.14 on the runner.** The `check` matrix varies
  *extras*, never interpreters, so the floor in `pyproject.toml` had never been executed by CI. **A
  fresh worktree runs 3.14 and the primary checkout runs 3.13**, so one commit answers differently
  in two directories on this machine — a branch gate green and the merged gate red on the same
  tree. `.github/workflows/ci.yml` now carries a `minimum-python` leg that asserts the interpreter
  it actually got, **and it had never executed once as of `934190c`** — the workflow triggers on
  push to `main`, so no branch push could run it. Read its first run before trusting it.
  **The false claim in the docs is a support claim, not a testing one**: nothing in `docs/` says
  3.13 is tested, while `docs/DESIGN.md` line 3, `docs/GUIDE.md` line 51, `README.md`'s badge and
  this file all say 3.13 is **supported**. Audited 20260903 13:23. **Do not "fix" those by raising
  the floor** — the code is the fix, and it is written. Also wrong, in the other direction:
  `docs/RETROSPECTIVES.md:2218` distinguishes a developer machine from CI by *“different OS,
  different Python”*, when the interpreter is the one thing the matrix held constant.
- **🚦 0.32.2 is published and swept. 0.32.3 is DUE and uncut, fourteen fragments deep — and it is
  the one that carries the ULID fix, so it matters more than an ordinary patch.** `changelog.d/`
  holds **5** and `retro.d/` **9** as of 20260903 14:21: sweep row 8's three fixes (a mistyped
  `--source-type` is a usage error, an empty KB stops blaming filters nobody passed, a broken
  symlink is reported rather than skipped) plus the two above — the 3.13 crash and `doctor`
  offering `--prune` a present document's id. **Cut as a PATCH**, on the coder's reasoning that
  `doctor` now reports *fewer* orphans and a sidecar whose document is present was never an orphan,
  so a false positive is removed rather than a contract narrowed.
  **One gate must be read before the tag: `minimum-python` had never executed as of `934190c`.**
  Do not cut on the strength of a local 3.13 run alone; read that job's own conclusion in the CI
  run for the commit you are tagging.
  0.32.2's own cut landed 13:07:54 with the wheel on the index 47 seconds later, verified with a
  control that fires: `pnk search -k 0` exits **2** at the parser on 0.32.2 and **1** on *no
  pinakes.toml found* on 0.32.1. **Do not re-litigate that bump if you are reading its record**:
  refusing `-k 0` *is* a breaking CLI change, and this project ruled that exact case at **0.7.1**
  and **0.20.1** on the ground that the previous behaviour was the defect.
  **`pnk sync --sidecars-only` reporting five zeros is S20, filed with no build-order row on
  purpose**: what the summary should count is the user's call, not an implementer's.
- **📌 The release procedure gained a timing rule at 0.32.2, and it changes what a release commit
  writes.** `docs/ROADMAP.md`'s `## Where things stand right now` reconciles three registers
  *counted, never incremented* — CHANGELOG headings, `git ls-remote --tags`, this file's table — so
  at the release commit, where the tag does not yet exist, writing it means incrementing. It now
  belongs to the **post-publish sweep**, in the same commit as STATUS's two published-version
  registers. `docs/RELEASING.md` § *Sweep the three documents* carries it. **The same row also
  stopped telling planners that Part 5's *Open corrections* heading carries an item count** — it has
  carried none since 20260825, when renaming it broke two in-page anchors.
- **✅ 0.32.0** (green 20260902 10:51, published 10:07). Its red
  lasted 44 minutes and is worth one sentence: a money assertion compared a value taken *before*
  the ledger's write-time quantisation against one taken *after* it, and **had been green for a
  month on the value of a constant it never mentions** — the ECB rate, which
  `docs/RELEASING.md` § *Before you start* step 3 now refreshes at every release. **That is the
  durable lesson, and it recurs**: the same file carried a second, latent instance one hop down.
  Fixed in `cf1f1cb`. The
  **20260830** red build, that release and its
  fourteen document defects are all **closed** — but read
  [`plans/20260830_0927-main-is-red-and-a-review-that-half-ran.md`](plans/20260830_0927-main-is-red-and-a-review-that-half-ran.md)
  anyway, because what it now carries is not that incident. It holds the **22 findings nobody had ever
  checked** — **checked 20260831**: four confirmed, eight pointing at `retro.d/` files consumed into
  `docs/RETROSPECTIVES.md` at a release, one still open. **Severity *as raised* ran about 5:1 against
  the tree**, which is the number to remember before trusting an untested raise, the rule that **a claim resting on a set you selected or an instrument you chose
  must state the selector**, and the record of **six** wrong claims in one day, each a valid
  inference over a population nobody named. **`prices.toml` is refreshed at every release
  now** — `docs/RELEASING.md` § *Before you start* step 3, which had never existed.
- **🛑 Two plans have scheduled work, and it is NOT all coder work any more.** Rows 21 and 22 of
  the live plan are **planner-owned** — the dogfooding on-ramp's design, and regenerating this
  file — both added 20260902 on the user's own instructions; and **rows 9, 23, 25 and 28 each
  carry a design choice inside a row whose blocker cell reads *nothing*** — row 9 where two
  `doctor` helpers live, row 23 whether `pnk upgrade` fails or degrades, row 25 where a
  plain-text guard belongs, and **row 28, filed 20260903, when `pnk doctor` walks at all**:
  an unresolvable symlink is invisible to it while `pnk sync` reports the same one, and
  widening the trigger changes `doctor`'s cost on every KB. `docs/README.md` names all four;
  this bullet named only row 9 until 20260903 12:16.
  *(What the red-main plan still owes is written into its § CHECKED 20260831, not into a queue
  row — five small corrections, each naming its own file.)*
  **The S16 HIGH holds nothing any more** — the user answered it 20260831 21:38 UTC
  (`sqlite3.IntegrityError` caught **narrowly**, on `SQLITE_CONSTRAINT_UNIQUE` naming
  `documents.path` only) and it was built and landed the same evening. **That option was invented
  when the question was put and is in neither the branch nor the plan's original two — read the
  sweep plan's build-order row 2, never a memory of the options.**
  *(This bullet has now been wrong **four** ways in three days: "all coder work — every decision is
  taken"; then "rows 3–5 … are owner planner" when rows 3 and 4 already read ✅ DONE; then "a live
  user decision holding a landing" for the half-hour after it was answered and built in another
  session; then "every row in them is coder work", for the two days after two planner rows were
  added; and now a fifth — naming **row 9 alone** as decision-bearing where `docs/README.md` named
  rows **9, 23 and 25**, for the day after rows 23 and 25 were written. **It is the most-falsified
  region in this file, and every instance has been about who owns what or who must decide what** —
  which is the one thing a cleared session reads it to learn.)*
  The **eight decisions and fifteen questions** in
  [`plans/20260825_1803-open-decisions.md`](plans/20260825_1803-open-decisions.md) were **ANSWERED by
  the user 20260825 18:16**, and the planner's half of them landed **20260825 18:39–18:56 UTC**, with later records and corrections through 20260826: D-34 closed
  (*promises only*, plus the audit that rowed 14 unrowed promises in `tests/test_serve.py`), arity
  requirement 3 closed, the three residues ruled, the `requires_pinakes` clause closed-superseded,
  `expect_green` declined, and the re-extraction loop and the `fragments.py` widening both deferred
  behind **written triggers**. **Every decided item now carries a build-order row** — D-36's build,
  the `_toml.py` unknown-key message and the G5 gate re-run gained theirs 20260826, the last after
  **21 days** with an owner and no queue position. Work whose owning plan has no build order is
  parked in the sweep plan's § *Decided work with an owner and no build order*, each row linking to
  the plan that owns the decision. **An owner without a queue position is how work ages here.**
  [`plans/20260825_0749-exposure-and-silent-status.md`](plans/20260825_0749-exposure-and-silent-status.md)
  — **§ X1 is built and on `main`**; **D-35 was answered 20260825 12:37**, which unblocks **§ X7**
  (three layers, and *not* what that plan first proposed — read the section, not the memory of it);
  **D-31 to D-34 were ANSWERED 20260825 18:16** — as were D-36, D-37 and every other open question, in
  [`plans/20260825_1803-open-decisions.md`](plans/20260825_1803-open-decisions.md), which is now the file
  to read first. **Two of the taken options were invented by that pass's adversary and are not in the
  original plans — read the decision, never a memory of the options.**
  [`plans/20260825_1240-run-pinakes-sweep.md`](plans/20260825_1240-run-pinakes-sweep.md) — **defects found by running
  Pinakes** (thirteen numbered — S1–S9 and S16–S19 — plus unnumbered Low classes; **that file states
  no total and neither should you**) — **S16 and S17 were both found by *reviewing
  a fix*, which is the sweep's own lesson turned on itself.** **S16 is ✅ BUILT** — landed
  `926bc43` 20260831, its rows and the sentence its fix falsified in `a53f2ed`. It crashed `sync`
  on an ordinary two-file rename swap while `doctor` reported OK, and `search` then answered from
  the wrong file. The fix **orders the applicable plans**; the **cycle half is contained, not
  resolved** — a `PathStillHeldError` with a remedy instead of a raw traceback, `pnk sync` still
  exiting non-zero, rows still left at paths no longer on disk.
  **It really was re-reproduced 20260826 06:49 UTC** against `origin/main`'s exact `src/` tree,
  after S2's fix — and that matters because *a still earlier claim of a 20260826 reproduction
  was* **unsupported** when it was made: the only run on record at that point was 20260825 18:18,
  *before* that fix — which is exactly how S17 came to be recorded as open after it had been
  cured.
  **S17 is ✅ FIXED** (it printed a remedy that never worked and left the document unindexed): the
  moved-sidecar guard from S2's second review fixed it as a side effect, **verified with a control**.
  **S2 is ✅ BUILT** (landed `3876b57`, 20260826 04:06 UTC). **S18 is ✅ BUILT** (20260830, `a2f5b86` + `8bb4be0`; this file was the last register still calling it open). **S19 is open and now *measured*** — its non-cyclic half reproduces, run independently by both sessions 20260826 07:19 UTC, so S16's scope is settled: ordering the applicable plans fixes the whole chain class, **cycles are a separate mechanism**, and the pinning case is a chain of three rather than a two-file swap. **D-36 and D-37 are now answered**. Every
  other file in `plans/` is closed, answered, deferred or proposed-unscheduled — and **an
  empty-looking list still means *the next thing to build has not been planned yet*, never *nothing
  to do***. `docs/ROADMAP.md` Part 5 holds what comes after.
- **A status claim is never gated — not a `##` heading, not a table cell.** In
  [`plans/20260731_1202-open-corrections.md`](plans/20260731_1202-open-corrections.md) an item's
  closure can sit in its **body**, so `grep '^## '` returns *Live* and stops — **this put two
  freshly-cleared coder sessions within one message of rebuilding a landed increment, 20260824 and
  again 20260825**; both times a peer caught it and no gate did. **On 20260826 it recurred one level
  in**: [`plans/20260825_1252-plans-sweep-findings.md`](plans/20260825_1252-plans-sweep-findings.md)
  holds **two registers of the same facts**, the pass that answered eight decisions updated the
  bullets and not the 27-row table — **twelve of its 27 rows stopped describing the tree**, and row
  1 read *S2 · LIVE · blocked on nothing* from S2's landing until a planner happened to look. **So: where a
  dated snapshot and a `## Build order` disagree,
  the build order wins.** **Read an item's body before building it**, and read an empty list as
  *nobody has run Pinakes lately*. **An item that reads as a decision may only be an unchecked
  assumption** — and one that reads as live may already be closed.

## Landing work: always push, always release

**Nothing is done until it is on `origin/main` and, when it completes a unit of work, tagged.** Work
left local is invisible to every other agent, machine and scheduled run. **The procedure is
[`docs/RELEASING.md`](docs/RELEASING.md).** These are the rules it assumes:

- **Push every landing** to `origin/main`, then fast-forward the primary checkout
  (`git pull --ff-only`). Never leave merged work sitting locally.
- **Before merging, run `python3 tools/shared_file_overlap.py --fetch --strict`** — then go and
  *read* the merged state of the files it names. **A clean auto-merge is not a correct merge:** git
  merges edits that do not overlap textually, never edits that *agree* (20260729). For the two
  documents every change writes to, the cause is removed rather than reported —
  [`changelog.d/`](changelog.d/README.md), [`retro.d/`](retro.d/README.md).
- **That tool cannot see a peer.** It compares you to `origin/main`, never to another branch — so
  before landing, intersect file sets with every live branch yourself, and settle the *order*,
  which may be forced rather than agreed: a peer's new gate can be red on `main` until your fix
  lands, and **running their gate is what finds that; asking them is not** (20260823).
  [`docs/RELEASING.md` § Landing beside a peer](docs/RELEASING.md#landing-beside-a-peer).
- **Cut the release** as soon as the work passes the SemVer table (feature = MINOR, fix/docs/deps =
  PATCH, breaking = MAJOR). Complete work never lingers in `[Unreleased]`.
- **A tag publishes to PyPI** and PyPI never accepts a version twice: `make release-check` runs
  **before the push**, never after — create the tag, gate it, then push
  ([`docs/RELEASING.md`](docs/RELEASING.md) steps 6–7). It is a real gate as of 20260826 and
  **absence is red**; it was three `echo`s until then. **A CHANGELOG entry and a `__version__` are only claims** —
  verify the release happened, never assume it.

## Tooling

- **uv only** — `uv add`, `uv run`, `uv build`. Never pip, poetry, or a hand-managed venv.
- Python 3.13+. `ruff`, `pyright` (strict), `pytest` must pass before any commit.
- `uv run ty check` is a fast pre-check, **never** the gate — at 0.0.63 it caught a fraction of
  what `pyright` strict does (RETROSPECTIVES, I1). Re-measure when it leaves beta.
- **Core dependencies stay light.** Nothing pulling torch enters `[project.dependencies]` —
  embedding backends are extras (`[st]`, `[light]`), and so are the PDF extractors (`[pdf]`,
  `[claude]`). CI's `check` job is a three-leg matrix over `[light]`, `[light,pdf]` and
  `[light,pdf,claude]`.

## Changing retrieval

Any change to chunking, fusion weights, reranking or the confidence signal must be justified by the
golden-set eval (`recall@k`, MRR, false-abstain rate) — never by intuition alone. Report the before
and after numbers in the commit message.

**And name the corpus that can license the change.** `tests/demo-kb`'s golden set is a regression
guard, not a licensing instrument — its improvable pool is too small to carry a verdict, so a
claimed improvement needs the RFC corpus (`tools/build_rfc_corpus.py`; frozen questions in
`tools/rfc_corpus/questions.yaml`) or another corpus whose improvable pool has been **re-measured,
not remembered**. The numbers, and why a power limit is not a mechanism limit: [`docs/DESIGN.md` §
What a corpus can license](docs/DESIGN.md#73-what-a-corpus-can-license).

## Docs

**One fact, one home** — [`docs/README.md`](docs/README.md) is the routing table and the
per-increment landing checklist. `docs/DESIGN.md` is rationale only; it changes when the *reasoning*
changes, never for a new flag or field alone. **README and DESIGN.md are deliberately version-free**
— never reintroduce a version number or "as of vX" claim into their prose.

**Seven rules live in [`docs/README.md` § Conventions](docs/README.md#conventions), each with its
measurement — read them before any docs change**: audit the neighbourhood not the diff; name the
audience and goal before writing; rewrite to the current state, never layer corrections; compact
monthly; verify a doc by running the commands it shows; a link *out* of `docs/` is absolute; never
rename a heading to fix a site anchor. `docs/` is **published** to
[lucagattoni.github.io/pinakes](https://lucagattoni.github.io/pinakes/) on every push to `main`, so
run `make docs` (`mkdocs build --strict`, which a PR also gates) before landing a docs change.

- **Every date carries a time, in UTC** — `YYYYMMDD HH:MM`, in the CHANGELOG, `docs/STATUS.md`,
  `docs/RETROSPECTIVES.md` and any "verified on" claim. **Read the clock, never compose it**:
  `date -u "+%Y%m%d %H:%M"`, or derive a past stamp from `git log`. **Timestamps written before
  20260804 11:32 are local and stay local** — converting one invents precision nobody measured.
- **Every new file in `plans/`, `changelog.d/` and `retro.d/` is named `YYYYMMDD_HHMM-<rest>.md`**
  (UTC, underscore not colon — the branch-name format), so `ls` reads chronologically.
  `tools/fragments.py` strips the prefix before reading a fragment's category. Batteries are named
  for their target instead, never dated.
