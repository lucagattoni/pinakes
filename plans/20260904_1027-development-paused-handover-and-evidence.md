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

**Nothing is half-built and nothing is waiting on a timer.** No background task, no monitor, no
scheduled job. Both sessions ended by choice, not by limit.

---

## 2. State at the pause — verifiable, not remembered

| | |
|---|---|
| `origin/main` | `7b079e54a26ff432feb3097018a6e41441554a53` — CI green, primary checkout in sync, **no worktrees** except any the coder names in its own fragment |
| Published | **0.32.5** on PyPI, verified from the index with a control that discriminates the fix |
| Fragments waiting | **6** (`changelog.d/` and `retro.d/`) — **a release is due and was deliberately not cut** |
| Increments landed 20260903–04 | rows 7, 8, 30, 31, 32, 38, 39, 40, 41, 43 · releases 0.32.2 → 0.32.5 |
| In flight at the pause | row 42 (coder) — see its fragment and the row for exact state |

**Why the release was not cut.** A tag publishes to PyPI and PyPI never accepts a version twice.
Publishing is *starting* work, not stopping it — and the release procedure is itself inside the
scope of the review. **The six fragments are a normal resting state**, not an omission. Whoever
resumes cuts 0.32.6 when the process question is settled.

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

### 3.3 Where the money is — and the tier is unpinned

| scope | transcripts | est. $ | share of $ | $/transcript | Opus share of units |
|---|---:|---:|---:|---:|---:|
| **main loop (resident sessions)** | 261 | **$4,574.62** | **63.8%** | **$17.53** | **90.0%** |
| subagents | 125 | $723.43 | 10.1% | $5.79 | 69.9% |
| workflow agents | 1,466 | $1,867.28 | 26.1% | $1.27 | 55.3% |
| **total** | **1,852** | **$7,164.92** | | | 77.1% |

<sub>Instrument: `tools/agent_spend.py --scope {main,subagent,workflow} models`, re-run 20260904.
Dollars are an estimate from a cached rate card.</sub>

**Resident sessions are 14.1% of transcripts and 63.8% of spend.** A main-loop transcript costs
**13.8×** a workflow agent. The analysis measured $3.38k over 130 main-loop transcripts on 20260903;
**one day later it is $4.57k over 261** — roughly **$1.2k of main-loop spend in a single day** of
two-session development. **Only `CLAUDE_CODE_SUBAGENT_MODEL` is pinned; nothing pins the main loop**,
so 90% Opus at the most expensive layer is a default nobody chose.

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
