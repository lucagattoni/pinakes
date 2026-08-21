## E6 — The measurement run (20260821 07:53)

**HIGH — the instrument that publishes the numbers had no tests, and its `--json` had never
run.** `vars()` on a `slots=True` dataclass raises `TypeError`, so `tools/deep_reservation.py
count --json` and `report --json` both failed on their first row, in every version that ever
existed. It survived because every measurement session read the printed table instead. The
general shape is worth keeping: **a tool written to be run by hand has exactly one exercised path
— the one the author happened to type** — and the flag nobody typed is not a lesser-tested path,
it is an untested one. The fix is cheap; noticing was the whole cost, and what noticed was sitting
down to write the tests rather than any run of the tool.

**HIGH — the published factor was not reproducible, and nothing said so.** The handover recorded
19.0× on synthesis and 16.5× on the loop. Those came from measurement KBs under `/tmp`, which the
operating system reaped after nine days, taking every transcript and every ledger row with them.
The money was spent and the numbers were real, but by the time anyone re-ran `report` the evidence
for them was gone — and `report` cheerfully printed a *different* factor over the surviving
records without any indication that it was answering a smaller question. **A measurement whose
substrate lives in `/tmp` has a shelf life**, and the number outlived it. What made this
recoverable rather than merely lost is that the runbook's rebuild step is free: the KBs come from
`tests/demo-kb` and `tests/partner-kb`, so the run could simply be done again.

**HIGH — the runbook's own step (c) measures the wrong branch.** It names three `no-answer`
questions to exercise the loop. On the calibrated KB one of them — *"Which software does the
catalogue run on?"* — scores **`medium`**, which takes the *cheap* branch: running the runbook as
written buys a synthesis call and records it as a loop measurement. The free pre-flight the same
document prescribes is what caught it, one paragraph after the document tells you to run it. Step
(b) already warns that "a `2` means the branch was mis-selected and the run measured the wrong
thing"; the inverse case had no such check, and the questions were never re-verified after the
thresholds were fitted.

**HIGH — and the reason step (c) chose those questions is itself false.** It argues that
`no-answer` questions are the right instrument because "nothing in the corpus answers them, so the
sufficiency gate cannot stop the run early and it goes to the round cap — which is the worst case
the reservation was sized for, and therefore the only case that measures it." Measured: **both**
`decomposition` runs stopped at **sufficiency**, after 2 rounds and after 1 round of 3. A
sufficiency gate reading a calibrated signal is perfectly willing to conclude that enough has been
established about a question the corpus cannot answer. So on a calibrated KB the loop's worst case
is *not* reachable by choosing a hard question, and the branch that actually reaches the round cap
is `unknown`, on a KB with no thresholds at all — the branch the runbook does not mention.

**MEDIUM — the more calibrated the KB, the *more* over-reserved its loop is.** The three branches
came out 29.75× (synthesis), **50.92× (calibrated loop)** and 22.35× (uncalibrated loop). The
ordering is not noise and it is not a defect: a reservation must cover `max_rounds`, and
calibration is exactly what lets a run stop before it gets there. The uncalibrated branch is the
least over-reserved *because* it has no early stop and spends the rounds it reserved. Reporting a
single blended figure would have hidden this entirely, which is the argument D-28 made before any
of it was measured.

**MEDIUM — `MAX_TOKENS` carries most of the over-reservation, and is the constant least safe to
lower.** 8,000 reserved against a widest-observed 660 across 22 reconciled calls (mean 241) —
12.12×, against 1.50× to 8.93× for the five input constants. It dominates because output bills at
five times input and is two thirds of a round's price. It is also the only one of the six that is
a *truncation* rather than a bill: an input ceiling set too low over-reserves, while an output
ceiling set too low cuts an answer off mid-sentence. The temptation to lower the one constant that
would visibly improve the headline figure is therefore precisely inverted from where it is safe to
do so, which is worth stating plainly next to a 12× ratio.

**LOW — the `[budget]` block the runbook tells you to append is now two-thirds the shipped
default.** It prescribes `per_operation_eur = 2.00` and `daily_eur = 6.00`; D-30 raised the
defaults to exactly those values in 0.24.0. Both measurement KBs ran the whole plan with no
`[budget]` section at all. Harmless, but it is a hand-editing step the document still asks for and
no longer needs — and the two keys that *do* still differ (`confirm_above_eur`, `monthly_eur`) are
the two it does not explain.

**LOW — the refusal path had never been run, and works exactly as specified.** Step (d),
untouched through two measurement sessions. With `per_operation_eur = 1.00` against the loop
branch's €1.38 estimate: refused **before the first call**, exit 1, no ledger row (22 lines before
and after) and no transcript (7 files before and after), with a message naming the cap, the
headroom, the branch, the call and round count, the complete manifest edit that would admit the
run, and the two cheaper routes before raising a cap. D-23 and E5's "a run that never returned
writes none" both hold.
