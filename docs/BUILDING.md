# Building an increment

**Audience: the agent building it. Goal: executor.** Follow it in order. This is the procedure that
runs *before* [Cutting a release](RELEASING.md); the rules about when to release are in
[`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md).

Extracted from `CLAUDE.md` on 20260806 00:00, when that file crossed its own size guardrail — as
`RELEASING.md` was on 20260801. Nothing was dropped in the move. **Which plan is live stays in
`CLAUDE.md`**, because it changes every few days and this procedure does not.

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

1. Own worktree, branch `YYYYMMDD_HHMM-i<N>-<slug>`.
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
   assertions, confirm the *right* test fails for the *right reason*, restore. The harness rules,
   each earned at least twice ([RETROSPECTIVES.md](RETROSPECTIVES.md) § *Start here* → "run a
   mutation pass"):
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
6. **A `changelog.d/` fragment in the same commit as the code** — never an edit to `CHANGELOG.md`
   itself
   ([`changelog.d/README.md`](https://github.com/lucagattoni/pinakes/blob/main/changelog.d/README.md)).
7. Land it — but first `python3 tools/shared_file_overlap.py --fetch --strict`: **other agents
   land work concurrently at any time**, and a clean auto-merge is not a correct merge
   (`CLAUDE.md` § Landing work). Then `python3 tools/land.py <branch> --cleanup`. **Never `git merge` by hand** — from inside
   the branch's own worktree that merges the branch into itself and reports success three times over
   ([`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md)). **Then
   `gh run list --branch main`**: local green is one leg of a three-leg matrix, and `main` has been
   red for three pushes and, later, four consecutive merges without anyone noticing (20260728, 20260801).

Which documents an increment touches, and in what order: [`docs/README.md` § Landing a new
increment](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md#landing-a-new-increment).

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

**A pointer nothing links to is not a handover.** Verify by opening what a fresh session opens —
`CLAUDE.md`, then `docs/`, then the plan — not by trusting that you wrote it down somewhere. A
*missing* row has no wrong text to find, so no diff review and no grep reaches it; only the question
does ([RELEASING.md](RELEASING.md), 20260811).
