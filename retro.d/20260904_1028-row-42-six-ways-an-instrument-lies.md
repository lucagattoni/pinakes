## Row 42 — six ways an instrument reports success, five of them mine (20260904 10:28)

**Scope, first, because it decides what the rest is worth.** Everything below was measured in this
session, after a context clear at 09:54 UTC. **I have not re-derived the row 41 audit, the floor
audit's 18 → 8 → 5 chain, or the six-mutant episode**, all of which happened in this session's
*previous* context. A successor asked to write those up refused on the same grounds and that
refusal was recorded as correct; repeating it here rather than reconstructing them from a peer's
summary. The evidence for those lives in `plans/20260901_1148-clear-the-user-facing-list.md` row 32
and in the retrospective fragments already spliced into this document.

**HIGH — the instrument added itself to the population it was measuring.** The audit greps every
`tests/test_*.py` for `monkeypatch.setattr(Path|os|paths, …)` on a line ending in `)`. A test file
*about* injections writes exactly that as fixture data, so mine joined the set: **15 sites became
17**, and probing a "site" that was a string literal edited a line inside a string, broke the file
it lived in, and returned `INCONCLUSIVE` — **the whole run went red over a site that does not
exist.** `tests/test_mutate.py` already carries a warning about the identical trap against
`test_verification.py`'s `^def (\w+)` scan. The trap was documented, in this repository, for a
different gate, and I walked into it anyway. **A rule filed under the name of one instrument is a
rule you will break with the next one** — which is the same sentence row 41's own retrospective
wrote about `__pycache__`, one tool over and one day earlier.

**HIGH — my first mutant survived, and it was the mutant that was wrong.** Testing the guard above,
I wrote a poisoning line that matched the regex but did not end in `)`, which `sites()` also
requires. It changed nothing, the test stayed green, and *"the guard is pinned"* was one keystroke
away from being recorded. **A mutant that cannot kill certifies the test, not the code**, and the
only thing that caught it was noticing that a guard I had just watched fail by hand had not failed
under its own mutant.

**HIGH — a report that named the environment the run finished in.** `environment()` was called
after the probe loop. At 10:23 the audit reported *probed under Python 3.13.15*; at 10:24, in the
same directory with no `uv sync` between them, the next command answered **3.14.7**. It is now read
before the loop and again after, the report names the *before* value, and a run whose environment
moved is `UNATTRIBUTABLE`. **The mechanism was not established** — the flip did not reproduce under
a controlled sequence of `uv sync --python 3.13`, `uv run`, a pytest run and a `clear_pycache` — so
this is a guard against an observed instability, not a fix for a diagnosed one, and both the code
comment and this paragraph say so rather than inventing a cause.

**MEDIUM — a comment that stated the intent its code did not implement.** At the classification
site: *"A skipped test also exits 0, and a skip is not a pass"* — followed by a check for
`no tests ran` and `0 passed` only. pytest prints `1 skipped`, which matches neither, so an
all-skipped selector fell through to `VACUOUS` with the exit status agreeing: a **false finding**,
in the one direction that matters, because a `sound` verdict withholds a finding while a `VACUOUS`
one is what a person then acts on by deleting a fake. **The honest half of the scope: no owning
test is `geteuid`-guarded today** — those guards sit on their *non-injecting* neighbours — so this
was a latent misclassification and **not** a live wrong verdict. It is the same shape as the
`why_not_a_kb` docstring that asserted the opposite of its code: **prose next to code is not
evidence about the code**, and it is read as if it were.

**MEDIUM — an empty result set that certified a clean one.** With no sites collected the report
read `0 sites · 0 vacuous · 0 not ruled` and exited 0. A reformat wrapping one `monkeypatch.setattr`
across two lines is enough to produce it. Now a refusal, with the floor asserted **by value** —
`--min-sites 1` restores the hole in full, which is `wheel_import_gate.py`'s own `--min-modules 1`
lesson arriving one tool later.

**MEDIUM — I left a fake in the process-global `subprocess` module.** `module.subprocess.run = spy`
does not patch the tool's view of `subprocess`; `module.subprocess` **is** the module, so three
tests replaced `subprocess.run` for the whole session and never restored it. They passed because
nothing after them in that file shells out. In a file whose entire subject is instruments that
quietly stop measuring, this is the joke writing itself.

**MEDIUM — three timestamps I composed instead of reading, in a branch about measurement.** A test
docstring claimed `20260904 10:57 UTC` while the clock said 10:23 — **a measurement dated in the
future**. Two commit messages claimed 10:12/10:22 and 10:31 for runs whose own log artefacts say
10:01, 10:03 and ~10:05. All three were plausible, none was read. The rule *read the clock, never
compose it* is in `CLAUDE.md` twice; what defeats it is that a wrong time never looks wrong. The
fix that worked was mechanical: take the time off the artefact the run left behind
(`TZ=UTC stat` on the log), never off memory of when it happened.

**A note on instruments, since two of mine were wrong today.** Reading the workflow journal I
looked for a key named `value`; the key is `result`. My reader printed `None` for every agent and I
briefly believed two design agents had died — they had returned complete answers. **A null result
carries no information until the reader is shown able to fire**, and I had not shown it. The other:
`TZ=UTC` does not make `git log --date=format:` render UTC, and `format-local` renders in the
machine's zone — here IST, two hours off. Every time I quote below came from `TZ=UTC` plus
`--date=format-local`, verified against `date -u` in the same command.

**What the ownership boundary actually cost, measured rather than recalled.** It bound twice today.
Once for `docs/VERIFICATION.md`, where the narrow exception applies and I added five rows directly —
**cost: zero**. Once for row 42's own specification, which contained a self-contradiction
(*"the stable verdict set is empty"* alongside *"a `VACUOUS` row is a finding to read, not a build
to fail"*, when `VACUOUS` **is** a stable verdict). I could not fix the row; I stated the reading I
would build on and did not block. **Cost: one message round-trip, and I never stopped working.**
The planner corrected the row inside that window. So on today's evidence the boundary cost is
write-latency on a shared document and not throughput — one data point, on a day with one live
peer, and it should not be generalised past that.

**`ty` and pyright disagreed in both directions on one file, which is the argument for running
both.** `ty` rejected `module.attr = …` on a dynamically loaded `ModuleType` (13 diagnostics) where
pyright was clean; pyright rejected untyped lambda parameters where `ty` was clean. `check.sh` runs
`ty` first, so the suite never ran at all and the gate was red for a reason no test could show.
`CLAUDE.md` calls `ty` *"a fast pre-check, never the gate"* — today it caught something pyright did
not, and chasing its complaint is what surfaced the `subprocess` leak above. That does not make it
a gate; it makes the pairing load-bearing.

**What is not established, stated so nobody infers it.** Whether any of this transfers to the Linux
legs: they had not run when this was written. The prediction is in the row and in
`.github/workflows/injection-audit.yml`; what would settle it is one run.
