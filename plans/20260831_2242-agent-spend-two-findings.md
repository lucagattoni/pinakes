# Two findings about what agents cost here — and what each one is *not*

**Measured 20260831 21:45–22:05 UTC by a peer session, then corrected against my own second-hand
version of them before anything was written down.** Both reached me as one-sentence claims. **Two of
the four things in those two sentences were wrong**, and asking rather than relaying is the only
reason this file is not another entry in § *six wrong claims in one day*.

| What I was about to write | What holds |
|---|---|
| *"`claude-fable-5` costs about 2× opus-5"* | **Exactly 2.00×**, on both input and output. Understated, not overstated |
| *"…and nothing stops an audit fan-out landing on it"* | True as a **gap**. **Never once realised** — 0 of 868 workflow agents, 0 subagents, ever |
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

**What must NOT be written: that anything has ever fallen into this hole.**

    fable-5 requests, main-loop sessions : 315   (147 of them Pinakes)
    fable-5 requests, subagent runs      : 0
    fable-5 requests, workflow agents    : 0 of 868

Every fable-5 request in the corpus — all projects, 50 days — was a main-loop session someone chose
deliberately. **This is an unguarded path, not a realised cost.** Its share of dollars is **3.42%
across all projects** ($127.85 of $3,733.05 est.) and **3.08% in Pinakes** ($90.88 of $2,950.93).
**A figure of 3.78% circulated and is not what the data now gives — do not write it.**

Both dollar figures are estimates computed from transcript `usage` blocks against the rate card
above, with cache multipliers **1.25× (write)** and **0.1× (read)**, both sourced from the same
bundled skill. **An estimate over transcripts, never a bill.**

### The proposed change is to a file this repository does not own

The fix is one clause in the **user's own global `~/.claude/CLAUDE.md`** — naming `fable` where the
subagent-model rules currently say *"the top tier"*, so the most expensive available model is not
reachable by omission. **That file is the user's. This is a proposal, not a queued item**, and it is
recorded here so it survives the session that found it.

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
