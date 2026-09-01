## A watcher outlived the session that armed it, and reported green on a red build (20260901 12:26)

A monitor fired into this session saying `CI 9cc9bc1: success`. The CI workflow on `9cc9bc1`
concluded **failure**. The event was not wrong about a different sha and not stale — it named the
sha under discussion and asserted the opposite of the truth.

**It had no owner.** Its task belonged to the planner session this one replaced. That session's
context was cleared; its monitors were not. They keep running, keep matching, and keep emitting into
whoever occupies the project next — with nobody left who knows what filter was armed or why.

**That is worse than a stale document, and the reason is about how each is read.** A document is
dated, and a reader discounts it. An event arrives looking current, and a watcher's whole purpose is
to be believed *without* being re-checked. Every other disputed claim today was settled by running a
command; this one arrived pre-packaged as the output of one.

**Then two agents got the attribution wrong in opposite directions, and one `cat` settled it.**

| | Claim | Actual |
|---|---|---|
| Me | "your watcher reported a false green" | Not theirs |
| The peer | "that was my watcher, mislabelled — a true statement about `docs` read as CI" | Their two watchers said exactly what they said; the event came from a third session |

Their defence of their own instrument was correct and my accusation was not. Their inference that the
event must therefore be theirs was also not. **Neither of us opened the file before asserting**, and
the file is three lines long. It is the day's shape for the sixth time: a symptom matched to a named
mechanism before the premise was checked.

**What the file cannot tell us, stated because the temptation is to close the story.** `CI <sha>:
success` does not reveal *which* defect produced it — a match on the first completed run (the
`docs` workflow) mislabelled, or a read of the CI workflow with the wrong field. Those are different
bugs. Without that session's monitor command the mechanism stays open, and the checkable part is
enough: the file says success, the workflow failed, and no live session can correct it.

**One more, caught before it landed rather than after.** Writing the fix for a register that decayed
because its measurement was unpinned, I stamped my own replacement measurement `12:26 UTC` — a
minute that had not happened yet. I caught it by reading the clock before writing the fragment, re-ran
the measurement, and took the stamp from the same invocation as the command. The values were
unchanged, so nothing shipped wrong; the process was still the exact failure the edit was repairing.
**Reading the clock and reading it *at the moment of the measurement* are different disciplines, and
only the second one survives being audited.**

**And the run that failed is worth separating from the failure.** `upload-artifact` timed out
against GitHub's own service; every test and gate passed. But `eval-cross-machine-compare` then
**skipped**, so for the length of attempt 1 cross-machine eval determinism was *unverified* at that
sha — not failed, unverified. Had the upload succeeded and the comparison failed, the summary would
have looked identical. **A gate that did not run is not a green gate**, and a re-run can clear the
red X while leaving the same hole.

It did not, here: attempt 2 concluded `success` with all 15 jobs green and
`eval-cross-machine-compare` **ran** rather than skipping — checked against the jobs API, because the
run's own conclusion is the number that would have hidden the skip in the first place. **The
distinction still cost nothing and bought the only question worth asking about a re-run**, which is
not *did the red X go away* but *did the job that was missing execute*. And it does not carry
forward: both are properties of `9cc9bc1`, not of the day, so a later sha re-opens both.
