## The review step ran before the fragment existed, so the fragment was never reviewed (20260826 11:30)

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

**LOW — and applying the rule immediately caught a false negative in the checking itself.** Verifying
that the `d9fe1a9` fragment really had carried the invented duration, `grep -o "wrong for.*hours"`
returned **nothing** — on a file that contains the phrase. **Markdown had wrapped it across a line
break, and `grep` is line-based.** The first measurement said the claim was unfounded; the second,
`tr '\n' ' '` before matching, said it was true. **A grep over prose is a grep over lines, not over
sentences** — so a phrase spanning a wrap is invisible to it, and the failure is silent and reads
exactly like a clean result. That is the shape of every defect in this increment: a check that
answers a narrower question than the one asked, and returns green.

**MEDIUM — and opening my own fragments found that I had composed three timestamps today, in seven
fragments about not composing things.** The repository's most-repeated rule is *read the clock, never
compose it*. Every fragment **filename** obeyed it — they come from `date -u "+%Y%m%d_%H%M"`. Every
fragment **heading** I typed by hand, and three of the nine disagreed with their own filename:

| Fragment | filename | heading I wrote | out by |
|---|---|---|---|
| `…0727-a-procedure-that-never-asked` | 07:27 | 07:26 | 1 minute |
| `…0733-the-cycles-price` | 07:33 | 07:31 | 2 minutes |
| `…1130-…-never-reviewed` (this one) | 11:30 | **08:00** | **3 h 30 m** |

The last is the instructive one: I wrote *08:00* from a sense of how long the session had been
running. The clock said **11:35**. **A composed timestamp is not approximately right — it is
unrelated**, and the error grows with exactly the thing that makes you stop checking.

**And nothing catches it. Measured, not assumed.** A probe fragment named `…_0101-…` with the
heading stamp `23:59` — twenty-two hours apart — was reported by
`python3 tools/fragments.py --check` as **"all well-formed", exit 0.** The filename prefix is parsed
(`fragments.py:124`) only to be *stripped* before reading the slug; **the heading's stamp is never
compared to it.** Both halves of the fragment resolve, so the same shape as every other defect in
this increment: a check that answers a narrower question than the one asked, and returns green.

**The fix is a gate and it is `tools/`, so it is proposed rather than written**: `--check` should
fail when a retrospective heading's `YYYYMMDD HH:MM` disagrees with its filename prefix. Both are in
the file; nothing external is needed; and it converts the repository's most-repeated convention —
which has now missed **three times in one morning, in the fragments of the sessions writing about
measurement** — into something that cannot miss silently.

