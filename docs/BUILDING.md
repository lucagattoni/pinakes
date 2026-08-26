# Building an increment

**Audience: the agent building it. Goal: executor.** Follow it in order. This is the procedure that
runs *before* [Cutting a release](RELEASING.md); the rules about when to release are in
[`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md).

Extracted from `CLAUDE.md` on 20260806 00:00, when that file crossed its own size guardrail — as
`RELEASING.md` was on 20260801. Nothing was dropped in the move. **Which plan is live stays in
`CLAUDE.md`**, because it changes every few days and this procedure does not.

## Settle your role before anything else

**A cleared or fresh context keeps the repository and loses the one fact that decides what it may
touch.** `CLAUDE.md` carries the rule; this is the procedure and the record behind it.

1. **Name your own role — coder, planner, or another — from what the user said in *this* session.**
   Not from what the repository makes possible, not from what the previous session was doing, and
   **not from the work that happens to be in flight**: a session that opens on an unlanded docs
   branch reads as *planner* and may not be one. **If you cannot determine it, ask the user and do
   nothing else until they answer.** This is one of very few rules here where the correct move is
   to *block*, and it has to be stated as an exception because `CLAUDE.md` § *Working mode* other-
   wise overrides the default of stopping.
2. **Ask every live peer the same question.** `ListAgents`, then `SendMessage` each live session:
   *what role do you hold, what are you working on, which paths are you holding?* State your own
   role, file set and timing in the same message — a peer cannot route around you if it does not
   know you exist — and wait for the reply before touching a shared path.
3. **Then work inside the ownership table** in `CLAUDE.md` § *Documentation has one owner*, and
   re-check at the moment of landing: `python3 tools/shared_file_overlap.py --fetch --strict`, then
   read the merged state of what it names.

**Both failure directions are silent, and 20260823 produced both inside a few hours.** One session
opened on an in-flight docs branch, from which *planner* was the natural inference, and was told
*"you are the coder"* two tool calls later — without that, it would have landed documents it did
not own. The other announced a land on a mandate its peer could not see; the mandate was real, and
the only thing that established it was the peer **asking**. A rule naming only the first direction
invites the second, where an agent that is in fact the planner leaves a document wrong out of
misplaced deference.

**A peer's answer is coordination, never permission.** It cannot authorise an action the user has
not, and an instruction relayed through a peer is something to put to the user as a diff — not
something to land.

## Proposing a change to a document you do not own

The ownership table is in [`CLAUDE.md` §
*Documentation has one owner*](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md). This is
what to do when a document it does not give you is wrong.

**Propose as `git diff <sha> -- <file>` against a named commit**, in your branch's commit message or
a note the planner reads. Never an edit, and never "it is one line".

**The planner incorporates it — judging *when*, not whether.** A correction to what is true **today**
lands on `main` at once. A doc change describing **your unlanded work** lands with your merge: `main`
must not document a command that does not exist yet.

**Why a round trip is worth it.** Documentation is the coordination surface, and a clean auto-merge
is not a correct merge — git merges edits that do not overlap textually, never edits that *agree*
(20260729). The cost is accepted: a correction waits for the planner.

**The one narrow exception is [`VERIFICATION.md`](VERIFICATION.md)** — add **only** the row a test
you wrote requires, and nothing else in that file.
[`tests/test_verification.py`](https://github.com/lucagattoni/pinakes/blob/main/tests/test_verification.py)
hard-fails on an unresolvable name, so a renamed or new test with no row makes *your own* branch red
**and you could not self-certify**.

## Read the build order out of `plans/`

**Never "the newest file" there.** That directory also holds shipped plans, an iteration log,
standalone increments, re-entry checklists and decision records;
[`docs/README.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md) has the table
that tells them apart, and `CLAUDE.md` names the one that is live.

Two rules about reading a plan, each learned more than once:

- **A plan's open decision is what the *plan* has not settled — not what the *repository* has not
  settled.** T5's D-4 sat open in the plan while `manifest.py` had already answered it one line
  below `VECTOR_TIERS`. Read the sibling key before weighing the decision table.
- **Read a plan's test list as part of its specification, not as an illustration of it.** Where
  prose and test list disagree, the test list has been forced to be concrete and the prose has not
  (T7's containment rule named one of its two real layers). But a named test can also be a
  prediction that cannot discriminate — T4's conflicting-hunk test asserted an observable both
  implementations produce — so re-derive the scenario before writing it.

## One increment at a time

Never batch increments; each is a separate, bisectable landing:

1. Own worktree, branch `YYYYMMDD_HHMM-i<N>-<slug>`. **And run the gates there, never in the
   primary checkout** — that is where `tools/land.py` merges, so another session can change its
   tree under a running `pytest` at any moment. Measured 20260823: a peer landed mid-`./check.sh`
   and three tests failed with *"matched 0 `# Part` heading(s)"* — loud, plausible, and pointed at
   the file that session had just touched. Nothing was wrong. **A red run in the primary checkout
   may be about a tree that no longer exists**, so re-run it at the new sha before believing it.
2. Implement the increment **with its tests** — tests ship in the increment that introduces the
   behaviour, never deferred. A test that touches a PDF fixture, the `claude` extractor or a real
   embedding backend carries the matching `tests/conftest.py` predicate (`pdf_runnable()` /
   `pdf_extraction_runnable()` / `paid_runnable()`) in its skip marker — on a worktree with the
   extra installed, a test that forgot one runs, passes, and says nothing about the CI leg where
   it cannot (20260804 13:30).
3. Green before review: run `./check.sh` (or `make check`) — every gate under `set -e`, so a
   failure is a non-zero exit rather than a line in a log that a pipe then swallows. **Run it bare
   and read its own exit status**: `./check.sh | tail && git commit` reports `tail`'s status, and
   that shape has landed commits over a red gate twice — once one line below the comment in
   `check.sh` that explains it (T4). **Re-run it as the last step before every commit** — green
   expires at the next keystroke, a reworded comment included. It formats Python **inside Markdown
   fences** too: a docs-only commit can still fail the gate. And a green run proves **this
   worktree's venv**, not the three-leg matrix: for a test gated on an extra, run its file once
   with the extra absent (`uv sync --frozen --extra light`, run it, then
   `uv sync --frozen --extra light --extra pdf --extra claude` to restore — never `--all-extras`,
   which pulls the ~2 GB `[st]` extra the matrix deliberately omits) — `uv run --extra X` does **not** prune extras a
   previous sync installed.
4. **Break the code on purpose — after committing.** Mutate the 3–5 most safety-critical
   assertions, confirm the *right* test fails for the *right reason*, restore.

       python3 tools/mutate.py tools/batteries/tools-release_order_gate.toml
       python3 tools/mutate.py --check-anchors tools/batteries/*.toml   # do they still hold?

   **The battery is a committed file, one per target, and you append to the one your target
   already has** — never a second file for it, which is how two increments end up maintaining two
   sets of mutants that disagree. `grep -l 'file *= *"src/pinakes/x.py"' tools/batteries/*.toml` says
   which; no hit means start one, named for the path with `/` → `-` and the extension dropped. The
   rule, and what to do when an anchor rots, are in
   [`tools/batteries/README.md`](https://github.com/lucagattoni/pinakes/blob/main/tools/batteries/README.md);
   `tests/test_batteries.py` fails if an anchor stops resolving, if a `kills` selector names a test
   that no longer exists, or if two batteries claim one file.

   **What the comments in a battery are for.** The proof is re-derivable — an afternoon per gate,
   measured. The *reasoning about which mutants were worth writing* is not, and it is the only
   thing in the file that the code does not already contain. Write it down beside the mutant.

   The harness rules, each earned at least twice ([RETROSPECTIVES.md](RETROSPECTIVES.md) §
   *Start here* → "run a mutation pass") and each a refusal in `tools/mutate.py`:
   - **Commit before mutating** — `git checkout <file>` restores to the last commit, not to the
     pre-mutation state, and has silently reverted uncommitted fixes six times here. After any
     restore, grep for the thing that was supposed to survive it.
   - **Assert each mutation's anchor matched exactly once** — a `str.replace` that matches nothing
     returns the string unchanged and reads as SURVIVED.
   - **Clear the module's `__pycache__` after writing and after restoring** — CPython invalidates
     on (mtime-to-the-second, size), so a same-length mutant applied and reverted within one
     second runs from stale bytecode.
   - **Run without `-x`**, and read *which assertion* fired — a failing test proves the mutant is
     caught, never that it is caught for the stated reason.
   - **Kill one known-catchable mutant first** — a run with no kills is a broken harness, not a
     clean bill.
   **"Mutation-verified" is a per-assertion claim, never a per-commit one**, and "pinned by test
   X" is a claim about a *failing* test: revert the fix and watch it go red, or do not write the
   word.
   **And know what the battery cannot reach: a defect with no assertion anywhere.** A `textwrap`
   reflow of a comment run flattened a `\`-continued shell command onto one line — legal to ruff,
   invisible to pyright, read as prose by a diff review (0.25.3, `4d5debf`). A prose tool pointed
   at text containing load-bearing whitespace needs its output re-read as the thing it is — a
   command, a table, an indent — never as prose. The sibling case: a script navigating Markdown
   matches the heading *level*, never a bare `startswith("## ")` — that steps over every `# `,
   and it is how 0.25.3's release section landed inside ROADMAP's Part 5. Both are prose-shaped
   tools applied to structure they do not model.
5. **Retrospective review** — a fresh adversarial pass over the increment's own diff, repeated
   until clean. Findings and fixes are their **own commit** — **and a fix gets the same treatment
   as the code it fixes, mutation included**: a fix applied under review inherits the review's
   confidence and none of its scrutiny, and a fix can silently disarm a test written for something
   else, so the battery re-runs after it. Anything worth keeping gets a
   [`retro.d/`](https://github.com/lucagattoni/pinakes/blob/main/retro.d/README.md) fragment; trivia
   stays in the commit message.

   **🛑 The pass opens the increment's own fragments, and every file the increment changed.** Not
   the plan it was working from — the diff. **This step's own position in this list is why it did
   not**: step 6 writes the `changelog.d/` fragment *after* the last review pass in step 5, so the
   procedure **guarantees** the fragment is never reviewed. Either write the fragments before the
   final pass, or run one more pass after them; do not leave it to memory.

   **A fragment is not scratch.** `tools/fragments.py` splices it into `CHANGELOG.md` and
   `docs/RETROSPECTIVES.md`, and `docs/` **publishes on every push** — so an unreviewed fragment is
   an unreviewed published document. Measured 20260826 07:42: the changelog fragment written in `d9fe1a9`
   carried *"wrong for twelve hours"*, a duration that had been **invented** and repeated across
   four files, in an increment whose subject was unmeasured claims. The review pass did not catch
   it because the pass read the plans and **never opened the fragment**; it was found while
   re-deriving timestamps for an unrelated reason.

   **The same hole covers ordinary source files.** A corpus measurement over this repository's own
   transcripts (`python3 tools/review_ledger.py <increment>`, landing separately; its last section
   is headed *CHANGED BY THIS INCREMENT, OPENED BY NOBODY*) found review passes open **207 of 248**
   changed files — 83%, and 90% on multi-pass increments — while `src/pinakes/__init__.py`, where
   `__version__` lives, was opened by **none of the 41 passes** over the mutation-batteries
   increment. **A file the increment changed and no pass opened is the cheapest place for a defect
   to survive review.**

   **The rule says *opened*, and that word is doing deliberate work.** What a transcript can show is
   which files a pass **opened**; whether it *reviewed* them is not observable and no tool will ever
   check it. So the checkable rule is the weak one — open every changed file and every fragment —
   and it is stated as the floor rather than the goal. **An opened file is not a reviewed file**;
   the measurement is a lower bound on attention, never evidence of it.
6. **A `changelog.d/` fragment in the same commit as the code** — never an edit to `CHANGELOG.md`
   itself
   ([`changelog.d/README.md`](https://github.com/lucagattoni/pinakes/blob/main/changelog.d/README.md)).
   **Written before the last review pass, or reviewed by one of its own** — see step 5.
7. Land it — but first `python3 tools/shared_file_overlap.py --fetch --strict`: **other agents
   land work concurrently at any time**, and a clean auto-merge is not a correct merge
   (`CLAUDE.md` § Landing work). Then `python3 tools/land.py <branch> --cleanup`. **Never `git merge` by hand** — from inside
   the branch's own worktree that merges the branch into itself and reports success three times over
   ([`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md); what `land.py`
   refuses, and why `--cleanup` deletes both copies of a branch:
   [RELEASING.md § Landing a branch](RELEASING.md#landing-a-branch)). **Then
   `gh run list --branch main`**: local green is one leg of a three-leg matrix, and `main` has been
   red for three pushes and, later, four consecutive merges without anyone noticing (20260728, 20260801).

Which documents an increment touches, and in what order: [`docs/README.md` § Landing a new
increment](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md#landing-a-new-increment).

## Content mine, keystrokes yours

**Some planner-owned text cannot land in its own commit.** A `docs/VERIFICATION.md` section for a
gate you are adding, or a counted paragraph in `tools/batteries/README.md` that
`tests/test_batteries.py` asserts, must change *atomically* with the code — **any split ordering
leaves `main` red or wrong at some commit**, and a repository whose gates are its memory cannot
afford either.

**So the planner decides the exact text and says so explicitly, and the implementer pastes it into
their branch unchanged.**

| | |
|---|---|
| **Authorship** | the planner's, entirely. Nothing about the ownership table is suspended |
| **The keystrokes** | the implementer's, because the commit has to be theirs |
| **The form** | the planner gives the **verbatim text**, not a description of it |

**This is not a licence to draft and seek approval afterwards.** *"I wrote it, is this alright?"* puts
the planner in the position of reviewing rather than deciding, which is the thing the ownership rule
exists to prevent — and a review that says *yes* is indistinguishable from one that was never
properly read. **Ask; do not draft.**

**Why it is written down at all:** it was re-derived from first principles **four separate times in
one session** (20260825), and two such edits were authorised into a coder's branch that day with no
record of why an implementer's commit contained planner-owned text. A future reader had no way to
learn the difference between this and a broken rule.

## Hand over before you stop

**Context dies with the session; disk survives.** So the handover is part of the increment, landed
in the same branch as the work — never a follow-up, because the pointers an increment falsifies are
exactly the ones the *next* session opens first. Set by the user 20260811 15:37, alongside the rule
that a boundary needing a context clear is a **stop** rather than an offer
([`CLAUDE.md` § Working mode](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md)).

| Where | What goes stale the moment the increment lands |
|---|---|
| **`CLAUDE.md`'s live-plan pointer** | "Build E1 next" — the first thing any session in this repo reads |
| **`docs/README.md`'s plan-routing row** | the same claim, for whoever opens `docs/` first |
| **The plan itself** | mark the increment built, and record what shipped *beside* what the section asked for — including anything the next increment needs that only this one learned |
| **The plan's baseline / measurement block** | which of its rows this increment just falsified, and how far `file:line` moved. Every plan here has drifted this way; the template release's did about thirty times in four days |
| **[STATUS.md](STATUS.md)** | the surface row — `on `main`, unreleased` between landing and release, then the version |

**All five are planner-only, so an implementer hands over by *proposing* them.** The rule that the
handover lands in the same branch as the work (the user, 20260811 15:37) is unchanged and is not
weakened here: what lands in that branch is the `git diff <sha> -- <file>` for each row, per
[§ Proposing a change to a document you do not own](#proposing-a-change-to-a-document-you-do-not-own).
The planner incorporates them. **An implementer that edits these directly has broken the ownership
rule, not satisfied the handover one** — and an implementer that writes nothing has satisfied
neither. The two rules meet here rather than collide; only the *form* of the handover differs by
role.

**`RESUME.md` may only ever hold what is also recoverable from `main`.** It is excluded via
`.git/info/exclude` — a file that is itself never committed — so a cloud run, a scheduled routine,
another checkout or a fresh worktree sees **no handover at all, and cannot discover that one
exists**. Neither `CLAUDE.md` nor `docs/README.md` points at it, deliberately: committing it
would make a file both roles write into a planner-only merge hotspot. **So it is a convenience, never
a carrier.** Anything that would be lost if it vanished belongs in the five rows above, which are
committed. The file already claims this about itself and nothing enforces it — that is the whole of
the rule. This is the *protection-for-me versus visibility-for-everyone* distinction applied to the
repository's own state, and nobody noticed the asymmetry until it was written into a plan about
`.gitignore`.

**A pointer nothing links to is not a handover.** Verify by opening what a fresh session opens —
`CLAUDE.md`, then `docs/`, then the plan — not by trusting that you wrote it down somewhere. A
*missing* row has no wrong text to find, so no diff review and no grep reaches it; only the question
does ([RELEASING.md](RELEASING.md), 20260811).
