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

## 3. Evidence for the analysis's proposed steps

**Measured 20260904 10:27 on the tree at `7b079e54a26ff432feb3097018a6e41441554a53`, except where a population is stated otherwise.**
Each row says what it supports and what it does *not*.

### 3.1 Structural claims — re-verified, and one has moved against us

| Claim in the analysis | Measured now | Verdict |
|---|---|---|
| No `.claude/` directory in the repo | `.claude` **absent** | holds |
| No hooks anywhere | global `settings.json` `hooks: <none>` | holds |
| `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` set | set | holds |
| `review_pass_gate.py` never run against a live journal | `check.sh` **0**, `Makefile` **0**, all three CI workflows **0**, `tests/` **2** (control: `paid_path_gate` in `check.sh` = 1) | holds |
| `CLAUDE.md` is 302 lines, target under 100 | **427 lines** at `d474ffa`+2 days — **+41%** | **worse**, and mostly written by this planner |

**The CLAUDE.md growth is the sharpest self-indictment available.** The analysis named the file's
size as a defect on 20260903 and quoted the official guidance — *"Bloated CLAUDE.md files cause
Claude to ignore your actual instructions"*. In the two days since, the planner added 125 lines to
it, every one of them a correction or a status note. **The mechanism that produced the growth is the
one the analysis diagnoses**: with no hooks and no agent definitions, prose is the only substrate
available, so every lesson becomes another paragraph in the file that is already too long to read.

### 3.2 Step 1 — coverage in every fan-out's return value <span>**supported, with a measured instance**</span>

The floor audit run this session (`wf_89bdaf06-435`) is a direct test. **Its judge died on an API
529 with 13 of 14 agents complete**, and the workflow returned `judgement: null`.

- **What saved it:** the script carried explicit coverage — `lenses_launched/returned`,
  `refuters_launched/returned`, `refuters_ran_both`, and a named list of findings capped without
  refutation. Reading those is what said *PARTIAL*, not the null conclusion.
- **What would have hidden it:** a reader who looked only at `judgement`. A null there is
  indistinguishable at a glance from "nothing found".
- **Population:** one workflow, 14 agents, journal on disk. Re-run of the judge alone later returned
  `run_quality: PARTIAL` **naming the cap** — 10 of 18 findings never refuted, 56% of the raise.

**This supports step 1 as written and adds one thing the analysis does not say: coverage counts are
necessary but not sufficient — the conclusion field must not be readable as a result on its own.**

### 3.3 Step 4 — calibrate the review instrument <span>**the strongest evidence, and it arrived by accident**</span>

The floor audit's findings were followed to their end over the following hours. **That chain is the
first measured false-positive characteristic this project has:**

| stage | count | instrument |
|---|---|---|
| Raised by 5 lenses | **18** | journal, counted |
| Refuted (8 launched, 8 returned, **8/8 ran both interpreters**) | 6 CONFIRMED, 2 ALREADY_FIXED | journal |
| Capped with **no refuter at all** | **10 (56%)** | judge's own report |
| Ruled survivors by the Opus judge | **5** | judge |
| **Real, user-visible, and fixed in 0.32.5** | **3** | the release's own controls, read from two wheels |
| **Reachable in production at all** | **0** at the time of the audit's own verdict | measured against production paths |

**Two separate corrections were needed to get there, and both were caught by the implementer, not by
the instrument.** The judge's most severe finding named the wrong cause — `root.is_dir()`, which
answers identically on both interpreters. And the two sites later filed as live defects were
**unreachable**, one of them because a guard landed earlier the same day already refused the
directory at the walk.

**What this licenses:** an audit that raises 18 and yields 3 real defects has a shape worth knowing
before the next fan-out is sized. **What it does not license:** a kill rate. Nobody seeded known
defects, so the *false-negative* half is still unmeasured — which is exactly what step 4 asks for and
this does not provide.

### 3.4 Step 5 — ownership and land rules as hooks <span>**supported, two instances in one day**</span>

- **Two sessions landed over a red gate in a single day**, hours apart, **both while quoting the rule
  at each other**. One used `check | tail && git commit`; the other used `check; echo $?` and an
  unconditional commit. Neither was ignorance — the rule is in `CLAUDE.md` and both had cited it.
- **The guard that fixed it is code, not prose** (row 39): `tools/land.py` now refuses a merged tree
  no `./check.sh` run has certified. **It policed its own landing** — the first thing it refused was
  the branch that introduced it.
- **The merged-tree subtlety was found before it shipped**: keying the marker to the branch tip would
  have been blind whenever `main` had moved. Counted over **every merge since 20260903 12:00 — 35
  merges, 5 differ (~14%), and every one of the five landed while a second session was active.**

**This is step 5's argument made twice**: a rule that two informed agents broke in one day is a rule
that needs a mechanism, and the mechanism worked immediately.

### 3.5 Step 7 — a status-claim linter <span>**supported, and it nearly cost a rebuild**</span>

**Four landed rows still read as open** hours after landing, and a **freshly-cleared coder session
proposed taking one of them** — work that had shipped in 0.32.5. `CLAUDE.md` already records this
exact failure twice before. **Cause, named rather than apologised for:** the planner spent the
morning appending corrections into row *bodies* and never returned to the *titles*, which is the half
a scanning reader reads.

**A linter checking that every `BUILT` cell carries a sha that is an ancestor of `origin/main`
would have caught all four mechanically.** That is step 7 exactly.

### 3.6 The fragment mechanism — independently re-measured, **holds**

The analysis measured 297 fragment paths, median lifetime **2.1 h**, none over seven days.
**Re-measured on a fresh cohort — 39 fragments paired since 20260903 — median 2.2 h, max 6.8 h.**
Two independent populations, the same answer. **This is the one hand-rolled mechanism the evidence
says to leave alone.**

### 3.7 Where the analysis is *not* supported by this session

- **"Review is ~36.8% of delegated spend"** — not re-run here. Quoted, not measured.
- **The re-derivation figures (95.8% / 35.6%)** — the analysis itself flags them as quoted from a
  docstring dated 20260826 and not re-run. Still not re-run.
- **Truncation is value-biased against the runtime lens** — the audit capped 10 of 18 findings, but
  **its lenses were not scheduled slow-first**, so this run neither confirms nor refutes the bias.
  A run with the ordering applied would.

---

## 4. What this session could not establish

- **The review instrument's kill rate.** Requires seeded defects. Nobody has done it.
- **Whether the ownership boundary ever costs throughput.** The two sessions gave opposite answers on
  20260903 and neither re-measured it today.
- **Whether `ty` and `pyright` should both run in `check.sh`.** The coder measured them
  disagreeing **in both directions** on one file today; that is one file, not a population.

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
