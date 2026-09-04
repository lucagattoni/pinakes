# Process-review data — harvested 20260904 10:44 UTC

**Raw records for the user's review of how Pinakes development is done. Collected, not analysed.**
Every file is derived from this repository's own git history and committed documents. **No
interpretation is offered here** — the columns are the artefacts' own fields.

**Why this exists.** Development was paused so the process could be reviewed against
*Framing, Not Roles* (artifact `2c7961ec`). The user asked for the data rather than a reading of
it: *"you have just to collect the data, no data analysis from your side"* and *"you have to collect
the RIGHT data, filtering the noise"*, with an emphasis on **long-run trends**.

**Scope and exclusions, stated so a null is readable.** These cover the repository only. **Agent
spend is deliberately absent** — it is the author's own project spend and this repo is public;
ask for it separately. Nothing here was sampled: each file is the complete population its header
describes.

| file | rows | one row is | instrument |
|---|---:|---|---|
| `retrospectives.tsv` | 195 | one retrospective entry | `docs/RETROSPECTIVES.md`, 12,029 lines, 208 `## ` headings — 195 parsed as stamped entries |
| `commits.tsv` | 1,086 | one non-merge commit | `git log --no-merges --numstat` over all history |
| `fragments.tsv` | 346 | one `changelog.d/`/`retro.d/` fragment | add→delete pairing by path over all history |
| `releases.tsv` | 64 | one release tag | `git tag` with creator date and subject |
| `claudemd_size.tsv` | 150 | one commit that touched `CLAUDE.md` | line count of the file at that commit |
| `daily_tree.tsv` | 29 | one **day** | the tree at the last commit of each day |
| `tree_growth.tsv` | 212 | one **change** in the file counts | `git ls-tree` at every commit; rows emitted only when a count moves |
| `ci-runs.tsv` | 793 | one CI run | `gh run list` + one `gh run view --json jobs` per non-success run |
| `agent_tokens.tsv` | 1,627 | one agent transcript | `tools/agent_spend.py`'s own collector, `--project Pinakes` |
| `agent_tasks.tsv` | 1,631 | one agent, **with the task it was given** | transcript's first user message + `agent_spend` collector |
| `tool_calls.tsv` | 64,662 | one tool call, with a **repeat index** | `tool_use` blocks in every transcript |
| `plan_rows.tsv` | 44 | one build-order row, first seen → first marked done | the live plan at each of 60 commits |
| `sessions.tsv` | 88 | one main-loop session | transcripts, `--project Pinakes` |
| `cross_session_messages.tsv` | 293 | one message received from a peer session | `<cross-session-message from-name=…>` in user turns |
| `commit_sessions.tsv` | 1,096 | one commit, with the **session that made it** | `Claude-Session` git trailer + `--numstat` |
| `session_id_bridge.tsv` | 115 | one (transcript, session-token) pair | `session_XXX` tokens found inside each transcript |

## Noise filtering — what was removed, and why

- **Merge commits excluded** from `commits.tsv`. They carry no authored change and would double
  every landing.
- **Generated and vendored paths excluded** from churn: `site/` (the built docs site), `uv.lock`,
  and binary assets. These swamp line counts without carrying authored signal.
- **`README.md` fragments excluded** from `fragments.tsv` — the two directory READMEs are
  permanent, not fragments, and would never pair.
- **Nothing else was dropped.** No date range, no author filter, no size threshold.

## Columns

**`retrospectives.tsv`** — `date` `time` `title` `severity` `claim` `lesson` `lines`
Severity is the entry's **own** `**HIGH|MEDIUM|LOW|CRITICAL**` token where it has one — **130 of
195 do**; the rest are blank rather than guessed. `claim` is the entry's first bold sentence.
`lesson` is the `Lesson:` line where present — **39 of 195**. `lines` is the entry's length.
**Known limit:** 13 of the 208 headings did not match the stamped form and are absent; the parser
required `## <title> (<YYYYMMDD[ HH:MM]>)`.

**`commits.tsv`** — `sha` `iso` `subject` then **lines changed (added+deleted) per area**:
`src` `tests` `tools` `ci` `docs` `plans` `frag` `claudemd` `changelog`, and
`files` (count of non-noise files touched). A commit touching only excluded paths is omitted.

**`fragments.tsv`** — `path` `stream` `added` `deleted` `hours`. `hours` is lifetime
add→delete; blank means still present. **332 of 346 paired**; unpaired are renames, which mis-pair
by path string, plus those still on disk.

**`releases.tsv`** — `iso` `tag` `subject`.

**`claudemd_size.tsv`** — `iso` `sha` `lines`, oldest first.

**`daily_tree.tsv`** — `date` `sha` `test_functions` `test_files` `src_lines` `docs_lines`
`battery_files`. A snapshot of the tree at the **last commit of each day**, 29 days. `test_functions` counts `def test_` across `tests/**.py`; `src_lines` and `docs_lines` are raw
line counts of `src/**.py` and `docs/**.md`. **Days with no commit are absent, not zero.**

**`tree_growth.tsv`** — `iso` `sha` `test_files` `battery_files` `tools_py`. One row per **change**
in those three counts rather than per commit, so the file is a step function and consecutive rows
are never equal.

**`agent_tokens.tsv`** — `scope` `transcript` `workflow_run` `first` `last` `requests`
`dominant_model` `models` `input_tokens` `cache_write_tokens` `cache_read_tokens` `output_tokens`
`context_tokens` `sidechain_requests` `full_rewrites`. **Tokens only — no money, at the user's
instruction.** Built by importing `tools/agent_spend.py` and calling its own `read_requests`, so
the two documented traps are handled by the instrument that documents them: **one API response is
written as several transcript lines sharing a `requestId`** (summing per line inflates by 2.14×),
and **`output_tokens` is a running partial** (take the max, never the first).
**Population: `--project Pinakes` only.** Figures taken without that filter count every project on
the machine and are roughly 2× the main-loop count — an error made and corrected in this harvest.
**Transcripts with zero parsed requests are omitted**, which is why this file has 1,627 rows
where `agent_spend.py` reports 1,677 transcripts.

**`agent_tasks.tsv`** — as `agent_tokens.tsv` plus `task_prompt` (first user message, 300 chars),
`duration_s`, `start`, `end`, `tool_calls`, `distinct_tools`, `distinct_targets`.

**`tool_calls.tsv`** — `scope` `transcript` `seq` `timestamp` `tool` `target` `call_hash`
`repeat_index`. **`repeat_index` counts identical calls**: same tool and same *whole* normalised
argument, keyed on `call_hash`, 0 on first use. **4,197 of 64,735 calls (6.5%) are repeats; 1,764
are the same call made five or more times in one transcript.**

> ⚠️ **This column was wrong twice before it was right, and the corrections are the useful part.**
> **v1** keyed on the argument truncated to 120 characters, so every Bash call collapsed onto its
> `cd <worktree> &&` prefix: it reported **18,573 repeats**, of which **8,800 — 47% — were that
> prefix**, not a repeated command. **v2** stripped leading `cd` chains and reported **12,853**,
> still dominated by `VAR=…` assignment preambles. **v3, current**, hashes the entire normalised
> command. **A truncated prefix cannot identify a shell command**, and the first two versions
> measured the working directory. Corrected 20260904 11:30; `target` is now the command's first two words
> for Bash and the full argument for every other tool, and is a *label*, not the identity.

**⚠️ Do not count instrument use from this file.** `target` is a label, and a Bash invocation
inside an `&&` chain is one call here but several invocations in the transcript. ⟦coder,
measured⟧ counting `check.sh` from `tool_calls.tsv` gives **64** where the transcripts hold
**157–229** depending on how strictly an invocation is defined — an undercount of ~3.6×.

**Reading it for repetition:** `SendMessage` and `TaskUpdate` repeats are coordination volume, not
loops — the "same call" is the same recipient. Filter by `tool` before counting.

**`plan_rows.tsv`** — `row` `title` `first_seen` `first_marked_done` `plan_commits_touching_file`.
Done is any of ✅ ⛔ BUILT DONE LANDED SETTLED DEAD appearing in the row's line. **17 of 44 rows
have never been marked done.** Only the live plan's build-order table; other plans are not covered.

**`sessions.tsv`** — one main-loop session, **regenerated 20260904 11:47** with three additions:
`role`, `session_id`, and an active/idle split. Columns: `transcript` `session_id` `agent_name`
`role` `start` `end` `span_s` `requests` `user_turns` `active_s` `idle_gt120_s` `median_gap_s`
`cross_session_msgs_in` `peers` `compaction_events` and the token columns.
**`role`** is taken from the transcript's `agent-name` line or from a literal *“you are the
planner/coder”* in a user turn — **11 planner, 14 coder, 63 unlabelled.** The unlabelled are not
roleless; the label simply is not in the transcript.
**`active_s` / `idle_gt120_s`** split the sum of inter-request gaps at **120 seconds** — an
arbitrary cut, stated so it can be changed; `median_gap_s` is given so you can pick your own.
Across all 88: **418,444 s under the cut, 2,440,667 s over it.** A gap over the cut is *elapsed
time between requests*, which includes the user thinking, a peer being waited on, and the session
sitting idle — **it is not attributable to any one of those from this data.**
**39 of 88 sessions received at least one peer message; 11 recorded a compaction.**

**`commit_sessions.tsv`** — every non-merge commit with its `Claude-Session` trailer and its
per-area churn. **848 of 1,096 commits carry a session id, across 40 distinct sessions.** The 248
without one predate the trailer or were made outside a session.

**`session_id_bridge.tsv`** — ⚠️ **the two identifier spaces do not join directly.** A commit
trailer names `session_01Xxx…`; a transcript's own `sessionId` is a UUID. **Overlap between them
is zero.** This file is the bridge: each transcript is scanned for `session_XXX` tokens appearing
anywhere in it, with `occurrences` and `is_most_frequent`. **39 of the 40 trailer ids appear in
some transcript**; 56 transcripts carry at least one token and **37 carry exactly one**, which are
the unambiguous ones. **A transcript can carry several tokens** — its own attribution plus any it
quotes from a peer message — so **`is_most_frequent` is a hint, not an identity**, and the
attribution is left to the analyst rather than guessed here.
**⟦coder, measured 20260904 12:10⟧ The analyst's rule can now be stated: a trailer id names a LINEAGE,
never a session.** `/clear` destroys the context and **preserves the session id**, so three
transcripts — two context deaths — carry one token and stamp 35 commits between them. One of
the three carries exactly one distinct token, so it cannot be quotation from a peer.

**`cross_session_messages.tsv`** — `timestamp` `to_transcript` `from_name` `chars`. **293 messages.**
Received only — a send is not recorded in the sender's own transcript, so this counts one side.

**`ci-runs.tsv`** — `created_at_utc` `run_id` `attempt` `workflow` `branch` `sha` `event` `status`
`conclusion` `started_at_utc` `updated_at_utc` `duration_s` `failed_jobs` `failed_steps` `title`.
Oldest first. Multi-valued cells use `|`.

**Instrument.** `gh run list --limit 1000 --json databaseId,workflowName,name,headBranch,headSha,event,status,conclusion,createdAt,startedAt,updatedAt,displayTitle,attempt`,
plus one `gh run view <run_id> --json jobs` per non-success run. Collected 20260904 10:53–10:54 UTC.

**Population.** All **793** workflow runs the API reports for this repository — every ref, every
workflow, whole history, 20260725 13:28 to 20260904 10:46 UTC. `--limit 1000` exceeds 793, so this
is the complete set rather than a page, and `GET /actions/runs` reports `total_count` 793 by a
differently-shaped instrument. **680 success, 93 cancelled, 20 failure.** Job and step lookups were
performed for all 113 non-success runs and all 113 returned — none silently empty. By workflow: CI
507, docs 221, Release 63, injection-audit 2. **Every run's `event` is `push`**; the column is
constant and is kept because that constancy is itself a fact about this repository.

**Every field is copied from the payload**, with two exceptions stated so they can be undone: `sha`
is truncated to 12 characters, and `duration_s` is the only arithmetic — `updatedAt − startedAt`,
both operands present on all 793 rows, so it can be recomputed or discarded.

**Filtering decision 1 — cancelled runs are KEPT** (93 of 793). Supersession by a newer push and a
genuine abort are indistinguishable from the run row, so dropping them would silently delete every
superseded run of a concurrency-cancelled workflow. The drop is the analyst's to make, with the
count visible.

**Filtering decision 2 — failing steps are collected, not only failing jobs**, as `job::step`.
*"check failed"* is a weak record; *"check (light)::Tests failed"* is attributable to a gate.

**Filtering decision 3 — a failing job is recorded wherever it occurs, not only under a failed
run.** A job whose own `conclusion` is `failure` is collected even when the run concluded
`cancelled`. Not hypothetical: **23 rows carry a failing job — the 20 failures plus 3 cancelled
runs**, and those three would otherwise have read as empty.

**Deliberately absent.** No time-to-green, no red-streak reconstruction, no per-gate rates, no
percentages, no commentary.

**Known limits.**

- **Earlier attempts are absent.** `gh run list` returns **one row per run** carrying that run's
  latest `attempt`; a re-run replaces rather than adds. Three runs sit at `attempt` 2, so at least
  three earlier attempts exist that this file does not contain and whose conclusions are not
  recoverable from it. *(An earlier draft of this header claimed the opposite — that re-runs are not
  deduplicated and each attempt is its own row. They are: 793 rows carry 793 distinct run ids.)*
  **On those three rows the timestamps are mixed**: `created_at_utc` is the original attempt's
  trigger time, while `started_at_utc`, `updated_at_utc` and `duration_s` describe attempt 2 — gaps
  of 469, 1054 and 1516 seconds. `duration_s` stays correct as `updated − started`; **do not read
  `started_at − created_at` as queue time on these three rows.** They are the only three rows in
  793 where that subtraction is non-zero.
- **`duration_s` includes in-run queue time** and is not billed minutes.
- **A run's `conclusion` is the run's, not any job's** — which is what filtering decision 3 exists
  to survive.
- **A ref can exist with zero runs, and this file cannot tell you why.** `v0.1.0` — a real
  published release, annotated tag 20260727 12:39:42 UTC, release published 12:40:02 — has **no row
  here**, and the `Release` workflow's history in this dataset begins at `v0.1.1`. The workflow
  existed and was armed at that tag (`release.yml` was added in the very commit `v0.1.0` names).
  **Why it never ran is not established by this extraction, and no mechanism is offered** — the
  obvious explanation, that the tag was made through the Releases API rather than a push, is
  refuted by `v0.1.1`–`v0.1.4`, which share its provenance and fired anyway. **Absence of a row is
  not evidence a check passed.**
- **Runs aged out of GitHub's retention are absent**, and this extraction cannot say whether any
  were. The earliest row is 20260725, the repository's first day of CI.
- **`branch` is whatever ref the run carried**, so the 63 `Release` runs name a tag (`v0.1.1`) and
  not a branch. 730 of the 793 rows are `main`.

**`FRAMEWORK.md` sits beside these files** — how development here actually works, what the data
can and cannot answer, and the two sessions' accounts where they disagree. **It characterises and
does not prescribe**, at the user's instruction. Read it after the data, not instead of it.

## The two questions this harvest was steered to answer

**Added 20260904 11:10 at the user's direction.** These are *pointers to columns*, not findings.

**1. Where tokens and time went, per task and subtask.**
`agent_tasks.tsv` carries one row per agent with **the prompt it was given** (`task_prompt`),
its `duration_s`, and its token columns — so spend groups by the task rather than by the file it
happens to live in. `sessions.tsv` does the same for resident main-loop sessions.
**`context_tokens` is the column to watch**: it is what the model was *sent*, re-transmitted every
turn, and it runs two orders of magnitude above `output_tokens`.

**2. Where an agent looped for little return.**
`tool_calls.tsv` has `repeat_index` — how many times that **exact tool + target** had already been
called in the same transcript, 0 on first use. **18,573 of 64,662 calls have `repeat_index >= 1`.**
Join it to `agent_tasks.tsv` on `transcript` to put repetition beside the task and its cost.
`agent_tasks.tsv` also carries `tool_calls`, `distinct_tools` and `distinct_targets`, so the ratio
of calls to distinct targets is available without touching the per-call file.

**What is deliberately not computed here:** no rates, no thresholds, no "wasteful" flag. Whether a
repeat is waste depends on what the agent was doing between the calls, and that is a reading.

## Reproducing

Every file was produced by a short script over `git log` / `git tag` / `git show` in this
repository. **The commands are in the commit that added this directory**, so a reader can re-run
them rather than trust the output.

## What is NOT in here, and would need a separate harvest

- **Time-to-green and red-streak length.** Per-run conclusions and failing jobs *are* now in
  `ci-runs.tsv`; what stays out is any reconstruction across runs, because deciding whether a
  `cancelled` run breaks a streak is a reading, not a record.
- **Agent spend by scope** — measured, deliberately not committed to a public repo.
- **Test and battery counts over time** — extractable from the tree, not yet extracted.
