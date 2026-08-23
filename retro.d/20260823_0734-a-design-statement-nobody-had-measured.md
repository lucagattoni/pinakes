## Committing the mutation batteries — a design statement nobody had measured (20260823 07:34)

**HIGH — the sentence that decided this was an assumption wearing a docstring.** `tools/mutate.py`
shipped in 0.27.0 saying *"a battery is a per-increment working file, not a portable artifact"*, in
a paragraph whose actual subject was where the `pytest` key lives. Nothing had measured it. It was
then load-bearing for two months of discarded batteries, and it decided the question by being read,
not by being right. `plans/20260821_0745-mutation-harness.md` says "per-increment battery"
throughout and **never decides persistence** — checked, not assumed.

The measurement took twenty minutes. Of **81 mutants** across six increments, **78 anchors still
resolved exactly once** a day to a week later. Every one that broke was one whose own code had
changed. The single *comment-bearing* anchor in the set was the one that went ambiguous, and
comment-bearing anchors exist only where the code line alone is not unique — so the fragile shape is
knowable in advance.

**The failure mode of keeping a battery is a refusal, not a wrong answer.** `mutate.py` resolves
every anchor before it writes anything and refuses on 0 matches and on 2. That asymmetry is what
made this decidable: a stale battery costs a maintenance prompt, and cannot produce a false `KILLED`
or a false `SURVIVED`. An argument about whether the claim outlives its proof would never have
resolved; the question *what does being wrong cost?* did.

**MEDIUM — the argument for keeping them was weaker than it first looked, and saying so changed
which one to make.** The first draft argued *the claim outlives its proof*. It does not: re-deriving
41 mutants against a gate is an afternoon. What is genuinely unrecoverable is the **reasoning about
which mutants were worth writing** — which breakages are plausible, which one is the shipped defect
the increment closed, and (twice here) which exist only because a first-draft guard-test turned out
to be a tautology. None of that is in the code. So the comments are the artifact and the mutants are
the index, which is the opposite of how the files were written.

**MEDIUM — consolidation is a check that scattering cannot perform.** Merging six scratchpad
batteries into three files surfaced things no individual battery could show: one battery entirely
superseded by a later copy of itself, and **two mutants byte-identical in `file`, `old`, `new` *and*
`kills`** under different names — the same edit counted twice in a report that read `29 killed`.
Both were invisible while the files sat apart.

**MEDIUM — a directory nothing reads is the failure this repository keeps recording.** A template
version that meant different bytes in every commit; a verification table where 61 of 98 test paths
did not resolve; a `docs/GUIDE.md` whose commands no longer ran. Committing batteries without
reading them would have joined that list, so `tests/test_batteries.py` reads them: anchors resolve,
`kills` selectors name tests that exist, no file is claimed twice, every battery is named for a file
it mutates — and a **non-empty control**, because all four iterate a glob and a moved glob would
make them vacuously green. 0.05s.

**The cost, stated rather than discovered later:** a refactor that moves a mutated line now turns
`./check.sh` red until the battery is repaired. Measured at 2 repairs per 81 mutants per week, each
a few minutes, and the assertion's message names re-anchoring **before** deletion — because deleting
a mutant to make a gate green is the silent damage this arrangement invites.

**LOW — `--check-anchors` reads the working tree, not `HEAD`, and that is the whole point.** A run
refuses an uncommitted target so that `git checkout <file>` stays a safe recovery after a hard kill.
Nothing is written in check mode, so inheriting that refusal would have bought nothing and disarmed
the check in the one moment it is wanted: mid-refactor, before the commit. Two guards that look alike
had different reasons, and copying the reason across would have made the second one useless.

**LOW — the test helper that wrote both batteries to the same filename.** `battery()` hard-coded
`battery.toml`, so the first "two batteries" test built the second by calling it again and copying
the result — silently overwriting the first. The overlap test passed anyway, because both files
claimed the same target either way; the *control* — two batteries claiming different files — is what
exposed it. A control earns its place by failing for a reason the pin cannot.
