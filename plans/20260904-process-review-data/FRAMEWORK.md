# How Pinakes development actually works — a framework for reading the data

**Written by the planner session, at the user's instruction, to sit beside the thirteen datasets in
this directory and be read against *Framing, Not Roles* (artifact `2c7961ec`).**

**It characterises and does not prescribe.** The user's brief was to describe the mechanism, say
which questions the raw data can settle and which it cannot, and stop short of recommending —
*Framing, Not Roles* already carries a rollout, and this planner built most of what would be under
review and is not a neutral party.

## How to read a claim here

Every claim is tagged by **how it was known**, because most of this project's recorded failures are
true statements over the wrong population.

| tag | means |
|---|---|
| **⟦observed⟧** | I saw it happen in this session, 20260903–04 |
| **⟦measured⟧** | Computed from a dataset in this directory; the file and column are named |
| **⟦read⟧** | Taken from records earlier sessions wrote. **True as testimony, not re-verified** |

**The bulk of the project's life is ⟦read⟧.** Six weeks exist; I was present for two days.

---

## 1. The mechanism, as it actually runs

**Two resident sessions.** A **planner** owns every document — `docs/**`, `plans/**`, any
`README.md`, `CLAUDE.md`, `CHANGELOG.md`. A **coder** owns `src/`, `tests/`, `tools/` and the
fragment streams. Neither writes the other's files; a coder proposes document changes as a diff, and
where text must land in the coder's own commit the planner dictates it and the coder pastes it
unchanged. ⟦read⟧ for the rule's origin, ⟦observed⟧ for it working: it bound twice in two days.

**Work is a queue of numbered rows** in one live plan file. A row carries a title, an owner, a
blocker, and a body that is usually longer than the rest of the row combined. ⟦measured⟧
`plan_rows.tsv`: **44 rows, 27 ever marked done, median 3.7 h from first appearance to first done,
max 48.3 h, and 17 never marked at all.**

**An increment is: own worktree → build → tests → `./check.sh` green → mutation battery →
adversarial review → fragments → land.** ⟦read⟧ from `docs/BUILDING.md`; ⟦observed⟧ ten times.

**Records are append-only fragments**, spliced into `CHANGELOG.md` and `docs/RETROSPECTIVES.md` at
release time, so two sessions never edit the same hot file. ⟦measured⟧ `fragments.tsv`: **346
fragments, 332 paired, median lifetime ~2 h, none over seven days.** This is the mechanism with the
strongest evidence of working and the only one measured twice, independently, to the same answer.

**Releases are frequent and small.** ⟦measured⟧ `releases.tsv`: **64 tags in 41 days.** Four were
cut in a single day during this session.

**Enforcement is entirely at the code layer.** ⟦measured⟧ ~20 deterministic gates run by
`check.sh`; **no `.claude/` directory, no hooks of any kind.** Every rule about *agent* behaviour —
roles, ownership, procedure, handover — is prose in a 455-line `CLAUDE.md`.

---

## 2. What the record shows

### 2.1 The project shifted from building to writing about building

⟦measured⟧ `commits.tsv`, weekly:

| week | `src/` lines | prose % of churn | retro fragments |
|---|---:|---:|---:|
| W30–W33 | 5,080–14,959 | 35–47% | 0–35 |
| W34 | **593** | 36% | 12 |
| W35 | 1,156 | **60%** | 26 |
| W36 *(4 days)* | 2,012 | **57%** | **63** |

`src/` churn fell about tenfold; prose became the majority; **W36 alone carries more retrospectives
than any complete week in the project's life.** Maturation explains part of this. Nothing in the
data says how much.

### 2.2 The records grew fastest where they were already too long

⟦measured⟧ `claudemd_size.tsv`: `CLAUDE.md` went **76 → 455 lines over 150 commits**, and **321 →
455 in the three days after an analysis named its size as a defect** — most of that written by me.
⟦observed⟧ the mechanism: with no hooks and no agent definitions, **prose is the only substrate
available**, so every lesson becomes another paragraph in the file that is already too long to read.

### 2.3 Where the tokens are

⟦measured⟧ `agent_tasks.tsv`, Pinakes only:

| scope | agents | context tokens | share |
|---|---:|---:|---:|
| resident main-loop sessions | 88 | 5.39 B | **60.1%** |
| subagents | 106 | 1.02 B | 11.3% |
| workflow agents | 1,437 | 2.57 B | 28.6% |

**Context — what the model is *sent*, re-transmitted every turn — runs ~270× output.** Resident
sessions are 5% of agents and 60% of context. Median agent duration 277 s, p90 1,372 s.

### 2.4 Repetition is smaller than it looks, and the measurement was wrong twice

⟦measured⟧ `tool_calls.tsv`: **4,197 of 64,735 calls (6.5%) repeat an identical call; 1,764 are the
same call five or more times in one transcript.** The first two versions of this column reported
**18,573** and **12,853** because they keyed on a truncated argument, which for Bash is the
`cd <worktree>` prefix — **47% of the first figure was the working directory.** The correction is
recorded in the README because it is the third instrument in two days whose first answer came from
reading the wrong thing.

### 2.5 Coordination has a measurable volume

⟦measured⟧ `cross_session_messages.tsv`: **293 peer messages received**; 39 of 88 sessions received
at least one; 11 sessions recorded a compaction. Sends leave no record in the sender's transcript,
so this counts one side only.

### 2.6 The retrospectives are overwhelmingly about the project being wrong about itself

⟦measured⟧ `retrospectives.tsv`: **195 entries, 130 carrying an explicit severity — 80 HIGH, 45
MEDIUM, 3 LOW, 2 CRITICAL.** ⟦read⟧ their subjects: a green test that asserted nothing, a count
quoted from a docstring, a gate that could not fail, a null result over a population that could not
contain the thing sought. **The dominant recorded failure is not a product defect. It is a false
belief about the product, the tests, or the records.**

---

## 3. Failure classes, named and dated

**Fully candid at the user's instruction.** Instances are named where the instance carries the
lesson.

### 3.1 A true measurement over the wrong population — the dominant class

Seven instances in two days, ⟦observed⟧ unless marked:

1. **20260903** — I ran `pnk doctor` on both interpreters, saw it complete, and wrote that it does
   not crash on 3.13. The KB had **no sidecar** for the unreachable document, so the raising line
   was never reached. With a sidecar it dies.
2. **20260903** — I said a merged tree differs from its branch tip "one in three", over three
   merges; the coder said "two of four"; the whole population of 35 gives **five, ~14%**.
3. **20260904** — I quoted agent-spend figures taken **without a project filter**, so my main-loop
   count was every project on the machine: **131, not 261** — inside the evidence file for this
   review.
4. **20260904** — the repeat column above, wrong twice.
5. **20260904** — the coder's predecessor handed over **791** CI runs; re-measuring found **793**.
6. **20260904** — the coder reported both checkouts resolving to 3.14.7. That was **a broken venv**,
   not the machine, and it reached `CLAUDE.md` on my paraphrase before either of us re-measured.
7. ⟦read⟧ **20260831** — six wrong claims in one day, each a valid inference over a population
   nobody stated.

**What separates the caught from the uncaught: every one was found by re-running, never by
re-reading.**

### 3.2 An instrument that cannot fail, reporting success

- ⟦observed⟧ **A review fan-out whose judge died on a 529 returned `judgement: null`** with 13 of 14
  agents complete. Explicit coverage counts in the return value are what said *partial*; the null
  conclusion field alone reads exactly like "nothing found".
- ⟦observed⟧ **A test that asserted nothing.** `test_an_unreadable_linked_kb_path_is_a_warning…`
  injected an error but built a fixture where the warning came from elsewhere. It passed with its
  own injection disabled. **A vacuous test and a sound one are the same colour.**
- ⟦observed⟧ **A mutant that could not kill.** It matched the anchor's regex but not its full
  predicate, so the test stayed green and "pinned by test X" was one keystroke from being recorded.
- ⟦read⟧ **`make release-check` was three `echo`s for a month** while two documents called it the
  last gate before an irreversible publish.

### 3.3 A rule that is prose is a rule that gets broken by people quoting it

- ⟦observed⟧ **Two sessions landed over a red gate in one day, hours apart, both quoting the rule at
  each other.** Mine used `;` where `&&` belonged, so the failure was *printed* and ignored.
- ⟦observed⟧ **The guard built for it caught its own author immediately** — `land.py` now refuses a
  merged tree no gate certified, and the first branch it refused was the one introducing it.

### 3.4 Registers drift from the tree, and the drift is invisible to every gate

- ⟦observed⟧ **Four landed rows still read as open**, and a freshly-cleared coder session proposed
  rebuilding one that had already shipped. Cause: I appended corrections into row **bodies** and
  never returned to the **titles**, which is the half a scanning reader reads.
- ⟦read⟧ `CLAUDE.md` records the same failure twice before, both times about ownership.

### 3.5 Rulings made from reading rather than running

- ⟦observed⟧ **I ruled a discriminator that would have regressed the floor.** It answered `False`
  for the exact shape behind the release-before-last's data-loss defect. The coder measured it and
  refused to build it.
- ⟦observed⟧ **I ranked a row above a gate design on an untested premise** — "live defects outrank a
  design" — having verified the mechanism but never that any production path reached it. It did not.
- ⟦observed⟧ **A specification of mine contradicted itself**: assert the *stable* verdict set is
  empty, while the next clause said a stable verdict is a finding to read, not a build to fail.

### 3.6 What the corrections have in common

**Nine of the day's substantive corrections came from the other session, not from self-review.**
⟦observed⟧ Self-review caught arithmetic and register drift; it did not catch a wrong framing.
Cross-session review caught framing repeatedly — and in one case a peer's *failed* refutation was
what exposed that an argument had never been load-bearing.

---

## 4. What the raw data can and cannot answer

| question | can the data settle it? |
|---|---|
| Where did tokens and time go, by task? | **Yes.** `agent_tasks.tsv` — prompt, duration, tokens per agent |
| Did an agent repeat itself? | **Yes**, for identical calls — `tool_calls.tsv`, `repeat_index` |
| Was a repeat *wasteful*? | **No.** That depends on what happened between the calls |
| How long does work sit? | **Partly.** `plan_rows.tsv` gives first-seen → first-marked-done, not first-*actually*-done |
| How often was `main` red, and on what? | **Yes** — the coder's `ci-runs.tsv`, with failing job **and step** |
| Does the fragment mechanism rot? | **Yes — no.** Measured twice, independently, same answer |
| Is review worth its cost? | **No.** Nobody has seeded known defects, so there is a false-positive shape and **no kill rate** |
| Did the ownership split cost throughput? | **No.** Two data points, opposite in kind, neither a population |
| Is truncation value-biased against slow lenses? | **No.** The one run that could have tested it did not schedule lenses slow-first |
| Would hooks have prevented the prose-rule failures? | **Not from data.** One counter-example exists: the guard caught its own author |

**One number is worth stating because it is the only end-to-end review measurement that exists.**
⟦observed⟧ + ⟦measured⟧ A floor audit raised **18** findings; 8 were refuted with all eight refuters
running both interpreters; **10 were capped with no refuter at all**; the judge ruled **5**
survivors; **3** were real and shipped fixes; and **0** were reachable in production at the time of
the verdict. **That is a false-positive shape, not a kill rate** — the false-negative half is
unmeasured because nobody seeded defects.

---

## 5. Open questions the data does not touch

- **What fraction of context is re-transmission that changed nothing?** `context_tokens` is
  measured; its *necessity* is not.
- **Would one session have been slower?** No counterfactual exists.
- **Is the retrospective growth a cost or a return?** Both readings fit the same table.
- **Does a 455-line `CLAUDE.md` still get read?** Nothing measures which lines change behaviour.

---

## 6. The implementer's perspective — and where it contradicts mine

**Source:** the coder session, `retro.d/20260904_1128-implementer-retro.md`. I asked it to be blunt
about the planner and to contradict me if my reading was wrong. **It did, and the contradiction is
the most useful thing in this document.**

### 6.1 My hypothesis was half right, and the missing half changes what the data means

I put to the coder that the day's real bottleneck was **the cost of establishing what was true**.
Their answer:

- **Agreed on corrections.** Every correction was truth-cost shaped — five for five.
- **Disagreed on the clock.** ⟦read, from their measurement⟧ **56 seconds to extract 793 CI runs;
  roughly 24 minutes to establish the extraction could be trusted.** And **4 min 40 s of their
  7 min 14 s of gate time went to re-gating because `main` moved under an already-green result.**

**Truth-establishment dominated the corrections. Contention with a moving base dominated the wall
clock.** These are different costs with different fixes, and — in their words — *"a framework that
merges them will prescribe more verification where the cost was actually sequencing, or better
sequencing where the cost was actually verification."*

### 6.2 The structural claim, which is theirs and which I would not have found

> **"Corrections are what reach you; waiting is what reaches me. Both denominators are real, neither
> is the whole."**

⟦observed⟧ This is visible in this document's own construction: I wrote §3 from the corrections that
crossed my desk and concluded truth-cost dominates. **The seat determines the sample.** It is the
strongest argument in the whole review for *asking the other role rather than reasoning about it* —
and it generalises past this project.

### 6.3 Instruments, ranked by the implementer, with a warning attached

⟦read⟧ Only the ones they actually ran this session:

1. **Review fan-out** — 2 real gaps, 1 false cause killed, at near-zero attention cost.
2. **`land.py`'s marker** — refused nothing and forced two correct re-gates. **The refusal is the
   yield.**
3. **`check.sh`** — caught nothing, and **could not have**, since the change was a `.tsv`.

**Their warning, which I am recording verbatim in substance:** *ranking gates by yield on one change
is how a project deletes the gate that saves it next week.* They **declined to rank** the mutation
batteries and the injection audit because this session ran neither.

### 6.4 Review is worth it, and its target should be prose

⟦read⟧ At n=1: worth it — because **a dataset's failure mode is not a wrong cell but a true sentence
licensing a wrong reading.** Three of four lenses re-checked things already true by construction;
**all the value came from the one lens attacking a claim they had made in prose.**

**Their own worked example, and the strongest argument for review in either account:** they wrote
*"every ref, every workflow, whole history"*, **re-read it**, and did not catch that it lets a reader
take the 63 Release rows as the release history with the first release silently missing. **A fan-out
caught it. Its target was their prose, not their code.**

**And truncation bit again** ⟦read⟧: the returned result truncated mid-run, and the only lens with
findings was the one they had to recover from `journal.jsonl`. **The lens with most to say is the
longest, so a summary loses it first.**

### 6.5 Which of the 455 lines actually worked

⟦read⟧ **About six.** They share one shape: **a rule with a mechanism attached** — `land.py`'s
guard, the ownership table, *read the clock*, *a null carries no information*, *a clean auto-merge is
not a correct merge*. **The long incident narratives changed nothing they did** — *"I could not act
on them and did not retain them."* They read all 455 lines to extract about six operative ones.

### 6.6 What would have made the day faster

⟦read⟧ **Not landing less — stating shelf life.** *"A verification should carry the base it was taken
against: I verified a patch applied, said so, and twenty minutes later it did not. Nothing was false
when I said it; it had a shelf life I failed to state."* **`applies to db65f5f` costs nothing and
turns a surprise into a visible expiry.**

### 6.7 Their assessment of the planner, including a refusal

⟦read⟧ **They declined to confirm four of the five failures I listed against myself** — the
discriminator, the untested premise, the four stale rows, the red-gate landing — because they did
not witness them and would not confirm them from a message. **They named why the refusal was hard:
my account is unflattering to me, which is exactly what makes accepting it feel safe.**

**That refusal is the correct move and it belongs in the framework**, because those four failures
appear in §3 of this document on my testimony alone. ⟦observed⟧ by me; **⟦unverified⟧ by anyone
else.** A reader should weight them accordingly.

What they did witness: **about five minutes lost to two of my landings mid-flight**, offset — their
judgement — by the reserved README row, which meant their session never had to ask where its output
belonged.

---

## 7. What the two accounts agree on

1. **Every correction, both seats, came from re-running — never from re-reading.**
2. **The instrument is the thing to distrust first.** Three instruments in two days returned a
   confident wrong answer before anyone doubted the tree.
3. **Review's value is highest against prose**, lowest against things already true by construction.
4. **A rule with a mechanism attached changes behaviour; a rule without one does not** — six
   operative lines out of 455, and two informed agents breaking a prose rule in one day while
   quoting it at each other.

## 8. Where they disagree, unresolved

| | planner | coder |
|---|---|---|
| The binding constraint | cost of establishing truth | **contention with a moving base**, on the wall clock |
| Ownership boundary cost | a write-latency on truth ⟦read, 20260903⟧ | zero, then one round-trip ⟦measured, 20260904⟧ |
| Whether the other's failures happened | ⟦observed⟧ mine, self-reported | **declines to confirm what it did not witness** |

**Neither account is the whole, and the reason is 6.2: the seat determines the sample.**
