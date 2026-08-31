## A gate green on `main` and red on the tree `main` is about to become (20260830 15:04)

**MEDIUM — three sessions measured one gate within an hour and got three answers, and every
measurement was correct.** The planner reported `release_order_gate` red and asked for a fix. A
second session ran it on `main` at `37689f1`, measured **green**, and — instead of reporting the
planner mistaken — said so and named its sha. The planner then re-measured, found it had reported a
property of its own uncommitted worktree as a property of `main`, and corrected itself unprompted.
The resolution came from neither: **reproducing the failure before writing a line.** Copying the
three documents to a scratch tree and appending 0.31.0 exactly as the post-publish sweep does
produced the planner's two failure lines verbatim.

**So the accurate statement is one none of the three had: the gate is green on `main` and red on the
tree `main` is about to become.** Both PyPI sequences declare `newest_may_lag`, so while 0.30.3 is
the *tail* its absence reads as latency; adding 0.31.0 makes it an interior hole, which lag does not
cover. **A blocker observable only from a tree that does not exist yet is still a blocker** — and it
is invisible to exactly the check a careful reviewer runs, which is `git rev-parse HEAD` followed by
the gate. This is the third measurement-over-a-moving-target failure recorded in one day and the
only one where the target moved *forward*: the other two moved backward, a suite read across a
release cut and a `TZ=UTC git log --date=format:` printing a committer-offset time as UTC.

**LOW, and the reason the fix needed three tests rather than one: a declared absence and a hole
nobody noticed have the same exit status.** The green run's `(declared absent: 0.30.3 — …)` sentence
is the entire difference, so one mutant silences that sentence and nothing else, and it is killed by
the real-documents test rather than by any of the new ones. The control that matters strips the
declaration and requires red on **exactly** the two PyPI sequences — built on a fixture rather than
the real documents on purpose, because before the sweep lands the real tree is green with or without
the declaration, so a control there would prove nothing today and something different tomorrow.
**A test whose meaning changes when an unrelated commit lands is not a control.**

**And the scope is the whole claim.** 0.30.3 is a real release *document* and only never a published
*artifact*; a blanket exclusion would have made the gate green by erasing that distinction. All
three new battery rows attack the scope rather than the mechanism — the mechanism was already
covered by 0.11.0's rows — because what is new here is *which* sequences carry the declaration, and
that is data, which no type checker reads.
