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

**`ci-runs.tsv`** — harvested by the coder session; see the header block below, written by them
and pasted here unchanged when it lands.

## Reproducing

Every file was produced by a short script over `git log` / `git tag` / `git show` in this
repository. **The commands are in the commit that added this directory**, so a reader can re-run
them rather than trust the output.

## What is NOT in here, and would need a separate harvest

- **CI history** — per-run conclusion, which job failed, time-to-green. The one long-run series
  nobody has; it lives in `gh run list`, not in git.
- **Agent spend by scope** — measured, deliberately not committed to a public repo.
- **Test and battery counts over time** — extractable from the tree, not yet extracted.
