## The same day, measured across fourteen sessions instead of one (20260904 12:23)

**The user read the fragment written from a single seat and said the bound was the problem** — *"it
is very limiting to stick to your current one only."* So the same questions were put to all **14
coder sessions** in the transcript store and answered from the JSONL rather than from anybody's
recollection: five independent lenses, then one judge that re-ran selectors instead of trusting
either side. **41 findings — 30 supported, 11 overstated, none unsupported.** What follows is what
widening changed, including where it falsified
([*the fragment written from one seat*](#the-implementers-seat--one-session-measured-20260904-1128)).

### The retraction that matters

That fragment says `check.sh` caught nothing and could not have. **True at n=1, false as a general
claim.** Across the 14: **157 invocations, 31 red of 139 resolved — 22.3% — with at least one red in
9 of the 14 sessions.** The reds are real defects, not process noise (`EXIT=1 … 1 failed, 2130
passed`).

**Why I got it wrong is worth more than the number.** I looked for each gate's outcome in its own
tool result, found 136 of 159 unreadable, and reported the red rate as unrecoverable. It is not:
coders background the gate to a log, so the outcome arrives in a **later** call that reads that log.
**I pointed the instrument one hop short and reported the gap as a property of the data.** From the
inside, a null caused by a mis-aimed selector is indistinguishable from a null that is real.

### Four inversions

| written from one session | measured across fourteen |
|---|---|
| `check.sh` catches nothing | **31 red of 139 resolved (22.3%)**, in 9 of 14 sessions |
| `land.py`'s refusal is the guard that earns its keep | **43 invocations, 0 refusals** — and that refusal only shipped 20260904 08:25 UTC, so at most ~8 of the 43 could ever have exercised it |
| coders are context-heavy | coders are the **leanest**: median context/output **189.5** (n=14) against planner 243.3 (n=10) and unnamed 285.1 (n=44) |
| the three handoff claims were three failures | two were; **one was correct and went stale**, which is not the same thing |

**Postscript, seven minutes later: it refused this landing.** `main` moved while this fragment was
being gated, so the merge produced a tree no `check.sh` run had certified and `land.py` declined to
merge it — *"no ./check.sh run has certified the tree this would land"*, naming all three trees and
offering the remedy. The count in the table is a historical population and stands. But **the guard
is younger than its first refusal by about four hours, and its first refusal caught the session
writing the sentence that it had never fired.** Deterrence and interception are both real; the
sentence needed the second half.

**Neither gate generalises to "the gates".** 22.3% red says a gate is not a rubber stamp. Zero
refusals in 43 says a guard can be correct and still never fire — its measured effect is deterrence,
and it is too young for a catch rate to mean anything. Different instruments, different ages.

### Three claims, three failure modes — the distinction the taxonomy rests on

- **`791` was measured, and correct when taken.** A tool result at 10:43:38 UTC reads literally
  `791`, 21 seconds before the harvest launched. It went stale because that session's **own**
  `land.py` push created two further runs at 10:46:32, both success: 678 + 2 = 680. **The
  measurement was invalidated by the measurer's own landing.**
- **The timestamp is two defects in one field.** `11:44` is a real file mtime read in local time and
  labelled UTC. `11:55` corresponds to **no event in either zone** — that session's last record is
  10:49:48 UTC. A unit error, plus a composed number, and the composed half is the worse one.
- **The de-duplication claim was never true.** `cut -f2 | sort -u` over the finished file is 793 of
  793. One line falsifies it.

**Only the third is the kind of error reading catches.** Stale-but-correct, composed-from-nothing
and never-true need three different fixes, and a failure list that merges them teaches the wrong
lesson to whoever reads it next.

### What widening did not overturn — and where it sharpened the edge

The claim that the binding cost is **establishing what is true** survives, with both a number and a
limit. Of 45 coded correction events, roughly **64% were fact-establishing**. The remaining third
were real defects in code, tests or verification logic — and **11 to 12 of those were caught only by
running something**: a mutation, a real interpreter, a real operating system. **That third is
invisible to reading**, so more review does not reach it. The judge also cut the 64/36 back from a
population statistic to what it is: a hand-coded sample drawn by a keyword selector.

### A rule whose compliance turned out to be auditable

Of 360 fan-out child agents across 10 of the 14 sessions, the five sessions predating the 20260831
model rule ran **96 of 103** non-synthetic agents on the top tier; sessions after it ran **15 of 237
— 6.3%** — and those fifteen are approximately one per fan-out, which is the judge the rule permits.
**The instrument already existed**, in the harvest's own `dominant_model` column, and had never been
pointed at the question. **A rule that can be audited after the fact out of data already collected
is worth more than one that can only be remembered.**

### What the judge cut from my own work

Eleven of the forty-one findings were overstated, and three of those are mine to answer for.
`fragments.py` catches **3 of 72 resolved (4.2%)**, not the 9.2% I relayed to a peer before
adjudication. *"Fan-outs are the richest source of caught coder errors"* is not established against
gates that went red 31 times in the same population. And a lens reporting one session as *"35%
active"* was **25.8%** by the repository's own stated threshold — it correctly identified an
elapsed-versus-active category error and then committed a milder version of the same error by
choosing a flattering cut. **State the threshold with the number, or the number means nothing.**

### The half the first fragment missed

All three handoff claims were defective. **All three were caught and corrected by the receiving
session inside about 65 minutes**, and the corrected values are on `main`. The channel failed and the
repair loop worked. **A retrospective that stops at the error has described half a system**, and the
half it drops is the half worth keeping.

**One correction reframes who does what here.** Across roughly 42 real human turns in all 14
transcripts — after excluding tool results, compaction summaries, task notifications, peer messages
and command wrappers — **zero correct a specific coder claim.** Catching errors is a peer, self and
gate function. What the user supplies is **scope** — and this fragment exists because of one
sentence of it.
