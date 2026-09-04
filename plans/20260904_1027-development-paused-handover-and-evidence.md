# Development paused — handover, state, and evidence for the next approach

**Written 20260904 10:27 UTC by the planner session, at the user's instruction, as both sessions shut down.**
Paired with a `retro.d/` fragment from the coder session covering the implementer's side.

**Why this file exists.** The user paused Pinakes development to review **the development process
itself** against an analysis they commissioned — *Framing, Not Roles* (Claude artifact
`2c7961ec`, written 20260903 against `d474ffa`). Their instruction: *"all the situation and the
state of the project development should be on disk and immediately being ready to take over any
time. No ambiguities. So the development can restart anytime from where you both left."*

**This file is the entry point for whoever resumes.** `CLAUDE.md` points here.

---

## 1. How to resume, exactly

1. `git fetch && git status` — expect `main` at `7b079e54a26ff432feb3097018a6e41441554a53`, clean, in sync.
2. Read `CLAUDE.md`'s **⏸ DEVELOPMENT IS PAUSED** bullet, then § 2 below.
3. **Ask the user whether the pause is lifted.** Do not pick up a row on your own judgement — the
   thing under review is the process that would tell you which row to pick.
4. If lifted: § 5 lists what is open, with the one decision each carries.

**The evidence the user asked for is `plans/20260904-process-review-data/` — 16 TSV datasets plus
three documents.** `README.md` there gives each file's instrument, population and noise filter;
`METHOD.md` says how the transcript data was extracted and lists the traps; `FRAMEWORK.md` is the
two sessions' account of how development here actually works, including **§ 9's audit of which
written rules are actually followed**. **Read `README.md` before any TSV** — several columns mean
something narrower than their name suggests.

**This pointer was missing until 20260904 14:27**, from this file and from `CLAUDE.md` both, for the
two hours after the harvest landed. The directory existed, was complete and was reachable from
neither entry point a resuming session reads — which is this file's own stated purpose failing in
the specific way `CLAUDE.md` warns about: *the entry points that survive are exactly the ones a
session's own work tends to falsify.*

**Nothing is half-built and nothing is waiting on a timer.** No background task, no monitor, no
scheduled job. Both sessions ended by choice, not by limit.

---

## 2. State at the pause — verifiable, not remembered

| | |
|---|---|
| `origin/main` | `e8d91f24922ad400af67afef4ab742f01ea9226d` (20260904 14:27) — primary checkout in sync, **no worktrees**. Was `7b079e5` when this file was written at 10:27; four documentation landings followed, the last being `FRAMEWORK.md` § 9 |
| Published | **0.32.5** on PyPI, verified from the index with a control that discriminates the fix |
| Fragments waiting | **8** — 2 in `changelog.d/`, 6 in `retro.d/` — **a release is due and was deliberately not cut**. **Count this from disk, never from this cell**: it read **6** from 10:27 until 14:27 while two more landed |
| Increments landed 20260903–04 | rows 7, 8, 30, 31, 32, 38, 39, 40, 41, 43 · releases 0.32.2 → 0.32.5 |
| In flight at the pause | row 42 (coder) — see its fragment and the row for exact state |

**Why the release was not cut.** A tag publishes to PyPI and PyPI never accepts a version twice.
Publishing is *starting* work, not stopping it — and the release procedure is itself inside the
scope of the review. **The waiting fragments are a normal resting state**, not an omission. Whoever
resumes cuts 0.32.6 when the process question is settled — and **reads `minimum-python`'s conclusion
in the CI run for the commit being tagged** first, per `docs/RELEASING.md` step 6.

*(That paragraph said "the six fragments" until 14:27. A count written into prose ages exactly like a
count written into a table, and prose has no column to check. This is the same defect
`docs/ROADMAP.md`'s three registers carry, one document over.)*

---

## 3. Evidence — long-run trends first

**Measured 20260904 on the tree at `c281463`. Every figure names its instrument. Nothing here is
quoted from a docstring.**

### 3.1 The long-run trend: `src/` churn collapsed while prose and retrospectives grew

| ISO week | commits | `src/` | code | prose | prose % | retro frags | releases |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-W30 | 51 | 5,893 | 10,404 | 7,596 | 42.2% | 0 | 0 |
| 2026-W31 | 231 | 14,959 | 43,798 | 31,480 | 41.8% | 15 | 15 |
| 2026-W32 | 206 | 6,558 | 27,155 | 23,877 | 46.8% | 35 | 16 |
| 2026-W33 | 84 | 5,080 | 12,091 | 6,584 | 35.3% | 9 | 7 |
| 2026-W34 | 124 | **593** | 14,282 | 8,188 | 36.4% | 12 | 16 |
| 2026-W35 | 152 | 1,156 | 8,026 | 12,264 | **60.4%** | 26 | 3 |
| 2026-W36 *(4 days)* | 235 | 2,012 | 11,686 | 15,738 | **57.4%** | **63** | 7 |

<sub>Instrument: `git log --no-merges --numstat` over all history, bucketed by `%G-W%V`. code =
`src/ tests/ tools/ .github/`; prose = everything else. Line churn overweights prose-heavy files —
used deliberately, because commit counts overweight the one-commit-per-review-pass habit.</sub>

**Three trends, and they point the same way.**

1. **`src/` churn fell about tenfold** — 5.9k–15k lines/week in W30–W33, then 593 / 1,156 / 2,012.
   Maturation explains part of it. It does not obviously explain all of it.
2. **Prose became the majority of churn** in the last two weeks — 42% early, **60.4%** and **57.4%**
   now. The project writes more about its work than it changes.
3. **Retrospective fragments grew fastest of anything** — 0 → 15 → 35 → 9 → 12 → 26 → **63 in four
   days**. W36 alone has more retrospectives than any complete week in the project's life.

**The honest counterweight, stated because it cuts against the conclusion:** in *this* two-day
window code was **49.3%** of churn (`src/` 1,568, `tests/` 2,532, `tools/` 1,659 against 5,963 of
prose). This window built more than the trend suggests. The trend is still down.

### 3.2 `CLAUDE.md` grew fastest when it was most criticised

| date | lines |
|---|---:|
| 20260725 | 76 |
| 20260731 | 225 |
| 20260826 | 276 |
| 20260902 | 321 |
| 20260903 *(the analysis calls it too long, quoting the official "bloated CLAUDE.md" guidance)* | 410 |
| **20260904** | **455** |

<sub>Instrument: line count at the last commit of each day the file changed; **150 commits** have
touched it.</sub>

**+42% in the two days after it was named as a defect, and this planner wrote nearly all of it.**
Against a target of under 100 lines, the file is at **455**. **The mechanism is the analysis's own
diagnosis demonstrating itself:** with no hooks and no agent definitions, prose is the only
substrate available, so every lesson becomes another paragraph in the file already too long to read.

### 3.3 Where the tokens are — **corrected 20260904 10:59: my first figures were the wrong population**

**Pinakes only** (`--project Pinakes`), tokens only, no money:

| scope | transcripts | requests | output tokens | context tokens (input + cache) |
|---|---:|---:|---:|---:|
| main loop (resident sessions) | 131 | 20,522 | 19,924,499 | **5,382,856,712** |
| subagents | 106 | 6,428 | 5,184,831 | 1,018,135,108 |
| workflow agents | 1,440 | 28,946 | 18,511,665 | 2,561,587,703 |

<sub>Instrument: `tools/agent_spend.py` with `--project Pinakes`, and `agent_tokens.tsv` in the data
directory for the per-transcript rows. **Context tokens are what the model was *sent*** — the number
re-transmitted on every turn — and they dominate output by two orders of magnitude.</sub>

**The correction, recorded rather than quietly fixed.** My first version of this section reported
**261 / 125 / 1,466 transcripts with dollar figures**. Those came from `agent_spend.py` run **without
`--project`**, so they counted **every project on this machine**, not Pinakes. The true Pinakes
main-loop population is **131 transcripts, not 261** — roughly half. **A ratio computed over the
wrong population is the failure this whole review is about, and I committed it inside the evidence
file for the review.** The dollar figures are gone at the user's instruction: **tokens only.**

**What survives the correction:** resident main-loop sessions are **7.8%** of Pinakes transcripts
(131 of 1,677) and carry **59.9%** of context tokens (5.38B of 8.96B). The shape of the earlier
claim holds; its numbers did not.

### 3.4 Review efficacy — two independent runs, and neither gives a kill rate

| | this session's floor audit | the coder's row-42 fan-out |
|---|---|---|
| agents | 14 (5 lenses + 8 refuters + judge) | 19 |
| harness failures | **judge died on a 529**; returned `judgement: null` | 0 errors, 0 empty |
| raised | **18** | 4 |
| never refuted (capped) | **10 — 56% of the raise** | 0 |
| survivors after judging | 5 | — |
| **real, user-visible** | **3** (all fixed in 0.32.5) | **2** (in already-gated work) |
| **reachable in production** | **0** at the verdict | — |
| stale raises | — | **2**, from readers whose tree moved under them mid-review |

**What this licenses:** an audit that raises 18 and yields 3 real defects has a shape worth knowing
before the next fan-out is sized. **What it does not:** a kill rate — nobody seeded known defects, so
the false-negative half is unmeasured. That is exactly what the analysis's step 4 asks for.

**One novel failure mode the analysis does not name**, from the coder's run: **two of four raises were
stale because three commits landed underneath the reviewers while they read.** The fix is a named
commit for the review to pin, not more reviewers — and **nothing in the harness surfaced it**; a
later-launched judge is what contradicted them.

### 3.5 What a hook would have caught, measured

| failure | instances | analysis step |
|---|---:|---|
| Landing over a red gate — **two informed agents, one day, both quoting the rule at each other** | 2 | 5 |
| Landed rows still reading open, nearly causing a **rebuild of shipped work** by a cleared session | 4 rows | 7 |
| A fan-out returning a null conclusion with 13/14 agents done | 1 | 1 |

**And the counter-example, which is the strongest argument for the hook direction:** the guard built
for the first of these (`tools/land.py` refusing an uncertified merged tree) **policed its own
landing** — the first branch it refused was the one introducing it. Prose did not stop two informed
agents; the mechanism stopped its own author immediately.

### 3.6 The one hand-rolled mechanism to leave alone

Fragment lifetime, **re-measured on a fresh cohort**: **39 paired fragments since 20260903, median
2.2 h, max 6.8 h.** The analysis measured **2.1 h over 297** paths across all history. Two
independent populations, one answer. **It does not rot.**

### 3.7 Structural claims re-verified

`.claude/` **absent** · global hooks **`<none>`** · `CLAUDE_CODE_SUBAGENT_MODEL` **sonnet** ·
`review_pass_gate.py` referenced in `check.sh` **0**, `Makefile` **0**, all three CI workflows **0**,
`tests/` **2** — control: `paid_path_gate` in `check.sh` **1**, so the selector fires.

---

## 4. What is still not established

- **The review kill rate.** Needs seeded defects. Nobody has run it. § 3.4 gives the false-positive
  side only.
- **Whether the ownership boundary costs throughput.** The coder measured it twice today — cost zero
  once, one message round-trip once, **never blocking**. Two data points, opposite in kind to the
  planner's earlier "write-latency" claim, and neither is a population.
- **Whether `ty` and `pyright` should both run in `check.sh`.** They disagreed **in both directions**
  on one file today. One file is not a population.
- **Re-derivation figures** (95.8% of files re-opened, 35.6% repeat tokens) — still quoted from a
  docstring dated 20260826, still not re-run. `tools/review_ledger.py --measure` would settle it.
- **Whether truncation is value-biased against the runtime lens.** This session's audit capped 10 of
  18, but its lenses were **not** scheduled slow-first, so it neither confirms nor refutes the claim.

---

## 5. Open rows at the pause

Read `plans/20260901_1148-clear-the-user-facing-list.md` § 3 for the bodies. **Four carry a decision
inside a row whose blocker cell reads *nothing*** — 9, 23, 25, and 29's discriminator.

| row | what | owner | note |
|---|---|---|---|
| **9** | `.pinakes/` questions in `doctor` | coder | design choice inside: where the helper lives |
| **23** | a post-render `tomllib.loads` in `template.py` | coder | design choice: fail or degrade |
| **25** | `pnk budget` prints a KB name raw | coder | design choice: where the guard belongs |
| **29** | a gate refusing the `pathlib` spelling on a corpus path | coder | **blocked on its discriminator, which is the planner's to rule.** 47 sites, 18 files, three discriminators already refuted, and a **parse-not-grep** constraint |
| **36** | reachability of the 47 | coder | **delivered as measurement**; 26 of the sites are classified *by reading, not by probe* |
| **42** | the vacuous-injection audit on Linux | coder | **in flight at the pause** — see the coder's fragment |

**The previous coder declined row 29 deliberately**, and the reason is worth honouring: they would
bring a session of specifics the design does not need, and a strong prior toward their own proposal.
**A fresh reader working from the row's written population is better placed than the person who
measured it.**
