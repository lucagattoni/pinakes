# Two findings about what agents cost here — and what each one is *not*

**Measured 20260831 21:45–22:05 UTC by a peer session, then corrected against my own second-hand
version of them before anything was written down.** Both reached me as one-sentence claims. **Two of
the four things in those two sentences were wrong**, and asking rather than relaying caught those two.

> **📌 CORRECTED 20260831 23:20 UTC — and what was wrong was one of the corrections, not a fifth
> claim.** Row 2 of the table below is struck through: the original sentence was closer to right
> than the correction that replaced it. Asking did not catch this one. The
> three zeros in Finding 1, and the sentence they licensed — *"an unguarded path, not a realised
> cost"* — **were false when this file was committed.** They were read out of a population that
> could not have contained a non-zero: main-loop transcripts only, while subagents live under
> `<session>/subagents/` and workflow agents under `<session>/subagents/workflows/<runId>/`.
> Counted across every population, **551 of 866 fable-5 requests ran inside a fan-out**. The
> corrected numbers are below, each re-run by this session against the committed
> [`tools/agent_spend.py`](https://github.com/lucagattoni/pinakes/blob/main/tools/agent_spend.py)
> rather than transcribed from the peer who supplied them.
>
> **The lesson is not "check harder".** Asking *did* happen, twice, and the answer came back
> consistent both times, because the question and the answer shared the same unstated selector. A
> zero is the one result a wrong population returns without looking wrong — every other figure in
> that message was correct, which is what made this one survivable. **The rule it argues for is the
> one already written in `CLAUDE.md`: a claim resting on a set you selected must state the
> selector.** This file did not, so nothing in it could contradict the zeros.
>
> **And the correction had a population error of its own — caught by the peer whose number it was
> correcting, 20260831 23:36 UTC.** The corrected paragraph cited *59 transcripts* while naming
> `message.model` as its selector; 59 is the *string* count and `message.model` gives **33**. The
> extra files merely discuss fable-5 — **this evening's own analysis sessions among them.** Both
> versions of this file have now shipped a wrong population, one hour apart, in the document whose
> subject is wrong populations. Neither was caught by re-reading it.

| What I was about to write | What holds |
|---|---|
| *"`claude-fable-5` costs about 2× opus-5"* | **Exactly 2.00×**, on both input and output. Understated, not overstated |
| *"…and nothing stops an audit fan-out landing on it"* | ~~True as a **gap**. **Never once realised** — 0 of 868 workflow agents, 0 subagents, ever~~ **FALSE — corrected 20260831 23:20.** It is realised and always was: **551 of 866 fable-5 requests ran inside a fan-out**, 63.6% |
| *"about 21% of reviewer runs die…"* | **18.1%** or **24.0%** depending on the question; **21% equals neither**. And *"reviewer runs"* is not a population anyone can isolate |
| *"…with no commit and no resume"* | **False.** All 157 transcripts are on disk, median 142 KB. Resume *re-runs* them; nothing was lost |

---

## Finding 1 — `fable` is a selectable model that neither `CLAUDE.md` names

**The gap is real and I verified its two halves separately.** `fable` is an accepted value of the
`Agent` tool's `model` enum — `sonnet | opus | haiku | fable` — confirmed in a session's own tool
schema rather than inferred. Neither the global `CLAUDE.md`'s subagent-model rules nor this
repository's names it. The audits-run-on-Sonnet rule and the cost-of-an-undetected-error rule both
discriminate between `sonnet` and *"the top tier"*, and **`fable` is above the tier they were
written against.**

**The price, with its provenance, because a rate card is not a measurement:**

| | input | output |
|---|---|---|
| `claude-fable-5` | $10.00 / MTok | $50.00 / MTok |
| `claude-opus-5` | $5.00 / MTok | $25.00 / MTok |

Source: the model table bundled with Claude Code 2.1.252, **which carries its own cache date,
`2026-06-24`**. It has **not** been checked against live pricing. Quote it as *"per the bundled
model table, cached 2026-06-24"*, or fetch the live page before asserting it flatly.

**The hole has been fallen into, repeatedly. Re-measured 20260831 23:36 UTC** by this session with
`python3 tools/agent_spend.py [--project Pinakes] --scope <scope> models`. **`--scope` gained its
`subagent` and `workflow` values while this correction was being written** (`f02c6ea`), which is the
only reason the split below can be quoted: an hour earlier it was true and *unpublishable*, because
no committed instrument could reproduce it.

| Population | fable-5 req | fable-5 est. | scope total est. |
|---|---|---|---|
| All projects, `--scope main` | 315 | $127.85 | $3,791.33 |
| All projects, `--scope subagent` | 235 | $50.53 | $725.48 |
| All projects, `--scope workflow` | 316 | $62.65 | $1,445.06 |
| **All projects, `--scope all`** | **866** | **$241.04** | $5,961.91 |
| Pinakes, `--scope main` | 147 | $90.88 | $3,009.43 |
| Pinakes, `--scope subagent` | 155 | $25.98 | $695.33 |
| Pinakes, `--scope workflow` | 316 | $62.65 | $1,415.28 |
| **Pinakes, `--scope all`** | **618** | **$179.52** | $5,120.04 |

The three restricted scopes **partition** the corpus — 315 + 235 + 316 = 866, and 147 + 155 + 316 =
618. **551 of the 866, 63.6%, ran inside a fan-out**; in Pinakes it is **471 of 618, 76.2%**, and
**every one of the 316 workflow-agent requests is a Pinakes run.** So `fable` is not an unguarded
path. It is a realised cost the subagent-model rules do not name — a materially *stronger* argument
for the proposed clause than this file originally made, not a weaker one.

**Quote the request counts, not the shares.** The numerators have not moved by a request or a cent
across four invocations tonight; the denominators grew while they were being read — the all-projects
total went $5,933.14 → $5,961.91 in sixteen minutes. **The two original numerators were right; only
their scope was unstated and their denominators perishable.** A figure of **3.78%** circulated and matches
no scope in the table — do not write it.

> **📌 The transcript count in this section was wrong too, and a peer caught it — 20260831 23:36
> UTC.** It read *"59 transcripts … measured by scanning every `*.jsonl` under `~/.claude/projects`
> for a `message.model` of `claude-fable-5`"*. **The number and the method it named were not the
> same measurement.** 59 — 57 an hour later, because it grows — is every file in which the *string*
> `claude-fable-5` appears. Keying on `message.model`, the selector the sentence actually claimed,
> gives **33**. The two dozen extra files merely *discuss* fable-5, **this evening's own measurement
> sessions among them: grepping for a model's name counts your own analysis as data.** 33 is also
> 7 + 12 + 14 across the three scopes, which is the check that would have caught it.

**The day span depends on the scope, and neither party said which.** Keyed on `message.model`, using
the tool's own `find_transcripts` classifier and de-duplicated per request — the counts below
reproduce the table above exactly, which is what validates the de-duplication:

| scope | transcripts | req | days carrying a billed fable-5 request |
|---|---|---|---|
| `main` | 7 | 315 | 20260707, 20260709, 20260803, 20260804, 20260805, 20260821 |
| `subagent` | 12 | 235 | 20260709, 20260803 |
| `workflow` | 14 | 316 | 20260821 |
| **`all`** | **33** | **866** | the six above |

**And the day span was got wrong a third time, by the instrument that reads it.** The peer who
supplied *"three days"* re-measured before sending, got **four** — 20260709, 20260803, **20260804**,
20260821 — and withdrew the three-day version. **The four-day answer is the artifact.** It was taken
from **file mtime**; the table above is taken from each request's own `timestamp`. A transcript's
mtime is when the file was last *written* — the end of a session, a later touch, a resume, a
recompaction. **It answers "when did this file stop changing", never "when was this billed".**

**Per file, mtime is wrong on 6 of the 33 — 18%** — and four of those six by six and a half weeks:

| billed | mtime | drift | |
|---|---|---|---|
| 20260803 | 20260804 | +1d | `agent-abcac9b05e84df538` |
| 20260821 | 20260822 | +1d | `cdcc3c5f-e8bf-4720…` |
| 20260707 | 20260824 | **+48d** | `7c6dcf4e-617f-4dae…` |
| 20260709 | 20260824 | **+46d** | `0c8be584-163c-4902…` |
| 20260709 | 20260824 | **+46d** | `dcb4ae77-c236-4319…` |
| 20260709 | 20260824 | **+46d** | `aaa66d6e-1d7a-45e3…` |

The four at +46 are sessions **resumed or recompacted on 20260824**, long after they stopped
billing. **Only one of the six moved the answer**, because the other five landed on days the union
already held or on main-scope files. So *"the two spans differ by one day"* is not the instrument's
error rate — **it is the error rate that survived a union.** An aggregate absorbs per-file error and
reports the residue, which makes an aggregate an instrument too, with a selector of its own.
**Three days stands, for the non-main set.**

So: a peer wrote *"the real span is three days"*; this file said *"six days only"*. **Both are
correct.** Three is the fan-out span (`subagent ∪ workflow`); six is every scope. And the fan-out days are
**disjoint by kind** — subagents on two days, workflow agents on one, never the same day — so
fable-5 inside a fan-out is **three episodes, not a steady leak**. That is a fact neither sentence
could carry, because neither named a population. **Third time this evening that a claim has been
carried by a population nobody named, and the first in which nobody was wrong about the data — only
about which data.**

All dollar figures are estimates computed from transcript `usage` blocks against the rate card
above, with cache multipliers **1.25× (write)** and **0.1× (read)**, both sourced from the same
bundled skill. **An estimate over transcripts, never a bill.** They exclude `<synthetic>` and, at
all-projects scope, `claude-haiku-4-5-20251001`, neither of which is on the card — the tool prints
both exclusions rather than silently dropping them.

### The proposed change is to a file this repository does not own

The fix is one clause in the **user's own global `~/.claude/CLAUDE.md`** — naming `fable` where the
subagent-model rules currently say *"the top tier"*, so the most expensive available model is not
reachable by omission. **That file is the user's. This is a proposal, not a queued item**, and it is
recorded here so it survives the session that found it.

**The correction above changes what is being proposed, not just its evidence.** As first written,
this asked the user to close a hole nothing had fallen into — a tidy-up, easy to decline and
reasonable to decline. What the measured numbers actually support is narrower and stronger: **the
rule the user set on 20260831 — *audits and large analyses ALWAYS run on Sonnet 5* — already says
`model: 'sonnet'` must be passed explicitly because "omitting the parameter is not neutral: it
silently inherits the parent's model".** That rule's own reasoning covers `fable` exactly, and 471
of 618 Pinakes fable-5 requests are the fan-out work it governs. **So the clause is a naming gap in
a rule the user has already taken, not a new rule** — which is a smaller ask and a better-supported
one.

**What this file must not do is decide it.** The subagent-model rules are the user's, the file is
the user's, and the strength of the argument is not a licence to apply it.

---

## Finding 2 — a killed workflow loses every agent that had not returned

**The framing I was handed — *"~21% of reviewer runs die"* — implies a per-agent death rate. It is
not distributed like one, and that is the finding.**

Population: **55 workflow runs, 868 workflow agent runs**, Pinakes project, every transcript on disk.

| Outcome | count | share |
|---|---|---|
| `result` row | 660 | 76.0% |
| `failed` row | 51 | 5.9% |
| **no terminal row at all** | **157** | **18.1%** |
| produced no `result` (157 + 51) | 208 | 24.0% |

**21% is between the two defensible numbers and equals neither.** They answer different questions:
18.1% started and recorded nothing; 24.0% returned no result by any route.

**"Reviewer runs" is not a population that can be isolated.** The journal carries only
`{type, key, agentId}` — no label. Classifying by prompt text with
`review|verif|refut|adversar|critic|judge|skeptic` matched **826 of 868 prompts (95%)**. **A filter
that keeps 95% is not selecting anything.** Write *workflow agent runs*.

**"No resume point" is false, and this is the half most worth correcting.** All 157 orphaned
transcripts are on disk — median **142,236 bytes**, smallest **27,471**, none under 2 KB. Nothing
was lost. The automatic `(prompt, opts)` resume cache simply misses them, so a resume **re-runs**
them. **That is a cost, not a data loss**, and the recovery of a killed pass's findings from
transcripts is the existence proof that the content is readable.

**The distribution is the defect:**

    157 orphans sit in 22 of 55 workflow runs.   33 runs lost nothing.
    wf_d4e3b1ad-3ab   16 of 16 agents   (100%)
    wf_302dd2f0-ede   15 of 19
    wf_403640a2-df3   15 of 17
    wf_b6773dfd-3b4   14 of 18
    wf_c94dd9f2-895   11 of 14
    top 10 runs hold 113 of the 157 (72%)

**Losing 16 of 16 is a whole-workflow termination — a session limit, an interrupt, a crash — not
sixteen agents dying.** The true statement is: *a killed workflow loses every agent that had not yet
returned, and a resume re-runs them.* Different defect, different fix.

**The obvious confound does not apply**: the most recent orphaned journal was written 20260826, so
none of the 157 belongs to a run still in flight.

---

## A third, offered and not yet acted on — the boot context

Measured 20260831 on two freshly-cleared Pinakes sessions: boot context **56,143** and **56,134**
tokens — agreeing to **9 tokens** — re-transmitted on every request. At one session's 48 requests
that is **269,438 price-units, 29.7% of its spend to that point**. It has grown **41,476 → 56,134
(+35%) since 20260728**. Population: the first request of every Pinakes session whose transcript
exceeds 50 KB, **n = 65**. **Measured, current, and with no denominator problem** — which is more
than either finding above could say when it arrived.

---

## The provenance problem this file has, stated rather than hidden

**✅ CLOSED 20260831 23:00 — `tools/agent_spend.py` is on `main`** (landed `e6134e6`, with
`tests/test_agent_spend.py`; a `--scope` flag followed in `4e37ea1` because the first version could
produce only the all-populations figure, so the main-loop share this file cites was unreachable by
the committed instrument). Every number in the corrected table above was produced by running it.
**The problem below is the one that produced the zeros**, and it is recorded as written rather than
rewritten, because the fix landing does not make the account of the failure less true.

**None of the four analyses was written to a file.** Every number above came from an inline
`python3` heredoc run in one session on 20260831, and **that session's context is the only place the
code existed.** The joins, recorded so the numbers are re-derivable rather than merely cited:

| Analysis | Join |
|---|---|
| outcomes | glob `PROJECTS/<pinakes>/*/subagents/workflows/*/journal.jsonl`; key on `agentId`; `started` sets `no-terminal-row` via `setdefault`; `result`/`failed` overwrite |
| prompts | glob the sibling `agent-<agentId>.jsonl`; take the first `type == 'user'` message |
| spend | key on `(file, requestId)`; take **`MAX` output_tokens** across a request's lines — the first line's output is a running partial, and taking it undercounts by **1.7755×** |
| dollars | the rate table above: `in*r + cache_write*r*1.25 + cache_read*r*0.1 + out*r_out` |

**This is the same shape as the finding it documents.** A measurement whose code lives only in a
context is one session-limit away from being a number nobody can check — which is exactly what
*"21% of reviewer runs die"* had already become by the time it reached me.

**And the transcript glob in that table is the defect, written down before anyone knew it was one.**
The spend row says *key on `(file, requestId)`* and never says which files; the outcomes row globs
`subagents/workflows/` explicitly, because that analysis was *about* workflow agents. The spend
analysis globbed main-loop sessions and nothing else — so *"fable-5 requests, workflow agents: 0 of
868"* was not a count of 868 things that came back zero. **It was a count over a set with no
workflow agents in it, printed beside a denominator borrowed from the analysis next door.** The
denominator made it look like a measurement of the very population it had excluded.

**The correction that generalises: a zero deserves the check every other number gets, and usually
does not receive one.** Every other figure in the message carrying these zeros was correct, and
each was checkable against something — a ratio, a rate card, a file on disk. A zero is checkable
only against the *population*, which is the one thing a summary line never carries. **So when a
count comes back zero, print the denominator's provenance next to it, not just its size.**
