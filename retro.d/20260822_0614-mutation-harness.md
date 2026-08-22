## The mutation harness — turning the last unguarded step into a tool (20260822 06:14)

`plans/20260821_0745-mutation-harness.md`, in one increment. The precedent is `tools/land.py`: when
prose has failed repeatedly against a class of mistake that fails *silently*, the rule stops being a
rule and becomes a tool.

**HIGH — a skipped test and a passing test are the same exit code, and this repository skips
constantly.** Not in the plan; found by measuring pytest before writing any code. A selector whose
tests all skip exits 0, which is byte for byte the SURVIVED signal, and Pinakes skips on a missing
extra by design (`pdf`, `paid`, `model`, the three-leg CI matrix). A battery aimed at one of those
on a `[light]` checkout would have reported *every* mutant in it unpinned — a confident, wrong claim
about exactly the assertions a mutation pass exists to check. The mirror case is worse and equally
invisible: a selector that is **already red** reports KILLED for every mutant aimed at it. One
pre-flight run per selector closes both, before any file is written.

**HIGH — `SIGTERM` skips `finally`, so a `try/finally` restore is not a restore.** Measured, 1 of 1.
`SIGINT` already raises `KeyboardInterrupt`, which is why the hazard is invisible to anyone who only
tests with Ctrl-C — and why the first version handled only `SIGTERM` until the harness's own battery
showed that dropping `SIGHUP` and `SIGQUIT` was a one-word edit no test could see. `SIGKILL` cannot
be handled at all, which is the real reason the plan's *refuse if the target differs from `HEAD`*
step is not a formality: after a hard kill the only recovery is `git checkout <file>`, and the
refusal is what makes that recovery correct rather than the seventh instance of the trap.

**MEDIUM — the T3 trap reproduces 6 times out of 6, and its test must not race the clock.** A
same-length mutant (`min(value, MAX)` → `max(value, MAX)`) written in the same wall-clock second as
the previous compile passes every test, because CPython validates a `.pyc` on
`(mtime-to-the-second, size)`. Reproducing it *first* is what made the test honest: the obvious test
— assert the same-length mutant is KILLED end to end — goes green on a slow machine with the
invalidation deleted, because the second boundary is crossed anyway. Two tests replace it. One
asserts no bytecode cache **exists** during a mutation, which has no clock in it at all; the other
forges the stale condition with `os.utime` and watches the mutant vanish, so the clearing has a
control rather than being ceremony.

**MEDIUM — pytest's `<error>` tag covers two opposite events, and conflating them threw away real
kills.** A *collection* error is the invalid mutant: nothing ran, no assertion was tested. A *setup
or teardown* error is a real node the mutant broke on the way in or out — and in this repository
fixtures build indexes, manifests and KBs out of `src/`, so fixture-mediated detection is the common
shape rather than a corner. Treating both as ERRORED, and testing that before failures, reported a
mutant that tripped a fixture *and* failed a plain assertion as *"the mutant did not run"*, tallied
`0 killed`. The two are now told apart structurally — a collection failure carries no `line`
attribute — rather than by matching pytest's message text.

**The correction that mattered more than the finding.** The reviewer who filed that one also
proposed the fix: route setup and teardown errors into KILLED. An independent skeptic, asked only to
refute the finding, confirmed the defect and rejected the remedy — routing them into KILLED would
manufacture the false green the tool exists to prevent, because no assertion fired and nobody may
write *"pinned by test X"* for a fixture noticing something. The shipped fix keeps the conservative
direction and repairs only the *sentence*. **An adversarial pass is worth more when the verifier is
allowed to disagree with the finder's remedy as well as with the finding.**

**The shape that recurred three times: a guard the CLI cannot reach.** Pointing the tool at itself
found, in three separate rounds, four clauses that no battery-driven test could kill — the second
anchor check inside `applied()`, `classify`'s `timed_out` and `setup_errors` branches, and the
report's *only-a-KILLED-row-may-name-a-killer* guard. Each is redundant against the code as it
stands today and each guards a state one line of drift away. Every one surfaced as a **SURVIVED
row**, which is the row the tool exists to print; none would have been visible to a reviewer reading
the diff. They are kept, and each gained a direct test on the constructed state rather than being
deleted as dead code — redundancy nothing tests is indistinguishable from redundancy that has
quietly stopped working.

**Twice, the battery's own selectors were the thing that was stale.** Both times a guard read
SURVIVED because the battery still named the test that existed before the fix, not the one written
for it. The lesson is narrow and mechanical, and it is about the battery rather than the code: **a
battery is source that goes stale like any other, and a SURVIVED row is a claim about a *pair* — the
mutant and the selector — either half of which can be wrong.** The third time, the anchor pre-flight
caught it before a single mutation ran, which is the whole argument for hoisting that check.

**What the tool still cannot see.** A survivor is a claim that wants checking by hand — the record
holds two increments where a mutant that did not reproduce the real prior logic was briefly taken
for a result, and the E7 session's own control mutant survived because every assertion imported the
constant it compared against. A mutation result implicating a file the mutant never touched is a
result about the harness, not the code, and nothing here detects that.

**The exit criterion, met the only way it could be.** The tool was run against itself: 25 mutants,
each disarming one of its own guards, **25 killed, each by the test named beside it**. Before that,
two mutants of `src/pinakes/graph/traverse.py`'s caps, both killed, tree clean afterwards — because
a tool that has only ever been run on its own fixtures has not been run.
