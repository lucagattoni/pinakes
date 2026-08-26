## Measuring the review loop — every arithmetic claim in the report had an error (20260826 06:50)

A session measured what this project's adversarial review costs, from the agent transcripts on disk,
and proposed eight ways to make it cheaper. An adversarial fan-out over those proposals returned 52
findings. **Six of the six arithmetic claims that were re-derived turned out to be wrong**, in a
report whose whole purpose was to be quantitative. The mechanism it described survived; almost none
of its numbers did. What follows is why each one broke, because the causes are not specific to this
measurement.

**HIGH — a number in a docstring is a claim with no gate on it, and the fix that invalidates it will
not say so.** `tools/review_pass_gate.py` shipped citing "613 review agents, 87% leave some
artifact, 58% of 6,015 targets are relative paths". During that same increment a filter was added
rejecting shell fragments a redirect-scan had reported as files — `0`, `c`, `15,}` — because a real
run showed them. Adding it changed the denominator of the measurement quoted three paragraphs
further down the same file, and nothing re-ran it: 49.2% of those 6,015 "targets" were never files.
The true figures are 41% leaving any artifact and 59% leaving none. `./check.sh`, `pyright`, `ruff`
and sixteen tests were green throughout. *Lesson: prose in a source file is unversioned evidence.
When a change alters what a measurement counts, the measurement is stale even though the diff never
touches it — and no gate in this repo can see that.*

**HIGH — a keyword classifier over agent briefs counts the repository's own instructions.** The
population was built by matching `review` over each subagent's task. `CLAUDE.md` tells every
*implementer* to "adversarially review" its work, so coder agents matched and were counted as
reviewers — and coder agents write far more files, and cost far more per turn (median ~173,500
tokens/turn against a reviewer's ~61,700), so they distorted every derived ratio. The replacement
classifies on role and was hand-audited over a 30-run random sample: 14 of 14 correct, recall
imperfect, so it is a lower bound rather than a point estimate. *Lesson: when the corpus is agent
transcripts, the vocabulary of the task and the vocabulary of the instructions are the same
vocabulary. State a classifier's measured error rate, or do not state a population.*

**HIGH — the currency was never declared, and the two currencies disagree by 25x.** "87% of review
spend is re-transmission, 13% is the findings" is a *weighted* ratio. In raw tokens — the unit every
other figure in the same report used — it is 99.5% re-transmission and **0.5% output**. Both are
true; quoting one beside totals stated in the other puts two denominators in one paragraph.
*Lesson: a ratio over tokens is meaningless until the weighting is written next to it.*

**MEDIUM — a pooled ratio is not a typical one.** "101,256 tokens per turn" was Σtokens ÷ Σturns
across the corpus. Corrected and de-contaminated it is 91,617 pooled, against a **per-agent median
of 61,688** — the pooled figure sits near the 90th percentile of individual agents, so it described
almost none of them. *Lesson: pooling answers "what did the fleet cost"; sizing a per-agent budget
needs the per-agent distribution, and the two differ by 50% here.*

**MEDIUM — six merges from one afternoon are not "recent increments".** The report argued that review
was disproportionate to the work, citing the last four merges at 7, 37, 62 and 232 changed lines.
Those were one burst of documentation and fragment merges. Re-sampled, the surrounding increments run
70 to 1,211 lines. An entire proposal — scale the review down for small increments — rested on that
sample and does not survive it. *Lesson: `git log --merges -n` returns the most recent n, not a
sample of the distribution, and a project that lands in bursts makes those two very different.*

**And the finding that made the rest recoverable: the fan-out that raised all of this lost every one
of its six refuters to a usage limit and returned `{"confirmed": []}`.** Written the way the tool's
own documentation recommends — collecting results and filtering out the empty ones — that is
indistinguishable from an adversary that examined the work and approved it. The findings survived
only because the harness counted launched agents against returned ones and refused. Each was then
confirmed by re-deriving it rather than by reading it again. *Lesson: an adversarial pass that
returns nothing is making a claim about itself first and about the work second, and re-reading a
number never falsifies it — recomputing it does.*

**And the finding the report should have led with: the retrospective loop IS the spend, and
its yield halves while its price does not.** The report's own share figures were computed from a
keyword classifier and were wrong twice. Recomputed the plain way — list every subagent run's task
title with its token total, then let the clusters fall out — 899 runs and 5.13 billion raw tokens
divide like this: **adversarial review of an increment, plus the refuters serving it, is 44.0%**;
building and fixing increments is 18.1%; plan work 7.8%; decision analysis 5.9%; sweeps 5.7%; corpus
and eval authoring 1.5%. A further 16.7% resisted clustering and is named here rather than
distributed, so 44% is a floor. **Review is 2.4x the next largest category**, and the nine single
most expensive runs in the project are all *build* work, which is the other thing the title listing
makes obvious and no proposal in the report addressed.

The decay inside that loop is recorded in the repo's own agent briefs, because each pass is told what
came before: **passes 1–4 over one increment found 30, 22, 13 and 6 issues.** Median cost per pass,
over the runs that state their number: 7.5M raw tokens at pass 2, 12.5M at pass 3, 12.9M at pass 5 —
flat to rising. Yield halves, price does not, so the marginal cost of a finding roughly doubles every
pass. *The caveat that keeps this honest:* only 43 runs state which pass they are, and later passes
announce themselves ("the FIFTH adversarial review pass") while a first pass usually just describes
the task — so the split of spend by pass number is biased and is not quoted. The decay curve is
quoted verbatim from the briefs.

*Lesson: the loop's cost is not the depth of any one pass, it is that every pass pays full price for
context the previous ones already established.* Each pass is a fresh agent, told the history but
handed none of the evidence, so it re-derives the map before it can look for anything new — at a
measured ~102,000 tokens per turn, where 99.5% of those tokens are re-transmitted context and 0.5%
are the findings. That is the shape to attack: not fewer passes and not cheaper models, both of which
trade away what later passes are good at, but a later pass that starts from what the earlier ones
established instead of from zero.

*And the method lesson, which is the one that generalises:* the clusters above came from listing
every task title against its token total and reading the list. Three successive regex classifiers
over agent prompts had each produced a different, confidently wrong answer. **Sort the units of work
by cost and read the labels** before writing a classifier over them.
