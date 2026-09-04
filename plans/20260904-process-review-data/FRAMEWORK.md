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
5. ⟦**corrected 20260904 12:10**, at the coder's insistence and rightly⟧ — **the 791 handed over was NOT an
   error.** It was correctly measured when taken and **went stale**: two runs landed between the two
   extractions. **A stale-but-correct measurement and a composed number are different failures with
   different fixes**, and listing them together blurs the distinction this taxonomy depends on. The
   predecessor's two real errors were a local timestamp labelled UTC and a wrong claim about re-run
   deduplication.
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
- ⟦**corrected 20260904 12:10** — this said the guard *"caught its own author immediately"*. **It did not, and
  I inferred a refusal from the word "policed".** ⟦measured, coder⟧ across 14 coder sessions:
  **`land.py` was invoked 43 times and succeeded 43 times — zero refusals in the population.** What
  actually happened is that both sessions **re-gated before landing in order to satisfy it**. Its
  effect is **deterrence, not interception**, and a framework crediting it with catches would be
  crediting the wrong mechanism.⟧

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
| Would hooks have prevented the prose-rule failures? | **Not from data**, and the counter-example I offered was wrong — see §3.3. `land.py` has **never refused**; its measured effect is deterrence |

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
3. **`check.sh`** — caught nothing *on that one change*, and could not have, since it was a `.tsv`.
   **⟦measured, coder, 20260904 12:10⟧ Across 14 sessions this generalisation is false: 157 invocations, 31 of
   139 resolved outcomes were RED — 22.3%, in 14 of 14 sessions, with real defects behind them.**
   The coder retracted their own line unprompted. **`check.sh` is not a near-always-green
   precondition**, and the n=1 reading is the exact shape their own warning names.

**Their warning, which I am recording verbatim in substance:** *ranking gates by yield on one change
is how a project deletes the gate that saves it next week.* They **declined to rank** the mutation
batteries and the injection audit because this session ran neither.

### 6.3b Instrument catch rates across 14 coder sessions ⟦measured, coder — **judge ruled 20260904 12:22**⟧

**41 findings: 30 SUPPORTED, 11 OVERSTATED, 0 unsupported. 5 of 5 lenses returned, none died.**
Two figures below were corrected *by* the adjudication and one ranking was withdrawn:
`fragments.py` was reported at 9.2% and is **4.2%**; `land.py`'s zero needed the age caveat; and
**"fan-outs are the richest source of caught coder errors" is withdrawn** — not established against
the gates, which went red 31 times on `check.sh` alone in the same population. **Both are real; the
ranking is not.**

| instrument | invocations | caught something |
|---|---:|---|
| `check.sh` | 157 | **31 of 139 resolved RED (22.3%)**, all 14 sessions |
| `mutate.py` | 150 | `--check-anchors` **18%**; battery runs **16.7%** found a SURVIVED mutant |
| `fragments.py` | 84 | **3 of 72 resolved (4.2%)** caught a real malformed fragment |
| `shared_file_overlap.py` | 39 | **2 of 38 resolved (5.3%)** — the one genuinely almost-always-null instrument |
| `land.py` | 43 | **0 refusals across that population — and the figure was nearly vacuous.** The gate-certification refusal shipped 20260904 08:25Z (`66ddb8f`), so **at most ~8 of the 43 could ever have exercised it.** ⟦read, coder, ~12:30⟧ **It has since fired — see §6.3f.** |
| workflow fan-outs | 34+ runs, 360+ child agents | in one increment a **pass-4 judge ruled DOES NOT LAND after three prior passes had cleared it** |

### 6.3c My hypothesis has a number, and it is not a landslide ⟦measured, coder — adjudicated⟧

Of **45 correction events read in full context: ~29 (64%) were truth-cost** — population, staleness,
an unmeasured claim. **The other ~16 were faulty logic or wrong scope, and 11–12 of those were caught
only by *running* something** — a mutation, a real interpreter, a real OS.

**That is sharper than either of our positions.** Truth-cost dominates, **but a third of corrections
are not truth-cost at all, and that third is invisible to reading.** It needs execution.

### 6.3d What the adjudication added ⟦measured, coder + judge, 20260904 12:22⟧

**The 791 has a mechanism, and it is sharper than "two runs landed in between".** The number came
from a command: a `tool_result` at **10:43:38Z reads literally `791`**, 21 seconds before the
harvest launched. **The drift was self-inflicted** — that session's own `land.py` push created run
ids `33864815430` and `33864815456` at 10:46:32–33Z, both success, **678 + 2 = 680**. **The
predecessor was invalidated by its own landing.**

**The timestamp defect is two defects, not one.** `11:44` is a **+1 h local reading of a real
mtime** — a unit error. **`11:55` corresponds to no event in either zone**; the session's last
record is 10:49:48Z — a **composed** number. **The composed half is the more serious**, and merging
them would have lost exactly the distinction §3.1 turns on.

**Three findings that contradict the single-session view:**

1. **Coder sessions are the *leanest* on context per output, not the heaviest.** Median
   context∶output — **coder 189.5** (n=14), **planner 243.3** (n=10), **unnamed 285.1** (n=44). And
   **compaction does not drive it**: the seven highest-ratio coder sessions have **zero**
   compactions between them, while the session with fourteen sits at 150.5.
2. **The user never fact-checks a coder's claim.** Across ~42–46 real human turns in all 14
   transcripts — after excluding tool results, compaction summaries, task notifications, peer
   messages and command wrappers — **zero correct a specific coder claim.** The dominant forms are
   role assignment and *"I hit my usage limit, please continue"* (verbatim in 7 of 14).
   **Error-catching is a peer, self and gate function. Scope-setting is the user's** — and this
   widened review exists because of one user turn.
3. **Elapsed time is unusable as a work proxy across most of the population.** One session shows a
   single **5,593-minute gap** and a **1.9% active fraction** over 99.6 hours. Another is **25.8%**
   active — **not the 35% a lens claimed**, and the judge caught that lens picking a flattering
   threshold. **State the threshold with the number or the number means nothing.** ⟦This corrects
   the corroboration I recorded for my own 120-second cut.⟧

**A rule whose compliance is checkable after the fact — and nobody had checked it.** The 20260831
subagent-model rule took effect and is measurable from `agent_tasks.tsv`'s `dominant_model` joined
on run. Of **360 fan-out child agents** across 10 of 14 sessions: the 5 sessions **predating** the
rule ran **96 of 103** non-synthetic agents on Opus; sessions **after** it ran **15 of 237 (6.3%)**,
and those 15 are **approximately one per fan-out** — which is the judge the rule permits.

**Two attribution warnings the judge issued:**

- **Attributing a window's commits to whichever session was in flight is unsound whenever a planner
  runs concurrently** — which here is always. Three commits credited to a coder session carry the
  planner's token.
- **Do not carry "compacts, then re-reads, pays twice" as measured.** Only 4 of 14 sessions
  compacted, genuine content-repeat calls are **17 of 4,494 (0.4%)**, and the lens testing it
  **disqualified its own control rather than claim the effect.**

**And a consequence for any future measurement:** the 89%-Bash figure survives, but `echo` (632) and
`python3` (610) alone are **28% of coder calls** and **cannot be typed from a 40-character target**.
Measuring what a coder did requires parsing Bash `tool_result`s and exit codes.

### 6.3e What the whole set agrees on

**The handoff channel failed and the repair loop worked.** All three header claims passed between
sessions were defective; **all three were caught and corrected by the receiving session within about
65 minutes**, and the corrected values are on `main`. **A retrospective that stops at the error
misses the half that worked** — and the coder notes this is not what their own fragment said.

### 6.3f The guard fired, on the session landing the sentence that said it never had ⟦read, coder — 20260904 12:30⟧

**Roughly four hours after the refusal shipped, `land.py` refused a landing.** ⟦read⟧ from the
coder; the mechanism is ⟦observed⟧ in `tools/land.py:160`, which emits *"no ./check.sh run has
certified the tree this would land"*, names all three trees, gives the remedy, and states **"There is
no override."** The refusal was added in `66ddb8f`, 20260904 08:25Z.

**What triggered it is the point.** `main` moved during their `check.sh` run, so the merge produced a
tree **no gate had certified** — which is *exactly* the mechanism they reported as their session's
dominant wall-clock cost, and the **fourth** occurrence of it for them that day. **This time the
guard converted a silent stale-tree landing into a stop.**

**And it caught the session in the act of landing a document that said it had never fired.** They
recorded a postscript rather than tidying it away, on the ground that the alternative is *"a document
whose own landing falsified it silently."*

**What this does and does not change.** The zero across 43 remains what it was: **a number that could
not have come out differently**, over a population that mostly predates the refusal. **What makes
this event evidence is that the same instrument, on a population where it *could* fire, did.**
Deterrence and interception are both real; the historical count only ever showed the first.

**It is the strongest single argument in this review for encoding a rule as an executable guard
rather than as prose** — and unlike most of what is argued here, it is a measured event rather than
an inference. Set beside §3.3: **two informed sessions broke the prose version of this rule in one
day while quoting it at each other**, and the executable version stopped its own author within hours
of existing.

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
