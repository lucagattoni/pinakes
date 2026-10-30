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
| **A3** | **Row 22**: regenerate `CLAUDE.md`. Method in § 5; outcome in § 5.1. | `CLAUDE.md`, and the docs that receive moved text | planner | ✅ **built 20261019 in branch `20261019_0913-a3-claude-md`**; its merge commit is the one `git log --first-parent --grep a3-claude-md main` finds. The map and the diff were put to the user, who said yes (read 20261019 11:27 UTC); it landed after that as merge commit `e47854c` (§ 5.1). **CI green on all 16 CI jobs and both docs jobs**, each read from its run; `minimum-python` read in its log: CPython 3.13.16, 2794 passed, 126 skipped |
| **A4** | Cut the release that carries A. | `CHANGELOG.md`, version | planner | ✅ **cut 20261019 as 0.32.7**: release commit `d9638c0`, tag `v0.32.7`, on the index 11:44 UTC. `minimum-python` was read in its log before the tag (CPython 3.13.16, 2794 passed, 126 skipped) and the published wheel was read against 0.32.6's: 78 entries, no `tools/` entry, only `__init__.py` and `prices.toml` differ. The sweep landed in its own commit. `CLAUDE.md` and the routing rows were closed after the user said yes to the diff (§ 11) |

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

### 5.1 Outcome — A3, 20261019

**Measured** (`wc -l -w CLAUDE.md`, the instrument of D4): **473 lines / 6,033 words** at `f1804ea` →
**148 lines / 1,497 words** at the A3 merge. Ceiling 150 and 2,700: met. **The aim of about 100 was
not reached**, and the reason is structural, not slack: the file is link-dense — every pointer is at
least one line that wrapping cannot shorten — and what remains is the set the brief names as *keep*.
Getting to about 100 means moving a whole kept section out (candidates, cheapest first: *Changing
retrieval*, *Unbuilt work*'s table, *Tooling*), which is a decision for the user, not a trim.

**The user's yes.** The map above and the diff (`CLAUDE.md` and every other file the change touches)
were put to the user as files, with the measurement and the review summary below; their answer, *yes
to the CLAUDE.md map and diff — land and push A3*, was read at 20261019 11:27 UTC, and nothing landed
before it. The size was put as it stands: 148 lines, not the aim of about 100.

**The map** — every section of the file at `f1804ea`, its outcome, and where its text went. *Moved*
means found at the destination by a whitespace-normalised `grep` (38 checks, all OK; the list is in the message of the commit found by `git log --grep
'every moved fact found at its destination'`; a phrase wrapped across two lines is invisible to a
plain `grep`).

| Section at `f1804ea` | Outcome | Destination |
|---|---|---|
| Intro | **Kept**, plus a size line naming `wc -l -w` | — |
| 🧭 Role first | **Kept**; the 20260823 failure record deleted | `docs/BUILDING.md` § *Settle your role before anything else* already held it |
| 🛑 Land with `land.py` | **Kept**; the three-successful-commands narrative deleted | `docs/RELEASING.md` § *Landing a branch* |
| Working mode (7 bullets) | **Kept** (five after merging two pairs); dates to a provenance comment | handover rule: `docs/BUILDING.md` § *Hand over before you stop* |
| What is live right now (about 250 lines, 9 bullets) | **Rebuilt from the tree** as four pointers | table below |
| This repository is PUBLIC | **Kept** | `docs/INVARIANTS.md` § *The paid path's key is its own* |
| Documentation has one owner | **Kept** (table and propose rule); the *Docs* section folded in as a paragraph | `docs/BUILDING.md` §§ *Proposing…*, *Content mine…* |
| 🚫 Unbuilt work is named | **Kept** (rule and table); the *final cut* clause moved | `docs/README.md` § *Conventions* |
| Naming | **Kept**; the capital-P paragraph folded into its table row | — |
| Invariants | **Folded** into *Building an increment* as one sentence | `docs/INVARIANTS.md` |
| Building an increment | **Kept**; the mutation paragraph moved | `docs/BUILDING.md` step 4; `tools/batteries/README.md` |
| Landing work (6 bullets) | **Kept** as a lead and two bullets; the bump rule and *never lingers in Unreleased* moved | `docs/RELEASING.md` (new paragraph at its head), §§ *Landing beside a peer*, steps 6–7 |
| Tooling | **Folded** into *Building an increment*; *ruff, pyright and pytest before any commit* dropped because `./check.sh` runs them | `docs/BUILDING.md` step 3; `docs/RETROSPECTIVES.md` (the `ty` measurement) |
| Changing retrieval | **Kept** | `docs/DESIGN.md` § 7.3 |
| Docs | **Folded** into *Documentation has one owner* | `docs/README.md` § *Conventions* |

| Old status bullet | Outcome | Destination |
|---|---|---|
| ⏸ Development is paused (analysis, *do not* list, evidence, the lifting of the release hold) | Rebuilt as one pointer | `plans/20260904_1027-…`, **in a note at its top written at A3** — those lines had no other home; the *do not* list is also in this plan's § 1 |
| 🧭 The live build order | Rebuilt as one pointer; the *build order wins* rule kept | `plans/20260901_1148-…` §§ 3–4; the rule is now also `docs/BUILDING.md`'s |
| 🛑 Every release offers to delete a ULID | **Deleted — false**: fixed and published in 0.32.3 | `docs/ROADMAP.md`, `docs/STATUS.md`, `CHANGELOG.md`, live plan row 30; its three lessons in `retro.d/20261019_0934-…` |
| 🚦 0.32.6 is cut | **Deleted — superseded** | `CHANGELOG.md`, `docs/ROADMAP.md`, `docs/STATUS.md`; the *read `minimum-python`* rule is kept in *Landing work* |
| 🛑 Row 31 is not fixed | **Deleted — false**: closed by 0.32.4 (row 37) | live plan rows 31 and 37 |
| 📌 The release timing rule | **Moved** | `docs/RELEASING.md` § *Sweep the three documents* |
| ✅ 0.32.0 | **Moved** | `CHANGELOG.md`; `plans/20260830_0927-…`; `docs/RELEASING.md` § *Before you start* step 3 |
| 🛑 Two plans have scheduled work | **Deleted — superseded**; its owners are in `docs/README.md`'s rows | `plans/20260825_1803-open-decisions.md`, `plans/20260825_1240-run-pinakes-sweep.md`, live plan |
| A status claim is never gated | **Moved** | `docs/BUILDING.md` § *Read the build order out of `plans/`*, third bullet |

**The sweep on the file's own name** (`ROADMAP.md` 0.15.1 records an earlier relocation, 20260806, leaving 21
references to moved text, 13 of them in `src/` and `tests/`, none findable by the moved wording).
`git grep -n "CLAUDE.md"` over the tree, 20261019: **closed plans, `CHANGELOG.md`, `ROADMAP.md`,
`STATUS.md` and `RETROSPECTIVES.md` are dated records and keep the file they described — not
edited.** Live documents, `src/`, `tests/`, `tools/`, CI, `Makefile` and the dotfiles were read
reference by reference against the new text.
- **Caused by A3, fixed:** `docs/README.md` (a routing row said a 🛑 in `CLAUDE.md` held row 30; one row
  needed the A3 status), `docs/RELEASING.md` (one phrase about `CLAUDE.md`'s live rows), the option B
  plan (three citations, one of them a figure — the 126 skipped now cited at `docs/ROADMAP.md`), live
  plan row 22. No `src/` or `tests/` reference now dangles because of A3: the sections they cite
  (*Changing retrieval*, *This repository is PUBLIC*, the key rule's wording, the UTC rule,
  *Documentation has one owner*, *Landing work*) kept their names and text.
- **Already dangling before A3 — found, not caused, not touched** (code comments are the
  implementer's, and the user confirmed this session as planner only). Proposed as a diff against
  `f1804ea` for whichever implementer next holds these files: `tools/review_pass_gate.py:68` and
  `tools/review_ledger.py:65` cite a `CLAUDE.md` § on exit status that was extracted to
  `docs/BUILDING.md` step 3 (the new *Building an increment* paragraph restores the rule in
  `CLAUDE.md` itself); `.github/workflows/injection-audit.yml:116` the same; `tools/land.py:215`,
  `tools/mutate.py:560` cite rules that live in `~/.claude/CLAUDE.md`; `tools/batteries/README.md:253`
  cites *commit before mutating*, which is `docs/BUILDING.md` step 4; `src/pinakes/paid.py:41` cites
  *a deliberate act*, which is `docs/INVARIANTS.md`; `.paid-path-allowlist:17` cites a
  `CLAUDE.md` allowlist that is `docs/INVARIANTS.md`'s; `.gitignore:31` cites a "primary check" that is
  `~/.claude/CLAUDE.md`'s; and `Makefile:105`, `tests/test_release_tag_gate.py:159` and
  `tools/batteries/tools-release_tag_gate.toml:116` quote *before the tag, never after* where the file
  says *before the push*.
- **Pointers to `~/.claude/CLAUDE.md` (five at `f1804ea`, added 20260915) were dropped.** That file is
  machine-local, so a public file naming it helped no cloud run or other clone; the regenerated file
  keeps only this repository's rules. `tools/land.py:215` and `tools/mutate.py:560` cite rules that
  live there (listed above); the pending 20260915 changelog fragment says `CLAUDE.md` names it, and
  A3's own fragment now says the pointers are gone.
- **No test reads `CLAUDE.md`'s sentences.** The gates that read the file: `tools/markdown_link_gate.py`
  (links and anchors; every one resolves), `tools/shared_file_overlap.py` (the filename in a hotspot
  list), `tests/test_markdown_link_gate.py` (the slugifier over every heading in the repository).
  `tests/test_docs_quote_the_shipped_sentences.py` searches `docs/`, `README.md` and `src/`, not this file.

**Review.** Round 1 — a read-only Sonnet reviewer, question *what does a cleared session do wrong with
the new file* (it read the file cold first, then the old one, then followed every pointer): ten
findings, nine acted on in `d026fa4`. The two that mattered: **the lifting of the release hold had
no source outside the file being deleted**, so the pause handover said a release was due while
`CLAUDE.md` said releases were free — it is now a note at the top of the pause handover; and **the
handover-versus-ownership contradiction, which the old file resolved in six words, had lost them**
— restored. Also restored: the bump rule (now in `docs/RELEASING.md`, whose header claimed
`CLAUDE.md` held it), *needing an answer to proceed is the bar for asking*, the invariants list,
and the right link for *ask, do not draft*. Not acted on: *A0–A3 landed* and the user's yes, true
only at landing. Round 2 — a second read-only Sonnet reviewer, on the questions *does every moved fact exist at its
destination* and *what pointer now dangles* (24 of 24 map rows, every link and anchor, and every
non-record hit of the file's name): no row not found, and both *false* bullets confirmed false from
the tagged sources (`934190c` is an ancestor of `v0.32.3` and not of `v0.32.2`). Eight findings, all
acted on or recorded: open live-plan row 24 and built rows 26 and 38–41 and 43 cited `CLAUDE.md` for
text that had moved (now one dated note at the head of that plan's § 3); *ruff, pyright and pytest
before any commit* had no map row (`./check.sh` runs them); *seven rules* had become unverifiable
(the count is gone); the *§ 8 handover* pointer led to A2's (now §§ 8 and 10); `docs/BUILDING.md`
said *two rules* over three bullets and `docs/RELEASING.md` named `CLAUDE.md` as the home of a rule
it had just stated; this map said *six* bullets for five; and the interpreter-pinning instruction
had no procedure home (now `docs/BUILDING.md` step 3).

**Not done, and recommended.** (a) **A size guard.** Three passes grew back; the new file says it
stays under 150 lines and 2,700 words and nothing enforces it. A test that counts both, excluding
own-line comments as the hygiene rule does, is a small implementer increment — and a new row, so it
waits for the pause. *(Closed 20261019 13:10 UTC: the guard landed in 123bff2 and counts own-line comments, which this paragraph said to exclude; § 10 item 1.)* (b) The leftovers above.

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

## 10. Handover — the state after A3, 20261019

**Written in the branch that records it** ([`docs/BUILDING.md` § Hand over before you
stop](../docs/BUILDING.md#hand-over-before-you-stop)). Of that rule's five places, A3 changed three:
`CLAUDE.md`'s pointer block (rebuilt, and the place a cleared session reads *A0–A3 landed, A4
remains*), this plan's § 2 rows, and `docs/README.md`'s routing rows. `docs/STATUS.md` tracks product
surface, which a documentation-only increment does not add.

**State.** A0 to A3 are landed. **A4 — cut the PATCH release carrying A (D5) — is the only increment
left, it is the planner's, and it has not started.** Verify with `git ls-remote origin
refs/heads/main` and `git log --first-parent --grep a3-claude-md main`, not from here. Development
stays paused except for this plan; option B is designed and its build is not resumed (§ 9).

**What A4 needs, from A3.**

- **Fragments wait in `changelog.d/` and `retro.d/`** — count them with `ls`. A3 added one of each
  (`…changed-claude-md-status-block-became-pointers`, `a3-what-the-status-block-held-…`). The
  retrospective one carries three lessons that had no other home; it is spliced into
  `docs/RETROSPECTIVES.md` at the cut, so read it there afterwards.
- **A PATCH, on the 0.32.6 precedent** (developer tooling and instructions, nothing a wheel ships).
  `docs/RELEASING.md` is the procedure; step 3 refreshes `prices.toml`'s `usd_per_eur` from a named FX
  source at every release, and step 6 reads `minimum-python` in the CI run for the commit being tagged.
- **Changes `CLAUDE.md` in two bullets:** the option A bullet says *A0–A3 landed; A4 … remains*, and
  the pause bullet says *except option A*. When A4 lands the first becomes a statement that option A
  is complete and the second goes with it — **a planner edit with the diff shown to the user first**,
  like A3. The file is close to its line ceiling (see § 5.1), so the edit displaces text rather than adds.
- **`docs/README.md`'s option A row** says A3 is built; A4 turns it to done. The A3 landing did not
  touch the live plan's other rows.

**Open, none blocking A4.**

1. **The size is unguarded.** § 5.1: nothing enforces 150 lines and 2,700 words, which is how three
   earlier passes grew back. A test is a small implementer increment and a new row, so it waits for the pause. *(Closed 20261019 13:10 UTC in 123bff2: `tools/claude_md_size_gate.py` and `tests/test_claude_md_size.py` count own-line comments, where this item recommended excluding them.)*
2. **Twelve citations of moved or global text** in `tools/`, `src/`, `tests/`, `.github/`, `Makefile`,
   `.gitignore` and `.paid-path-allowlist` were dangling before A3 and still are (§ 5.1 lists each). Code comments
   are the implementer's; they were not touched.
3. **The template release row.** `CLAUDE.md`'s row now says what is unbuilt — the `sqlite-vec` tier —
   because the template ecosystem and `pnk upgrade` have shipped (`docs/STATUS.md`, 0.19.0 to 0.21.0). The same
   table is copied at `docs/STATUS.md:316` and described in `docs/README.md` § *Conventions* the old
   way, and whether the name should have left the table at 0.22.0 is a planner decision this increment did not take. *(Closed the user, 20261030, before 19:40 UTC: 0.22.0 was ruled the final cut; the row is now *the `sqlite-vec` tier, staged*.)*
4. **The aim of about 100 lines was not reached** (§ 5.1). It needs a kept section moved out, which
   is the user's decision.

## 11. Handover — option A is complete, 20261019

**Written in the branch that records it** ([`docs/BUILDING.md` § Hand over before you
stop](../docs/BUILDING.md#hand-over-before-you-stop)). **State.** A0 to A4 are landed and 0.32.7 is
published; verify with `git ls-remote --tags origin v0.32.7` and `git log --first-parent main`, not from
here. **Development is paused again with no exception**: option A was the pause's one. The cut
emptied `changelog.d/` and `retro.d/`.

**What the cut found, for whoever cuts the next one.** (1) `uvx --from "pinakes[light]"` did not
resolve on a machine whose newest interpreter is CPython 3.15, because `onnxruntime` has no `cp315`
wheel; it worked with `--python 3.13`. (2) The price table was 44 days old when the cut began, so a
fresh install of 0.32.6 showed `WARN price table`; the cut re-stamped it, and it will go stale again
30 days after any release. (3) A `gh run watch` that exits 1 with *can't assign requested address* is a
local network error, not a CI failure: ask `gh run view <id> --json status,conclusion,jobs`.

**What is open, and whose it is.** The user's three option B decisions, in
[`plans/20261019_0817-option-b-dogfooding-on-ramp.md`](20261019_0817-option-b-dogfooding-on-ramp.md) § 9;
the open items of § 8 and § 10 above, none of which blocked the release; and every other row of the
live plan, which resumes only on the user's word. **This plan has no increment left.**
