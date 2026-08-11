## E2 — The deep release's round estimator (20260811 16:15)

**HIGH — the worst case left out the one input the user controls: the question itself.** The plan's
formula prices carried memory, `final_k` passages and a prompt constant, and the first draft
implemented exactly that, with the question folded into `PROMPT_TOKENS`. But a question arrives as
an argv string — `pnk ask "<question>"` — with no length limit anywhere in the CLI, and it is
carried into *every* call of a run, so a 50,000-token question would have been reserved for at
1,500 tokens. Fixed by pricing it separately (`QUESTION_TOKENS`) against a stated ceiling
(`QUESTION_CHAR_CEILING`) that E4 must enforce, since this module refuses nothing but a stale price
table and an oversized request. *Lesson: when a worked example pins an estimate to the cent, it
also silently fixes the size of every input the example did not vary. The question was the one term
with no bound anywhere in the system, and the arithmetic looked right because the example never
made it big. Ask what is in a call's input that the formula does not name — not whether the formula
was implemented correctly.*

**HIGH — the second review pass found a ceiling below its own measurement, in a module written to
refuse exactly that.** `PASSAGE_ENVELOPE_TOKENS` carried the comment *"the longest `path —
heading_path` pair is under 120 characters"*, asserted without running anything, and 100 tokens was
sized from it. Running it — by extending `tools/measure_passage_tokens.py` to report the envelope
as well as the chunk — returned **220 characters**, about 110 vendor tokens at the pessimistic
conversion the module's other constants use. The constant was under-reserving against a number
nobody had taken; it is now 250, with the measurement and its date beside it. *Lesson: the review
question that found it was "which of these numbers did I measure, and which did I merely write?" —
asked of a file whose every other constant carries a command. A measured neighbour makes an
asserted one look measured too, and prose like "measured from the corpora above" is how the two
become indistinguishable.*

**MEDIUM — a total divided by its call count and multiplied back was not the total.** `Decimal`
division is exact to 28 significant digits and no further, so `per_call_eur * calls` landed one
digit above `total_eur` at the shipped defaults — meaning, in the other direction, a per-call
reservation could sum to less than the operation it belongs to. Caught by a test asserting the two
were equal. Fixed by deriving the total *from* the per-call price rather than the per-call price
from the total, which removes the class rather than the instance: no set of constants can
reintroduce it. *Lesson: `Decimal` fixes base-10 representation, not associativity — money code
should multiply a unit price up, never divide a total down, and the direction of the last digit is
chosen by nothing.*

**MEDIUM — a "measured" docstring falsified by the fix in its own increment.** The docstring above
cited the two 28-digit values it was measured at; the fix changed the arithmetic that produced
them, so re-running the same comparison now round-trips exactly and the cited numbers describe code
that no longer exists. Rewritten to say what was observed *and when it stopped being reproducible*,
rather than left reading as a claim about the shipped module. *Lesson: the measurement most likely
to go stale in a docstring is the one that motivated the change in the same diff — grep your own
increment's fixed defects for the numbers that justified them.*

**LOW — a purity test written as a denylist, in a repository that had already learned not to.** The
first version asserted `deep/estimate.py` imports no `anthropic`, `sqlite3`, `httpx`, `requests` —
a list that is never finished, and whose next omission is always the one that matters.
`check.sh`'s NUL scan records the same lesson about file suffixes ("a denylist of binary formats is
never finished"), one file away. Rewritten as an allowlist of what the module may import, so a new
import has to be argued for in the test. *Lesson: for "this module stays pure", enumerate what is
allowed. The repository's existing gates are worth reading for the shape of the assertion, not only
for the rule.*

**A finding handed to E4 rather than solved here.** At the shipped defaults (`final_k = 8`,
`[chunking] max_tokens = 510`, `[budget] per_operation_eur = 0.30`) the cheap branch prices at
EUR 0.2627 and fits inside the cap; a five-round loop prices at EUR 2.81 and is 9.4x it. So on a
stock KB, `pnk ask --deep` would answer a *confident* question and refuse an uncalibrated one at
round 0 — which is precisely the combination D-22 option E was chosen to avoid, arrived at through
the caps instead of through the signal. E2 declines to fix it by lowering a ceiling: that is the
trade `PAGE_TOKEN_CEILING` refused, and the numbers are conservative by design until E6 measures
them. It is pinned as
`tests/test_deep_estimate.py::test_the_shipped_defaults_leave_the_loop_outside_the_default_operation_cap`,
reading both sides out of the manifest defaults so it tracks them rather than restating them.
