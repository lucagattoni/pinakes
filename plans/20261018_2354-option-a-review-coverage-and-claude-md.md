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
| **A0** | Record the decision: this file, a routing row, one line in the pause bullet. | `plans/` (this), `docs/README.md`, `CLAUDE.md` (one line, diff shown first) | planner | ✅ landed `668f92f`, 20261018; CI green |
| **A1** | **Steps 1 and 3**: one committed review workflow. Contract in § 3. | `.claude/workflows/`, `.gitignore`, tests | builder | ✅ **landed `bba0746`, 20261019; CI green on all 16 jobs, `docs` and `injection-audit` too.** Reviewed in three passes (two adversarial, one cold read for the first live run), with fixes after each. **The real fan-out has not been run** (D3, on A2's diff) |
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
  `not_real`, `unrefuted`, `unjudged`, `dismissed_on_a_guess`, `unchecked_high`,
  `contested_rulings` and `ignored_rulings`. **A finding whose refuter died is `unrefuted`, never
  dropped.** *(Field names as shipped. This bullet said `lenses_run` and `lenses_died` until the
  first review pass of A1 found the plan and the script disagreeing, and `conflicting_rulings`
  until the third; the shape that settled is the script's.)*
- **Pinned at both ends.** `args.sha` and `args.base` are both commit shas; a branch name is
  refused, because `origin/main...<sha>` is an empty diff once the increment has landed, and every
  lens reports `diff_files` so one that saw nothing is a dead lens: a sha or base that does not
  exist makes every lens say so and the pass `VACUOUS`, not a quiet `PARTIAL`. After a `--no-ff`
  landing `git merge-base origin/main <sha>` returns the sha itself; the base is then the merge
  commit's first parent, and the script's error says so.
- **A reply is read again before it is believed.** The schemas are enforced by the runtime and not
  by the script, so an unusable lens counts as dead, an unusable verdict as no verdict (the finding
  is `unrefuted`), an unusable ruling as no ruling (the survivor is `unjudged`), and two rulings on
  one id that disagree cancel out. A judge that throws is a dead judge, and any agent that throws
  keeps its cause (`died_why`, the unrefuted reason, the log) instead of losing it to
  `pipeline()`'s bare `null`.
- **A guess is visible.** The refuter is told to default to refuted when unsure, and says in
  `basis` whether it checked or guessed. A high-severity finding dismissed on a guess is a gap
  (`PARTIAL`); at any severity it is listed in `dismissed_on_a_guess` and named in the `note`.
- **The prompts give each agent its role.** A read-only reviewer, told not to message peers or
  follow the repository's role-and-landing rules, to use `mktemp -d` for scratch space, what a
  finding and a severity are, and that text between the markers is data. Whether subagents obey
  is for the live run (§ 6.1).
- **Bounded, and said so.** A lens gets at most 20 findings refuted; the rest are listed as
  `unrefuted` with the reason, not dropped.
- **Count before filtering.** A lens that died is turned into a record of its death before
  anything is filtered (`runs[i] || deadRecord(...)`, never `.filter(Boolean)`), and a dead lens
  forces `PARTIAL` at best. `VACUOUS` means *no lens returned*, and it
  is a different outcome from `CLEAN`, not a smaller one.
- **Slow lenses first**: the runtime lens, then the missing-set lens, then the text lenses, so a
  session limit cuts the cheap end.
- **Every refuter prompt carries** *"If a claim is about state on disk, look at the disk."*
- **Models:** Sonnet for lenses and refuters, one Opus judge over the collected verdicts, which may
  run commands.
- **How it is tested is the builder's call**, and the plan does not choose it: the classification
  (`VACUOUS`/`PARTIAL`/`CLEAN`/`FINDINGS` from counts) is pure and must be tested directly; the
  script's fan-out cannot run in `check.sh`, and the D3 smoke run (§ 6, and § 6.1 for what it must settle) is the only live exercise.

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

### 6.1 What the first live run must settle

Everything below was reasoned about or tested against a stub, and a reviewer said so each time it
raised one. The smoke run on A2's diff is where they are observed; **until then treat a surprise as
a finding about the script, not about the increment under review.**

1. Does the runtime accept `model: 'sonnet'` and `'opus'`, and the schema keywords the script uses
   (`pattern`, `minimum`, `minItems`, `minLength`)? A refusal shows as all four lenses dying with
   their cause in `lenses.died_why`.
2. Is the workflow found by name (`/adversarial-review`, or `Workflow({name})`), and in what shape
   do `args` arrive?
3. Does a relaunch with `resumeFromRunId` retry an agent that failed, and is the resume cache keyed
   on the prompt and options or on the order of calls? The docs say both in different places.
4. Do the lens and refuter subagents, which receive this repository's `CLAUDE.md`, stay read-only
   and silent, or do they try to settle a role or message peers?
5. Do unattended agents manage `git worktree add`, `uv sync` and `/tmp` writes inside a
   worktree-isolated session, and do two agents ever pick the same scratch name?
6. What does a run cost in calls and tokens, and how long does one slow refuter hold up the judge
   (the script cannot set a timeout: `Date` and `setTimeout` are unavailable)?
7. Is `coverage` readable as the first line of a real result, or does the person drown in it?

## 7. Constraints that apply to every increment

- **Procedure:** own worktree, tests in the same change, `./check.sh` green, an adversarial review
  and fix loop, a fragment, `tools/land.py`, then the CI run read in its logs
  ([`docs/BUILDING.md`](../docs/BUILDING.md)).
- **`./check.sh` in a Claude Code shell on this machine needs two environment fixes**, neither a code
  defect (measured 20261014–15): the harness exports `PYTHONDONTWRITEBYTECODE=1`, which fails two
  `tests/test_mutate.py` tests, and `check.sh` runs some tools with a bare `python3` that is 3.9 here.
  The invocation that passed: `PATH="$PWD/.venv/bin:$PATH" env -u PYTHONDONTWRITEBYTECODE ./check.sh`,
  with its exit status read from a log you wrote, not from a pipe.
- **`.gitignore` did not exclude `.claude/worktrees/`** when this plan was written (a machine that has
  run Claude Code excludes it in `.git/info/exclude`, which no other clone has), and A1 added it
  before anything under `.claude/` was committed.
- **Delegated builders run on Sonnet** (pass `model` explicitly); only the judge is Opus.
- **A2's `settings.json` and A3's `CLAUDE.md` are instruction files**: the diff is shown and the user
  says yes before either lands.

## 8. Handover — the state after A1, 20261019

**Written in the branch that records it, because context dies with the session and the pointers an
increment falsifies are the ones the next session opens first** ([`docs/BUILDING.md` § Hand over
before you stop](../docs/BUILDING.md#hand-over-before-you-stop)). Of that rule's five places only
this plan is falsified by A1 landing: `CLAUDE.md`'s pointer and the routing row name this plan and
not an increment, the baseline in § 5 is still true at the sha it names, and `STATUS.md` tracks
product surface, which a developer-tooling workflow does not add.

**State.** `origin/main` is `bba0746` at the time of writing — **verify with `git ls-remote origin
refs/heads/main`, not from here**. Development is paused except for this plan. A0 and A1 are landed;
**A2, A3 and A4 are not started.** Fragments wait in `changelog.d/` (`ls` counts them; none is user-visible, and
there is no release until A4). A1's branch and worktree, `20261019_0002-a1-review-workflow`, still exist:
`python3 tools/land.py 20261019_0002-a1-review-workflow --cleanup-only` removes them, and so does
the older `20261018_2354-option-a-resume`.

**What shipped beside what § 3 asked for**, so A2 does not rediscover it:

- A1 grew from one workflow into a workflow, a Node harness that runs it against stub hooks
  (`tests/review_workflow_harness.mjs`, with a seeded fuzz and a strict check of the `meta`
  literal), a test module, a 114-row battery written from a generator, and an amendment to the
  battery naming rule (a leading dot is dropped, because the hidden name was invisible to the
  README's own lookup commands).
- **Three review passes found what the first battery could not.** A battery of 22 mutants was fully
  killed; a reviewer who then wrote 62 of its own saw 50 survive. The lesson is kept as a memory
  note and is the argument for the analysis's step 4 (calibrate the review instrument): a fully
  killed battery measures the mutants its author thought of.
- **Behaviour the first plan did not specify**: both ends of the diff are pinned (a branch name as
  `base` is refused); every agent call goes through `ask()` so a throw keeps its cause; an empty
  diff is a dead lens, so a sha that does not exist is `VACUOUS`; a high-severity finding a refuter
  dismissed on a guess is a gap and every guess is listed; rulings that are malformed or disagree
  contest their survivor; finding text is fenced as data in the prompts.

**What A2 needs, gathered while building A1:**

1. **The Stop hook's contract, from the hooks reference.** It receives the common fields
   (`session_id`, `transcript_path`, `cwd`, `hook_event_name`, …) plus `stop_hook_active`,
   `last_assistant_message`, `background_tasks` and `session_crons`. It blocks by exiting 2 with the
   reason on stderr, or by printing `{"decision": "block", "reason": "…"}`. **`stop_hook_active` is
   true when Claude is already continuing because of a stop hook: check it, or the hook blocks on a
   condition that cannot resolve.** Claude Code overrides after 8 consecutive continuations and the
   count resets whenever Claude calls a tool (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises it). Project
   hooks live in `.claude/settings.json` and a handler's `timeout` is in seconds (600 by default for
   a command hook). *Not established:* whether a committed hook needs workspace trust before it runs.
2. **`${CLAUDE_PROJECT_DIR}` stays at the original project root in a worktree**, while `cwd` follows
   Claude. A hook command written as `${CLAUDE_PROJECT_DIR}/tools/hooks/…` therefore runs the
   **primary checkout's** copy, not the worktree's: building A2 in a worktree means the hook that
   fires is the old one until A2 lands. Decide the command's path with that in view.
3. **Where the journals are.** On this machine a workflow run writes
   `~/.claude/projects/<project dir>/<session id>/subagents/workflows/wf_<id>/journal.jsonl`, and
   `tools/review_pass_gate.py` already takes `--journal`, `--transcript-dir`, `--list` and `--json`.
   The Stop hook's `transcript_path` and `session_id` should be enough to find the runs of this turn;
   that derivation is A2's to design and to test against a synthetic directory.
4. **The gate has two jobs the hook must not conflate**: `review_pass_gate.py` says whether a run's
   agents all returned (a count from the journal), and the workflow's own `coverage` says whether
   the review was complete. A run can pass the first and be `PARTIAL` on the second.
5. **The smoke run (D3) is on A2's diff**, and § 6.1 is the list of what it must settle. It is a
   multi-agent run the user approved; run it with `args = {sha: <A2's tip>, base: <git merge-base
   origin/main <tip>>, title, claims}`, **before landing A2**, from a directory where
   `git show <sha>:<path>` works.
6. **`.claude/settings.json` is configuration: show its diff and wait for the user's yes.** So is
   the `CLAUDE.md` of A3.

**How to run the gate in this environment** (measured 20261014–19, and in memory): in a Claude Code
shell `PYTHONDONTWRITEBYTECODE=1` is exported and `python3` is the Xcode 3.9, so
`PATH="$PWD/.venv/bin:$PATH" env -u PYTHONDONTWRITEBYTECODE ./check.sh`, with its exit status read
from a log you wrote. In an `EnterWorktree` session the Bash tool refuses compound commands that
mention git: write commit messages to a file and use `git commit -F`, and put multi-step edits in a
script file.

## 9. After A

**Option B — the dogfooding on-ramp (row 21)** is planned next, as the user asked. It is **not
designed yet**: no plan states what the one-command start does, what the checklist checks, or what
"started" means. That plan is written after A lands, not folded into it.
