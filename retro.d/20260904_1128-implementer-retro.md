## The implementer's seat — one session, measured (20260904 11:28)

**Written at the planner's request, for the user's framework on how development here actually
works. The witness is bounded and the bound matters**: this session was cleared at 10:51 UTC, told
"you are the coder", and did one thing — harvest `ci-runs.tsv` and land it at `a52ea93`. Everything
below is from that session. **Three of the six questions asked reference measurements a *previous*
session took; those are marked skipped rather than answered.** Answering them from a predecessor's
handoff is precisely the failure this session spent its morning correcting.

### Where the time went

| activity | wall clock | what it was |
|---|---:|---|
| the extraction itself | **56 s** | `gh run list` + 113 × `gh run view`, eight-way parallel |
| gates | **7 min 14 s** | three `./check.sh` runs, 2502 tests each |
| the audit fan-out | **17 min 4 s** | 5 agents, 451k tokens, 130 tool calls — none of it my attention |
| peer coordination | 4 messages out, 4 in | **zero blocking waits**; work always ran in parallel |

**The headline is the ratio: 56 seconds to extract, roughly 24 minutes to establish that the
extraction could be trusted.** The harvest was the cheapest thing that happened. Everything
expensive was verification — and the verification is what made the file usable, because it found
the two things that would have misled a reader.

**Two of the three gate runs — 4 min 40 s of the 7 min 14 s — were caused by `main` moving, not by
anything I changed.** The tree I was gating changed underneath a green result twice.

### What the two-session split cost, and bought

**Bought:** the planner reserved the row, decided the path, and named the instrument *before this
session existed*. I never had to ask where the output belonged or escalate a structural question.
That is the whole case for the split and it is a strong one — the decision was waiting for me.

**Cost:** two landings mid-flight, each forcing a full re-gate and a patch regeneration. The second
one invalidated a patch I had **already verified applied**. About five minutes, and it was
structural rather than careless.

**Skipped:** whether the boundary cost "zero and one round-trip" is representative. That
measurement was a predecessor's, not mine, and I have one session's n.

### Instruments, ranked by defects caught per unit of my attention

Only the ones this session actually ran. **Skipped: the mutation batteries and the injection audit
— this session ran neither, and ranking an instrument I did not use is how a framework acquires a
confident wrong row.**

| instrument | my attention | caught | verdict |
|---|---|---|---|
| the audit fan-out | ~0 (backgrounded) | **2 real disclosure gaps, plus 1 false cause killed** | earned it, decisively |
| `land.py`'s gate marker | seconds | refused nothing — **forced two correct re-gates** | earned it; the refusal *is* the yield |
| CI on `main` | ~0 (backgrounded) | 0 | the only instrument running the floor interpreter |
| `check.sh` | **7 min 14 s** | 0 | correct precondition, zero detection *for this change* |
| `shared_file_overlap.py` | seconds, twice | 0 (reported none, twice) | two nulls rank nothing |

**One caveat I want on the record, because the table invites the wrong reading.** `check.sh` caught
nothing for me and *could not have* — I added a `.tsv`. Its cost was real and its yield was zero,
and that is a correct outcome for this change rather than an indictment. **Ranking gates by their
yield on a single change is how a project deletes the gate that saves it next week.**

### The review fan-out, at n=1

It cost 451k tokens and 17 minutes I did not attend to. It returned **zero defects across 793 × 15
cells** and **two in the prose around them**. Worth it — because the failure mode of a dataset is
not a wrong cell. It is a true sentence that licenses a wrong reading.

**The value was concentrated in one lens of four.** Three lenses re-checked things already true by
construction: row fidelity re-verified fields copied verbatim from a payload, and the build script
had already asserted field counts. The fourth attacked **a claim I had made in prose**, and that is
where everything was. **What I would change first: point the lenses at the claims, not at the data.
A build script can assert its data; it cannot assert its author's sentences.**

**The judge earned its separate, more expensive call.** My own auditor proposed a *cause* for the
missing release — that a tag made through the Releases API does not fire the push event. It was
plausible, and I had no reason to distrust my own agent. The judge refuted it with the auditor's own
comparison set. **Left alone, I would have published it.**

**Truncation is value-biased, and it hit the lens that mattered.** The returned result truncated
mid-run and I had to read `journal.jsonl` to recover the completeness lens's findings — the only
lens with findings. A fan-out that reports by summary loses its most valuable output first, because
the lens with the most to say is the longest.

### Which written lines actually changed my behaviour

The operative ones, all of which I can point at an action for:

- **The `land.py` rule with its executable guard** — I did not hand-merge, and the marker refusal is
  why I re-gated instead of assuming a green result still applied.
- **The ownership table** — I did not touch `README.md`, and I went *looking* for a delegation,
  which is the only reason I recognised one sitting in a commit message.
- **"Read the clock, never compose it"** — produced a correction directly: the handoff's "UTC" stamp
  was local time.
- **"A null result carries no information"** — made me confirm my `failed_steps` selector had fired
  23 times before trusting its zeros.
- **"A clean auto-merge is not a correct merge"** — made me re-read the merged README, which is how
  I found my verified patch had gone stale.

**What I read past:** the naming and versioning tables, the release procedure, and most of the long
incident narratives. Correctly — I was not releasing. But **I had to read all 455 lines to learn
that**, and extracted perhaps six operative ones.

**The operative lines share a shape: a rule with a mechanism attached.** The narratives — which
release was red, which claim was wrong on which day — I could not act on and did not retain. That is
the concrete answer to "which lines did work": **the ones stating an invariant and the failure it
prevents.** The ones recounting an incident changed nothing I did.

### What would have made today faster without making it worse

Not "land less". The fix is smaller and it is mine: **a verification should carry the base it was
taken against.** I verified a patch applied, reported that it applied, and twenty minutes later it
did not. Nothing was false when I said it — it had a shelf life I failed to state. Writing *"applies
to `db65f5f`"* costs nothing and converts a surprise into a visible expiry.

### On the planner's hypothesis — agree on corrections, disagree on the clock

The planner proposes that the day's bottleneck was **the cost of establishing what was true**, not
review capacity or ownership. From this seat that is **half right, and the half it misses changes
the prescription.**

**Every correction was truth-cost shaped** — 791→793, the mislabelled UTC stamp, the re-run claim,
the `v0.1.0` gap, the refuted cause. Five for five.

**The clock went somewhere else.** Twenty-four minutes verifying against fifty-six seconds
extracting, and five of seven gate minutes to a base that moved. **Truth-establishment dominated the
corrections; contention with a moving base dominated the wall clock.** Those have different fixes,
and a framework that merges them will prescribe the wrong one. The planner sees corrections because
corrections are what reach them; I see wall clock because waiting is what reaches me. **Both
denominators are real and neither is the whole** — which is itself the argument for asking the other
seat rather than reasoning about it.

### On the planner, since asked directly

**I did not witness four of the five failures listed** — the discriminator that would have regressed
3.13, the row ranked on an untested premise, the four landed rows reading open, the landing over a
red gate. They are not in my session, and **I will not confirm them from a message.** Confirming a
peer's account of an event I did not see is the exact move this fragment argues against, and it
would be worse here because the account is self-critical and therefore easy to accept. What I
witnessed cost about five minutes and was structural. Against that, the reserved README row saved
this session from having to ask where its own output belonged.

### What I got wrong

1. **Guessed the gate-marker directory before reading `land.py`.** Cost seconds; same class as
   everything else here — asserting a location instead of reading one.
2. **Reported a patch as applying cleanly without naming the base.** See above.
3. **I wrote "every ref, every workflow, whole history."** True about runs, and it would have let a
   reader take the 63 `Release` rows as the release history with the repository's **first release
   silently missing and no failure row to flag it**. I wrote that sentence, I re-read it, and I did
   not catch it. A fan-out did. **The strongest argument for review in this fragment is that its
   target was my own prose, not my code.**
