## S2 — A census is not a plan (20260825 18:55)

**HIGH — two mutants survived 267 tests because every assertion counted actions instead of ordering
them.** `pairing.pair()` returns a list of actions, and `describe()` — the helper the whole test file
asserts through — reduces it to a census by kind. When the same-path branch stops emitting a
`SoftDelete`, the vanished-path loop re-emits one further down the list, so the wrong plan and the
right plan have an **identical census**: same actions, same counts, different meaning. `documents.path`
is UNIQUE, so the order is the entire behaviour — an `Adopt` applied while the row it replaces is
still active raises `IntegrityError` instead of replacing it. One of the two survived the entire
suite. The generalisable form: **when a function returns a sequence, a test that asserts its
contents has not asserted the sequence**, and a helper that summarises is where that blindness
hides. The fix was a named property (`retires_before_adopting`) rather than a positional
`assert kinds == [...]`, so it states what must hold rather than what happened to be produced.

**A SURVIVED row is a claim about a pair, and here the wrong half was the selector.** The inverted-guard
mutant was killed by *five* tests — just not the one the battery named beside it. Re-running it
against the whole suite rather than the selector is what showed that, and it took one command. The
battery's own README already says this ("either half of which can be wrong"); what this adds is the
cheap procedure: **before believing a survivor, run the mutant against everything, not against its
selector.** A survivor that nothing kills and a survivor whose selector is misaddressed need
different fixes, and they are indistinguishable from the battery's output alone.

**MEDIUM — the first discriminator was wrong, and a test falsified it rather than a reviewer.** The
`doctor` check was designed, reviewed and specified as *"a retired row whose file and matching
sidecar are both still on disk"*. That rule misses the state S2 is named for. When a sidecar's id
changes at a path, the row that gets retired keeps **its own old path**, while the document that has
become unfindable is the one whose sidecar now claims that id somewhere else — so a path-based rule
reports the wrong document and misses the real one. What found it was writing a test for an adjacent
case (a path reused by a different document) and watching it fail for a reason I had not predicted.
The rule is now keyed on the retired **id**. Worth stating because the wrong rule had already
survived a careful adversarial review: **a specification written from the mechanism can be wrong in
the same direction as the code**, and only a case neither party considered separates them.

**MEDIUM — running corrected a confident inference, and the correction changed the build order.** From
the pure function I inferred that a rename chain silently re-mints a published id — a `Mint` for a
document whose sidecar already carried one, which would breach ULID permanence. Running it showed
the crash *preempts* the mint: on `main` the first adoption raises before the `Mint` is ever
reached. The defect is latent rather than shipped. That is not a smaller finding, it is a different
one, and it carries an ordering constraint nobody had written down: **fixing the rename collision
without this fix first would unmask the re-mint.** The inference was sound and the conclusion was
wrong, which is this repository's most-recorded failure shape and was reproduced here in the space
of ten minutes.

**LOW — a condition that cannot be false is worse than no condition.** The first draft of the guard
read `claimed is not None and claimed.document_path != path`. The second term can never be false
where it is evaluated: the sidecar beside that path is the one that disagrees, so the sidecar
claiming the row's id is necessarily a different one. It would have shipped as an unkillable mutant
— a line no test can pin, which reads as care and provides none.

**MEDIUM — I measured the check as free, and it is not. It costs 12–17%.** The first measurement
said `pnk doctor` went 0.822s → 0.818s over 2000 documents and I wrote "free, within noise" into a
fragment. An adversarial reviewer measured +12% on the same corpus, which sent me back to it. They
were right. Re-measured **alternating branch and main against one KB** rather than running each side
once in its own worktree: main 0.7099s / 0.6700s, branch 0.7959s / 0.7823s — **+12.1% and +16.8%** —
and `walk_document_paths` alone is **49 ms** over 1995 documents. The added work is real, it is the
glob, and it is paid only when the KB has retired rows (otherwise the check returns before walking).

**The method is the finding.** Two sequential measurements taken in two worktrees cannot resolve a
10% difference on a machine that drifts by more than that between them — my "before" run happened to
land slow and my "after" fast, and the difference I was trying to detect was smaller than the drift
I did not control for. Interleaving costs nothing and would have shown it immediately. **A/B by
alternation, never A-then-B**, whenever the effect is smaller than the noise you have not measured.

What survives is the comparison that actually mattered: the attempt this replaces measured **2.25x**
(0.746s → 1.682s) and this is about **1.15x**, because the expensive question was never the check —
it was a SHA-256 over the whole corpus and a second `ruamel` parse of every sidecar `_sidecars()`
had already parsed. Reusing that parse and asking the walk for paths alone is what the ratio buys.
"Cheaper by a factor of eight" was the honest claim; "free" was not, and nobody would have caught it
if a reviewer had not run the number I had already published.

**And the exit code is still not a validity signal, demonstrated while verifying this.** Running the
real `pnk doctor` against a healthy 2000-document scratch KB exits **1** — for `embedding` and
`reranker`, because the fake backend is registered inside pytest and not in a plain CLI process.
Two sessions built measurement harnesses on that exit code in one day; this is a third sighting
inside an hour of deliberately watching for it. Assert on the named check row, never on the exit
code.

**HIGH — the fix introduced the exact shape it was removing, and only an adversarial pass saw it.**
Guarding the branch where a sidecar *disagrees* with the row left the ordinary branch alone, so a
sidecar **moved** from one document onto another produced `RefreshMetadata(X, a.md)` beside
`Adopt(X, b.md)`: the same-path loop trusted the index row because nothing beside `a.md`
contradicted it, and the adoption loop followed the sidecar that had walked away. One id, two
paths, one plan. Measured on both sides: `origin/main` raises `IntegrityError` and keeps both rows;
this branch **exited 0**, moved the row to `b.md`, and left `a.md` on disk with no row at all —
indexed yesterday, unfindable today, nothing recorded. **A loud failure turned into a silent one is
the precise regression that condemned the previous attempt at this fix**, and this increment
reproduced it while carrying a commit message about not doing so. Two things made it findable: an
independent reviewer that ran `origin/main` as a control rather than reasoning about it, and a
`UNIQUE` constraint that had been the only thing noticing — by crashing. The lesson is not "guard
the other branch". It is that **a guard written for the case you are thinking about is not a
property**; the repair is `places_each_id_once()`, asserted over every shape the file exercises,
because a helper asserted case by case is a helper nobody runs on the case they did not think of.

**MEDIUM — a property helper that did not implement its own docstring.** `retires_before_adopting()`
was written to assert "no `Adopt` may land on a path this plan retires *later*", and built its
index of retirements with `reversed(list(enumerate(...)))` — so for a path retired twice it kept the
**earliest** position, and a plan that retires a path, adopts onto it, then retires it again passed.
It was doing real work (it is the only thing that kills two of the battery's mutants) and it was
still wrong about the sentence above it. **A named property is worth more than an inline assertion
and is also a second place to be wrong**; the reviewer read the implementation rather than the name,
which is the only way that class is ever caught.

**MEDIUM — the count I published was scoped and I called it complete.** This file said a mutant
"survived the entire suite" and the battery said "the whole suite of 267 tests". 267 was
`pytest tests/test_pairing.py tests/test_sync.py tests/test_doctor.py` — the three files covering
the code — while the suite is 2167. Caught when a planner asked to publish the number in a document
whose whole subject is not publishing counts nobody has run. Re-measured properly, at the exact
commit where the survival was observed, with the mutant applied and the full suite run: **2165
passed, 0 failed.** The claim was true and the denominator was invented, which is the same defect
one level up from the one the paragraph was describing. **State the population, not just the
number** — and when a scoped run is what you have, name the scope.

**HIGH — I reported a defect as open after my own later commits had fixed it, and a planner recorded
it as scheduled work.** S17 (a rename that frees a path a new document then takes) was measured
early, against `origin/main` and against my branch *as it then stood*; both failed, so I filed it as
pre-existing and unfixed. It was pre-existing. But the moved-sidecar guard that came out of the
second adversarial pass — four commits later — fixes it as a side effect, because S17's mechanism is
the same *one id at two paths* shape. Re-measured with a control: at `03e6f86` the walk records
`SidecarError: … appeared after the walk had already read this directory` and the renamed document
is **never indexed**; at `3876b57` it reports `1 indexed, 1 renamed` and the document is active.

**The error is not the measurement, it is the report: a finding taken against a moving branch has a
sha, and mine did not carry one.** It was true when taken and false four commits later, and nothing
in the report let either of us see that. It had already been written into a plan as a two-part fix,
which is one message from a fresh session rebuilding something that works — the failure this
repository's own `CLAUDE.md` records happening twice in two days. **Stamp every cross-session
finding with the commit it was measured at, and re-measure before anyone schedules it.**

And the repair for the claim itself is a test, not a corrected sentence. *"S17 is fixed"* written in
a plan is a fact that decays silently; `test_a_rename_that_frees_a_path_a_new_document_then_takes`
is the same fact that goes red if it stops being true. Confirmed red at `03e6f86` before being
believed.

**LOW — and the same disease in a docstring I had just written.** `_retired_documents` claimed the
pre-commit hook's sidecar "cannot trip it: nothing the hook does retires anything", and the
changelog fragment repeated it. A reviewer measured otherwise: at a **reused** path — a new document
at a name some earlier document held — `sync --sidecars-only` does reach rule (2). The report there
is *true* (the document has no row and `pnk search` cannot see it) and the shipped hook pair never
leaves that state, since post-commit indexes inside the same commit. So the check is right and the
sentence was wrong, which is the more embarrassing half: **an absolute claim written to explain why
a design is safe, in the same paragraph that had already earned the right to a narrower one.**
