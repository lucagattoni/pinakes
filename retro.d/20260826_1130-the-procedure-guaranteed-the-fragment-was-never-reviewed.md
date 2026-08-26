## The review step ran before the fragment existed, so the fragment was never reviewed (20260826 08:00)

A peer measured that **no adversarial pass in this repository's transcript corpus has ever opened
the `changelog.d/` or `retro.d/` fragment its own increment wrote**, and that passes open only
**207 of 248** files their increment changed — with `src/pinakes/__init__.py`, where `__version__`
lives, opened by **none of the 41 passes** over the mutation-batteries increment.

**MEDIUM — the cause is not inattention, it is the order of the steps.** `docs/BUILDING.md` lists
the adversarial review as step 5 and *"a `changelog.d/` fragment in the same commit as the code"* as
step 6. **The fragment does not exist when the last review pass runs.** The procedure guarantees the
outcome the measurement found; no reviewer had to forget anything. That is a better finding than
"reviewers skip fragments", and it is only visible if you read the two steps as an ordering rather
than as a list.

**MEDIUM — and it had already cost something, in the increment that was about exactly this.** The
changelog fragment written in `d9fe1a9` carried *"wrong for twelve hours"* — a duration that had
been **invented**, and repeated across four files, inside an increment whose whole subject was
claims asserted without measurement. The review pass did not catch it because the pass read the
plans and **never opened the fragment**. It was found while re-deriving timestamps for an unrelated
reason. A fragment is not scratch: `tools/fragments.py` splices it into `CHANGELOG.md` and
`docs/RETROSPECTIVES.md`, and `docs/` publishes on every push — **an unreviewed fragment is an
unreviewed published document.**

**LOW, and it is the caveat that keeps the rule honest.** The rule says *opened*, not *reviewed*,
and the peer insisted on the distinction before it was written down. A transcript can show which
files a pass opened; whether it reviewed them is **not observable and no tool will ever check it**.
So the checkable rule is the weak one, and it is stated as a floor rather than a goal. **An opened
file is not a reviewed file** — the measurement is a lower bound on attention, never evidence of it.
Writing the strong version would have produced a rule that reads as a guarantee and is not one,
which is the failure class this repository names most often.
