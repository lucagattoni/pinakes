## Committing the mutation batteries — a design statement nobody had measured (20260823 07:34)

**HIGH — the sentence that decided this was an assumption wearing a docstring.** `tools/mutate.py`
shipped in 0.27.0 saying *"a battery is a per-increment working file, not a portable artifact"*, in
a paragraph whose actual subject was where the `pytest` key lives. Nothing had measured it, and it
then decided the question for two months by being read rather than by being right.
`plans/20260821_0745-mutation-harness.md` enumerates what it deliberately left open and persistence
is not among them — checked, not assumed. So this fills a gap rather than overturning a position.

The measurement took twenty minutes. Of **81 mutants** across six increments, **78 anchors still
resolved exactly once** a day to a week later, and every one that broke was one whose own code had
changed. **The failure mode of keeping a battery is a refusal, not a wrong answer** — `mutate.py`
resolves every anchor before it writes anything and refuses on 0 matches and on 2. That asymmetry is
what made the question decidable. An argument about whether a claim outlives its proof would not
have resolved; *what does being wrong cost?* did.

**HIGH — and the measurement was aimed at the half that had never broken.** `docs/RETROSPECTIVES.md`
already recorded which half rots, twice in one increment: *"a battery is source that goes stale like
any other, and a SURVIVED row is a claim about a pair — the mutant and the selector — either half of
which can be wrong."* Both my 81-mutant recovery and a peer's five refactor scenarios stress-tested
**anchors**. The **selector** is what historically went stale. The gate resolves both, and the half
that matters is the one the headline number says nothing about. **Check the record for which half
failed before designing a measurement of the other.**

**HIGH — the repair loop produced two broken mutants under best-case conditions, and that is the
strongest evidence against the model, not for it.** Two anchors were repaired here: same day, by the
author, with full context. Both widened `old` from one line to two and **left `new` at the one line
it used to replace**:

| Repaired mutant | What the edit actually did |
|---|---|
| *the prose list loses its exemption* | deleted `minimum=15,` **and** flipped the flag — two changes under a name promising one, and the floor it fell back to sits on the boundary of that sequence's length, so the test may have gone red for the floor |
| *the prose sequence is read in the wrong direction* | deleted `starts_at` and duplicated `minimum=15,` — `keyword argument repeated`, a **SyntaxError at import** |

The second read **KILLED**, in a batch reporting `0 errored`. `classify` treats a *collection* error
as the invalid mutant, and this module is imported **inside** the test rather than at module scope,
so the SyntaxError arrived as an ordinary assertion failure. A confident row about a question nobody
asked — the one thing the tool exists to refuse — produced by the tool, in its own corpus, on the
first day. n=1 in the direction an adversary predicted, and it is the honest cost of the model.

`refuse_a_mutant_that_cannot_compile` now catches the syntax half, before the first write, and it
**earned itself within the hour**: restructuring `check_anchors` staled two mutants in this
increment's own battery and it caught both. `ast.parse` would not have — it accepts `f(a=1, a=2)`
and `compile()` does not, which is exactly the case that got through, so a test pins the
discrimination rather than leaving the choice of `compile` looking like a detail. **The other half
has no guard**: an edit that still compiles and changes two things under a name promising one is
invisible to everything here. Read the diff a mutant produces, never its anchor.

**MEDIUM — a corpus with no inventory can shrink to nothing with every gate green.** None of the
first draft's checks was a *count*, and the sanctioned repair for a property that has genuinely gone
is to delete its mutant — which makes deletion the cheapest path to green during a refactor. Split
a 739-line gate six weeks from now, watch thirteen anchors resolve zero times, delete thirteen
blocks: `./check.sh` green, the battery reads `28 of 28 killed`, and **nothing anywhere recorded
that it was 41.** `mutants = N` per battery, validated in `load_battery`, makes deleting a row a
two-line edit that says so.

**MEDIUM — the argument for keeping them was weaker than it first looked, and saying so changed
which argument to make.** The first draft argued *the claim outlives its proof*. It does not:
re-deriving 41 mutants against a gate is an afternoon. What is unrecoverable is the **reasoning
about which mutants were worth writing** — and the durable channel for that already existed. A
per-mutant table can go in a `retro.d/` fragment, and `docs/RETROSPECTIVES.md` has exactly **one**,
against 93 commits that speak of a mutation pass. The channel existed, worked, and was used once.
That is the case for a directory, and it is a better one than *there was no channel*.

**MEDIUM — consolidation is a check that scattering cannot perform.** Merging six scratchpad
batteries into three files surfaced what no individual battery could: one battery entirely
superseded by a later copy of itself, and **two mutants byte-identical in `file`, `old`, `new` *and*
`kills`** under different names — the same edit counted twice in a report reading `29 killed`.

**MEDIUM — a directory nothing reads is the failure this repository keeps recording.** A template
version that meant different bytes in every commit; a verification table where 61 of 98 test paths
did not resolve; a `docs/GUIDE.md` whose commands no longer ran. So `tests/test_batteries.py` reads
them, in 0.05s. **Its cost, stated rather than discovered later:** a refactor that moves a mutated
line turns `./check.sh` red until the battery is repaired — measured at 2 repairs per 81 mutants per
week, minutes each. The assertion names re-anchoring **before** deletion, because deleting a mutant
to green a gate is the silent damage this arrangement invites.

**MEDIUM — the corrections a review pass made to this file's own claims.** Each was a number stated
with more confidence than the data carried:

- *"the single comment-bearing anchor in the set was the one that went ambiguous"* — **wrong on both
  halves.** Three of the 81 anchors carry a comment; the one that went ambiguous carries none. One
  comment-bearing anchor did rot, in the superseded battery. The generalisation drawn from it — that
  the fragile shape is knowable in advance — went with it.
- The mcp battery was described as spanning six files. It spans **seven**; `check.sh` was in neither
  enumeration.
- The section for `tools/fragments.py` was labelled 0.28.0; the property shipped in **0.27.1**.
- Its header was a comment that had **migrated** during consolidation, claiming "the two gates" and
  a control that had gone to the other file. A comment attached to the wrong mutant is silent, and
  the comments are the reason these files exist.
- A mutant named *"ci.yml guards the gate with `|| true`"* appended `&& echo ok`, which does not
  swallow the failure the name promises. The **name is the only guard** against an anchor that still
  resolves while the semantics moved, so a name that misdescribes its own edit disarms it.

**MEDIUM — "regression asset" is the one thing this cannot be, and the README now says so.**
`report()` exits 0 when mutants SURVIVE, deliberately — *"It is not a harness failure, so this exits
0 — read the rows."* Nothing here changes that, and the committed gate never runs a battery: it
checks that strings resolve. Anything CI-shaped built on top needs its own check on the survivor
count. **And the denominator belongs beside the claim**: four batteries, four targets, all under
`tools/`; **no module under `src/`** has one, and no invariant in `docs/INVARIANTS.md` is covered.
The covered files change 3–11 times a month, `cli.py` 58 and `sync.py` 40. A coverage index with a
hidden denominator is the exact defect this repository keeps catching in its own gates.

**LOW — `--check-anchors` reads the working tree, not `HEAD`, and the difference is the point.** A
run refuses an uncommitted target so `git checkout <file>` stays a safe recovery after a hard kill.
Nothing is written in check mode, so inheriting that refusal would have bought nothing and disarmed
the check in the one moment it is wanted. Two guards that look alike had different reasons, and
copying the reason across would have made the second useless.

**LOW — three ways the first draft of a "report every failure" contract reported fewer.** The
test-file refusal *raised* inside the per-battery loop, discarding the problems already collected
and never reading the batteries after it — which is the run's behaviour, and the thing this mode is
defined as not being. The claim set keyed on the battery path *as typed*, so one battery named twice
under two spellings was a false double-claim. And stdout was flushed only on the problem path, so a
refusal printed above the summaries it contradicted.

**LOW — the flagship test passed when half of what it pins did not happen.** The two stale mutants
were named `gone` and `also gone`, and `"gone: …" in stderr` is satisfied by the `also gone` line
alone. Reporting only the *last* problem passed a test whose docstring calls reporting *every*
problem "the difference from a run that matters most". **Two fixture names where one is a substring
of the other is a silent half-assertion**, and the same shape hides anywhere a test asserts on
substrings it also chose.

**LOW — the test helper that wrote both batteries to the same filename.** `battery()` hard-coded
`battery.toml`, so the first "two batteries" test built the second by calling it again and copying
the result — silently overwriting the first. The overlap test passed anyway, because both files
claimed the same target either way; the **control** — two batteries claiming *different* files — is
what exposed it. A control earns its place by failing for a reason the pin cannot.
