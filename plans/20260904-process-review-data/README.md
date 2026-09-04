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
| `ci-runs.tsv` | *(coder)* | one CI run | `gh run list` over the whole history, with failing job **and step** |
| `agent_tokens.tsv` | 1,627 | one agent transcript | `tools/agent_spend.py`'s own collector, `--project Pinakes` |
| `agent_tasks.tsv` | 1,631 | one agent, **with the task it was given** | transcript's first user message + `agent_spend` collector |
| `tool_calls.tsv` | 64,662 | one tool call, with a **repeat index** | `tool_use` blocks in every transcript |
| `plan_rows.tsv` | 44 | one build-order row, first seen → first marked done | the live plan at each of 60 commits |
| `sessions.tsv` | 88 | one main-loop session | transcripts, `--project Pinakes` |
| `cross_session_messages.tsv` | 293 | one message received from a peer session | `<cross-session-message from-name=…>` in user turns |

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

**Reading it for repetition:** `SendMessage` and `TaskUpdate` repeats are coordination volume, not
loops — the "same call" is the same recipient. Filter by `tool` before counting.

**`plan_rows.tsv`** — `row` `title` `first_seen` `first_marked_done` `plan_commits_touching_file`.
Done is any of ✅ ⛔ BUILT DONE LANDED SETTLED DEAD appearing in the row's line. **17 of 44 rows
have never been marked done.** Only the live plan's build-order table; other plans are not covered.

**`sessions.tsv`** — one main-loop session: `agent_name` where the transcript records one,
`user_turns`, `cross_session_msgs_in`, `distinct_peers`, `peers`, `compaction_events`, tokens.
**39 of 88 sessions received at least one peer message; 11 recorded a compaction.**

**`cross_session_messages.tsv`** — `timestamp` `to_transcript` `from_name` `chars`. **293 messages.**
Received only — a send is not recorded in the sender's own transcript, so this counts one side.

**`ci-runs.tsv`** — harvested by the coder session; see the header block below, written by them
and pasted here unchanged when it lands.

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

- **CI history** — per-run conclusion, which job failed, time-to-green. The one long-run series
  nobody has; it lives in `gh run list`, not in git.
- **Agent spend by scope** — measured, deliberately not committed to a public repo.
- **Test and battery counts over time** — extractable from the tree, not yet extracted.
