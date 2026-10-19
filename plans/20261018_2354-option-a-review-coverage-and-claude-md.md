# Option A — a review fan-out that says whether anyone looked, and a `CLAUDE.md` that fits

**Written 20261018 23:54 UTC by the planner session, at the user's instruction.** Development has
been paused since 20260904 10:21 ([`plans/20260904_1027-development-paused-handover-and-evidence.md`](20260904_1027-development-paused-handover-and-evidence.md)).
**The user resumed it for this plan only**: *"Resume with option A, bounded to the analysis's three
cheap steps plus regenerating CLAUDE.md (show me the diff first), then plan option B's dogfooding
on-ramp."* Approved 20261018, with the recommendations on D1–D5 below, including the D3 smoke run.
**Every other row in the live plan stays paused.** Do not pick one up because this file exists.

## 1. What this is, and the source

The pause was to review the development process against *Framing, Not Roles* (Claude artifact
`2c7961ec`, written 20260903 against `d474ffa`). Its § 9 sequences the corrections by evidence and
reversibility. This plan takes **steps 1–3, which that table calls cheap and reversible, and row 22
of the live plan** (regenerate `CLAUDE.md`). Quoted from the artifact, not paraphrased:

1. *"Coverage in every fan-out's return value; count nulls before filtering; report VACUOUS /
   PARTIAL / CLEAN."*
2. *"Run `review_pass_gate.py` at fan-out completion — the workflow's last step and a Stop hook.
   **Not** in `check.sh` or CI, which have no journal and would pass vacuously."*
3. *"Slow lenses first; 'look at the disk' line in every refuter prompt; the missing-set lens as a
   named agent."*

**Taken from the artifact's § 9 and left for later, on purpose** (the analysis's own order puts them
after these three): step 4 (calibrate the review instrument with seeded defects), step 5 (ownership
and land rules as hooks), step 6 (`.claude/agents/` definitions, procedures to skills), step 7 (the
status-claim linter, which is also row 24), step 8 (planner as session or definition). **Its
*do not* list stands**: no reviewer session, no loosening of the ownership table, no larger
fan-outs before step 4, no agent teams for the planner→coder flow.

## 2. The increments

| # | What | Files | Owner | Status |
|---|---|---|---|---|
| **A0** | Record the decision: this file, a routing row, one line in the pause bullet. | `plans/` (this), `docs/README.md`, `CLAUDE.md` (one line, diff shown first) | planner | in progress |
| **A1** | **Steps 1 and 3**: one committed review workflow. Contract in § 3. | `.claude/workflows/`, `.gitignore`, tests | builder | not started |
| **A2** | **Step 2**: a Stop hook that runs `tools/review_pass_gate.py` on a review run from this turn. Contract in § 4. | `tools/hooks/`, `.claude/settings.json` (diff shown first), tests | builder | not started |
| **A3** | **Row 22**: regenerate `CLAUDE.md`. Method in § 5. | `CLAUDE.md`, and the docs that receive moved text | planner | not started — diff shown first |
| **A4** | Cut the release that carries A. | `CHANGELOG.md`, version | planner | not started |

**Order, and why `CLAUDE.md` is last:** A3 describes a finished state; written first it would
describe the plan, which is how that file has been wrong four ways in three days. A2 follows A1
because the hook reads what A1's workflow writes. **A3 can overlap A1–A2 only in its *read* phase.**

## 3. A1 — the workflow's contract

From the artifact § 8.5, limited to steps 1 and 3:

- **Coverage in the return value.** The result carries
  `coverage: VACUOUS | PARTIAL | CLEAN | FINDINGS` with `lenses: {expected, returned, died}`,
  `checks` (what each lens says it ran), `not_run`, `raised` (a count), `confirmed`, `refuted`,
  `not_real`, `unrefuted`, `unjudged`, `conflicting_rulings` and `ignored_rulings`. **A finding
  whose refuter died is `unrefuted`, never dropped.** *(Field names as shipped. This bullet said
  `lenses_run` and `lenses_died` until the first review pass of A1 found the plan and the script
  disagreeing; the shape that settled is the script's.)*
- **Pinned at both ends.** `args.sha` and `args.base` are both commit shas; a branch name is
  refused, because `origin/main...<sha>` is an empty diff once the increment has landed, and every
  lens reports `diff_files` so one that saw nothing counts as `not_run`.
- **A reply is read again before it is believed.** The schemas are enforced by the runtime and not
  by the script, so an unusable lens counts as dead, an unusable verdict as no verdict (the finding
  is `unrefuted`), an unusable ruling as no ruling (the survivor is `unjudged`), and two rulings on
  one id that disagree cancel out. A judge that throws is a dead judge.
- **Bounded, and said so.** A lens gets at most 20 findings refuted; the rest are listed as
  `unrefuted` with the reason, not dropped.
- **Count before filtering.** `dead = results.filter(r => r === null).length` runs before any
  `.filter(Boolean)`; `dead > 0` forces `PARTIAL` at best. `VACUOUS` means *no lens returned*, and it
  is a different outcome from `CLEAN`, not a smaller one.
- **Slow lenses first**: the runtime lens, then the missing-set lens, then the text lenses, so a
  session limit cuts the cheap end.
- **Every refuter prompt carries** *"If a claim is about state on disk, look at the disk."*
- **Models:** Sonnet for lenses and refuters, one Opus judge over the collected verdicts, which may
  run commands.
- **How it is tested is the builder's call**, and the plan does not choose it: the classification
  (`VACUOUS`/`PARTIAL`/`CLEAN`/`FINDINGS` from counts) is pure and must be tested directly; the
  script's fan-out cannot run in `check.sh`, and the D3 smoke run (§ 6) is the only live exercise.

## 4. A2 — the hook's contract

- **Event:** `Stop`. If a workflow journal was written during this turn, run
  `tools/review_pass_gate.py` over it.
- **Block** the turn from ending while the fan-out is `VACUOUS` or `PARTIAL` **and unacknowledged**.
  Acknowledgement is a file the session writes after it has told the user which lenses died; the
  hook's own message says so. **Claude Code overrides a Stop hook after 8 consecutive blocks**
  (best-practices page, quoted in the artifact § 2), so the hook is a strong nudge and not a lock —
  the plan states that limit rather than discovering it.
- **Never in `check.sh` or CI.** They have no journal and the gate would pass vacuously there.
- **Paths are relative to the project directory.** This repository is public: no `/Users/...`.
- **`.claude/settings.json` is configuration**, so its diff is shown to the user before it lands.

## 5. A3 — regenerating `CLAUDE.md`

**Measured 20261018 on the tree at `72a2bd3`: 473 lines, 6,020 words** (`wc -l -w CLAUDE.md`),
against the global hygiene ceiling of about 150 lines and 2,700 words, and the artifact's target of
under 100 lines. Three earlier slimming passes each grew back within days.

**Method.** Classify every section into one of four outcomes and show the user the full map with the
diff before anything lands.

| Outcome | Where it goes |
|---|---|
| Keep | Rules that change what an agent does and that nothing else enforces: the public-repo rules, the paid-key invariant, the land rule, the ownership table, the naming tables, the pointer to `INVARIANTS.md`. |
| Move | Incident narratives and the long "what is live right now" bullets, to the document that already owns each fact. **Grep first**: a move is verified by finding the text at its destination, not assumed. |
| Delete | Text already stated elsewhere, each one checked. |
| Rebuild from the tree | The live-status block, which row 22 names the most-falsified region. It becomes a short pointer to the live plan and the pause state. **Never a summary.** |

Provenance (who asked, when, which incident) goes in own-line HTML comments, which never reach a
session's context. **A cleared session's only pointer to the live build order is that block**, so
the rebuilt version is checked by reading it as a cleared session would.

## 6. Decisions — taken by the user 20261018, with the recommendations

| # | Question | Taken |
|---|---|---|
| D1 | Where steps 1 and 3 live | **A committed workflow script**, not prose in `BUILDING.md`. Pulls one item of the artifact's step 6 forward. |
| D2 | What the Stop hook does on `VACUOUS`/`PARTIAL` | **Block until acknowledged**, with the 8-block override stated. |
| D3 | A smoke run of the new workflow | **Yes — on A2's own diff**, the smallest real target. It is a multi-agent run and was approved as such. Without it, step 1 would be tested on synthetic input only. |
| D4 | `CLAUDE.md` size | **150 lines and 2,700 words as the hard ceiling, aiming for about 100.** |
| D5 | Release at the end | **Cut a PATCH** after A, on the 0.32.6 precedent for developer tooling. |

## 7. Constraints that apply to every increment

- **Procedure:** own worktree, tests in the same change, `./check.sh` green, an adversarial review
  and fix loop, a fragment, `tools/land.py`, then the CI run read in its logs
  ([`docs/BUILDING.md`](../docs/BUILDING.md)).
- **`./check.sh` in a Claude Code shell on this machine needs two environment fixes**, neither a code
  defect (measured 20261014–15): the harness exports `PYTHONDONTWRITEBYTECODE=1`, which fails two
  `tests/test_mutate.py` tests, and `check.sh` runs some tools with a bare `python3` that is 3.9 here.
  The invocation that passed: `PATH="$PWD/.venv/bin:$PATH" env -u PYTHONDONTWRITEBYTECODE ./check.sh`,
  with its exit status read from a log you wrote, not from a pipe.
- **`.gitignore` does not exclude `.claude/worktrees/`**, which exists on disk inside the repository.
  A1 adds that rule **before** anything under `.claude/` is committed.
- **Delegated builders run on Sonnet** (pass `model` explicitly); only the judge is Opus.
- **A2's `settings.json` and A3's `CLAUDE.md` are instruction files**: the diff is shown and the user
  says yes before either lands.

## 8. After A

**Option B — the dogfooding on-ramp (row 21)** is planned next, as the user asked. It is **not
designed yet**: no plan states what the one-command start does, what the checklist checks, or what
"started" means. That plan is written after A lands, not folded into it.
