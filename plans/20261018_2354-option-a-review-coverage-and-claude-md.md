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
| **A1** | **Steps 1 and 3**: one committed review workflow. Contract in § 3. | `.claude/workflows/`, `.gitignore`, tests | builder | ✅ **landed `bba0746`, 20261019; CI green on all 16 jobs, `docs` and `injection-audit` too.** Reviewed in three passes (two adversarial, one cold read for the first live run), with fixes after each. **The real fan-out ran 20261019, on A2's diff** (D3; outcomes in § 6.1) |
| **A2** | **Step 2**: a Stop hook that runs `tools/review_pass_gate.py` on the workflow runs of the session that is ending. Contract in § 4. | `tools/hooks/`, `.claude/settings.json` (diff shown first), tests | builder | ✅ **built 20261019 in branch `20261019_0732-a2-stop-hook`**; its merge commit is the one `git log --first-parent --grep a2-stop-hook main` finds. The user approved the exact `settings.json`. The D3 smoke run reviewed it and confirmed 15 findings, all fixed or recorded in § 8. **The hook fired live once, 20261019 09:24 UTC** (the A2 session's report; § 8 open item 1 says what was and was not observed) |
| **A3** | **Row 22**: regenerate `CLAUDE.md`. Method in § 5; outcome in § 5.1. | `CLAUDE.md`, and the docs that receive moved text | planner | ✅ **built 20261019 in branch `20261019_0913-a3-claude-md`**; its merge commit is the one `git log --first-parent --grep a3-claude-md main` finds. The map and the diff were put to the user, and it landed only on their yes (§ 5.1) |
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

## 4. A2 — the hook's contract, as built

- **Event:** `Stop`. Run `tools/review_pass_gate.py` over every workflow run of the session that is
  ending, found from the payload's `transcript_path`
  (`<transcript minus its suffix>/subagents/workflows/wf_*/journal.jsonl`). *(Planned as "a journal
  written this turn"; a Stop payload does not show where a turn began, and § 8 says why a session
  is the better unit.)*
- **Block** the turn from ending while a run is `VACUOUS` (no agent returned anything) or `PARTIAL`
  (some never returned, or returned nothing), **as its journal counts them**, and unacknowledged.
  Acknowledgement is one command, printed in the block message, that writes `gate-acknowledged.json`
  into the run's directory with what the session told the user and the verdict it covers. **Claude
  Code overrides a Stop hook after 8 consecutive blocks** (best-practices page, quoted in the
  artifact § 2), so the hook is a strong nudge and not a lock — the plan states that limit rather
  than discovering it.
- **Never in `check.sh` or CI.** They have no journal and the gate would pass vacuously there.
- **Paths are relative to the project directory.** This repository is public: no `/Users/...`. The
  command in `settings.json` follows the working directory's git top-level, not
  `${CLAUDE_PROJECT_DIR}` (§ 8, open item 4).
- **`.claude/settings.json` is configuration**, so its content was shown to the user, and approved,
  before it was written.

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

**Outcomes — the first live run, `wf_5b3bc97d-245`, 20261019 07:48–08:19 UTC, on A2's tip `a0781ed`
(base `55ac0e7`).** Measured from the run's own journal, its 25 agent transcripts and the result.
Where a line says *seen in other sessions' journals* it is a refuter's reading of data this session
did not re-measure.

| # | Settled |
|---|---|
| 1 | **Yes.** Four lenses and twenty refuters ran on `sonnet`, the judge on `opus` (the agents' `meta.json` says so), and every structured reply used `pattern`, `minLength`, `minItems`, `minimum` and `enum` without a single `died_why`. |
| 2 | **Found by name**: `Workflow({name: "adversarial-review"})` ran the committed file (the runtime's saved copy, `<session>/workflows/scripts/adversarial-review-wf_<id>.js`, is byte-identical to it), and the harness also lists it as a skill. `args` arrived as the object: the lenses checked the `claims`. |
| 3 | **Not exercised here** — nothing died, so nothing was resumed. *Seen in other sessions' journals:* **a resume appends to the same journal in the same run directory, with the same Run ID**; a failed key is started again with a new agent id (`started, failed, started, result`); the runtime's own note says agents whose `(prompt, opts)` are unchanged replay from cache. So the docs' two statements agree: the cache is keyed on the call, not its position. |
| 4 | **Read-only and silent.** 570 tool calls: `Bash` 531, `StructuredOutput` 25, `WebFetch` 6 (the hooks reference), `Read` 3, `ToolSearch` 3, `Skill` 2 (`workflow-authoring`, by two refuters). **No** `SendMessage`, `ListAgents`, `AskUserQuestion`, `Agent`, `Edit` or `Write`; none tried to settle a role. |
| 5 | **Yes, and no collision.** Lenses ran `git worktree add --detach`, `uv sync --frozen`, the 31-mutant battery and the whole of `./check.sh` in scratch worktrees under `mktemp -d` (47 uses), and removed them: no extra worktree, branch or stash was left in the repository. Ten fixed `/tmp` names were used and **each by exactly one agent**. One lens's first `./check.sh` failed two tests because its shell exported `PYTHONDONTWRITEBYTECODE`, as § 7 warns, and it re-ran without. |
| 6 | **25 agents (4 + 20 + 1), 2,978,435 subagent tokens, 570 tool calls, 1,821,671 ms — 30 min 22 s wall.** That is the price of one review pass on a five-file, 1,213-line diff, so it is not a per-commit gate. How long one slow refuter held the judge is **not measured**: the journal carries no timestamps. |
| 7 | **Readable, with one cost.** `coverage` is the first key and the `note` says *NOT a clean pass*; the completion notice truncated the 96 kB result but kept both. The cost: this run was `PARTIAL` with **no lens dead and every agent returned**, because the lenses honestly listed 24 probes they could not run (a live Stop firing among them). An honest `not_run` makes `PARTIAL` the common outcome, and a verdict that is usually `PARTIAL` will be read past. |

**Not on the list, found by the run.** (a) **Fifteen of twenty raised findings were confirmed, three
refuted, two ruled not real**, and two lenses found defects no stub could have: the gate read a
result containing U+2028 as a dead agent, and the battery's 31 kills hid six unpinned behaviours (a
reviewer's own mutants survived). (b) The harness **neutralises subagent output that mentions
`.claude/settings.json`** as *instruction-shaped* (`settings-json`) in eight of the 25 replies —
the content still arrived, but a review of a configuration file will carry that log line. (c) **The
journal and the result are different questions**: this run passed `review_pass_gate.py` (25 of 25
returned) and was `PARTIAL` on `coverage`. The Stop hook sees only the first.

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

## 8. Handover — the state after A2, 20261019

**Written in the branch that records it** ([`docs/BUILDING.md` § Hand over before you
stop](../docs/BUILDING.md#hand-over-before-you-stop)). Of that rule's five places this plan is the
one A2 falsifies: `CLAUDE.md`'s pointer and the routing row name this plan and not an increment,
and `STATUS.md` tracks product surface, which developer tooling does not add. `docs/BUILDING.md`
step 5 now describes the hook.

**State.** A0, A1 and A2 were built; **A3 (regenerating `CLAUDE.md`) has since landed (§ 5.1) and A4
(the release) is not started (§ 10).** Verify what is on `main` with `git ls-remote origin refs/heads/main` and `git log
--first-parent --grep a2-stop-hook main`, not from here. Fragments wait in `changelog.d/` (`ls`
counts them; none is user-visible, there is no release until A4). Development is paused except
for this plan.

**What A2 shipped beside what § 4 asked for**, so the next increment does not rediscover it:

- **"Written this turn" became "this session, unacknowledged".** The hook judges every workflow run
  of the ending session that did not finish cleanly and has no acknowledgement covering it. A turn
  boundary is not visible from a Stop payload, and a run a user was never told about should block
  the next turn too. An acknowledgement ends it for good.
- **An acknowledgement covers a digest of the journal as well as the counts.** A resume appends to
  the same journal in the same run directory, and the gate pairs agents by key, so a counts-only
  fingerprint let one acknowledgement hide every later pass. (Review finding, confirmed.)
- **The hook defers to the payload on whether a run is live**: nothing is judged while
  `background_tasks` lists a workflow; with the list present and no workflow in it, every run is
  judged `--assume-finished`; with the list absent the gate's 180 s window decides.
- **It fails loudly, never as a block**: a bad payload, a crash, or a gate that exits `1` without
  its verdict exits `1` with the cause on stderr, and one run the gate cannot judge does not hide
  a dead run beside it.
- **Agents are named by the label the journal gave them** (`lens:runtime`), not by hex id, and
  `--told` must be a sentence (at least three words, not the placeholder the message prints).
- **The review gate was fixed** (`tools/review_pass_gate.py`): it read a result quoting U+2028 as a
  dead agent. Two tests, fragment `fixed-the-review-gate-read-a-unicode-line-separator…`.
- **The battery more than doubled while it was reviewed.** It was written with 31 mutants, all
  killed; the first review's own mutants left seven alive, and a second, independent reviewer wrote
  82 more and left 28 genuine survivors. Every one is a row now, in the one battery that also
  holds the `settings.json` rows. `grep -c '^\[\[mutant\]\]'` counts them. **A fully killed
  battery measures the mutants its author thought of**, twice over.

**Open, in the order they matter.** None blocks A3.

1. **The hook fired live once, on a planted run.** *Reported by the A2 session, which started a
   fresh session for it; A3 did not observe it.* Observed live 20261019 09:24 UTC from a worktree
   session at `f1804ea`: a planted dead run blocked the turn end and, once acknowledged, the next
   turn end was silent. Earlier (20261019 08:26 UTC) the session that *created* `.claude/settings.json`
   did not pick the hook up, probably because the file did not exist at startup; that was not
   tested. **Not observed:** the real Stop payload, a block while a workflow is in
   `background_tasks`, the 8-block cap, and workspace trust for a committed hook.
2. **The hook counts agents, not coverage.** `coverage: PARTIAL` is not in the journal; the run in
   § 6.1 was `PARTIAL` and passed the hook. Putting it in reach needs the workflow to write its
   result somewhere the hook can read; it is a new increment, not a fix.
3. **The gate counts by journal key.** A key that returned and was later started again without
   returning reads as returned (seen in a real journal: 8 keys, 7 of them `started, result,
   started`). The hook re-judges after a resume but the gate may still say the same thing. What it
   should say is a decision about the runtime's semantics, not a patch.
4. **The command in `settings.json` follows the working directory's git top-level**, so a session
   that `cd`s into another checkout runs that checkout's copy at every Stop, with no prompt. The
   alternative, `${CLAUDE_PROJECT_DIR}`, always runs the original checkout's copy, which defeats a
   worktree. Accepted, and written in the hook's docstring. **In the live check (item 1) the hook ran
   the primary checkout's copy, not the worktree's**: following the git top-level did not follow the
   worktree there. A throwaway hook that prints `pwd` would settle why. *(The A2 session's report.)*
5. **Journals the gate cannot read pass silently.** One with no parseable agent line — the first
   `started` line cut by a kill, or nothing written — is a gate exit `2`, and the hook treats `2` as
   "cannot judge yet". A run whose only agent line was lost is invisible. Not fixed: telling it from
   a run that has not started needs the registry the hook already reads, and the case was not seen.
6. **What "never returned" covers.** Of the 118 journals on this machine when the second review
   counted (it judged them `--assume-finished` after the U+2028 fix: 97 clean, 21 not), the 49
   `failed` events include 44 on agents the gate calls dead. So the message's *never returned*
   includes agents that errored, not only ones cut off by a limit, and the remedy differs: an error
   may recur on a resume. The journal does not say why. Counts are that reviewer's, not re-measured.
7. **Stale text found and left**: `review_pass_gate.py`'s `find_runs` docstring cites
   `test_discovery_finds_a_real_layout`, which does not exist; `tools/review_ledger.py` reads
   transcripts with `splitlines()` (the defect the gate had, not measured there).

**What A3 needs, from this increment.** Nothing new: A3 describes a finished state, and `CLAUDE.md`
should point at this plan's § 8 and not carry the list above. **Do not copy the open items into
`CLAUDE.md`** — they are the most-falsified kind of text there.

**Where the review's artefacts are**, for anyone auditing the 15 findings: the run's journal and
agent transcripts are at `~/.claude/projects/<project slug>/<session>/subagents/workflows/wf_5b3bc97d-245/`,
and its full result is in that session's `tasks/` directory; neither is in the repository.

**How to run things in this environment** (measured 20261014–19, and in memory): in a Claude Code
shell `PYTHONDONTWRITEBYTECODE=1` is exported and `python3` may be the Xcode 3.9 or a 3.15, so
`PATH="$PWD/.venv/bin:$PATH" env -u PYTHONDONTWRITEBYTECODE ./check.sh`, with its exit status read
from a log you wrote. In an `EnterWorktree` session the Bash tool refuses compound commands that
mention git: write commit messages to a file and use `git commit -F`, and put multi-step edits in a
script file.

## 9. After A

**Option B — the dogfooding on-ramp (row 21)** is designed in
[`plans/20261019_0817-option-b-dogfooding-on-ramp.md`](20261019_0817-option-b-dogfooding-on-ramp.md):
design only, the build not resumed. Read that file, not this one, for what it does.
