## Both hops were green for the value of a constant neither of them mentions (20260902 10:45)

Two assertions in `tests/test_pdf_trace.py`, one live and one latent, were **correct against every
input anyone had ever run them on**. Neither was a badly written test. Both depended on the value of
a constant that appears nowhere in their text, and this repository refreshes exactly that constant
on a schedule.

| hop | what it compared | why it was green | what ended it |
|---|---|---|---|
| 2, reservation | `cost_eur` against `estimate.per_request_eur` | at `usd_per_eur = 1.1596` the multiply back landed exactly on six decimals, so quantisation was a no-op | the 20260901 refresh to `1.159` |
| 4, reconciliation | a bare `Decimal.quantize()` against the ledger's `ROUND_HALF_UP` | today's prices make per-token USD exactly six decimals, so there is never a tie to resolve | nothing yet — it is latent |

**The trigger is scheduled, not hypothetical.** `docs/RELEASING.md` § *Before you start* step 3
refreshes `prices.toml` at every release. That step is the input to both assertions and is named in
neither. A price-granularity check — something that asks whether a refreshed rate or per-token price
still leaves the arithmetic on the quantum — is arguable on this evidence. It is deliberately not
built here: that is new process, and new process is not an implementer's to invent.

**Measured, because the plausible story was wrong twice.** A rearrangement that divides once instead
of twice looks like a principled fix; over 40 000 randomised `(rate, cost, requests)` cases it fails
**54%** of the time — and **0.00%** at `requests == 1`, which is the fixture's own shape. It would
have passed this test, and any sweep shaped like the fixture, while leaving the assertion
structurally false. My own first proposal failed **1.81%** of the same sweep, because it inherited
the very rounding-mode defect I then found in hop 4.

**What the fix stops covering, said plainly.** Both sides of hop 2 now go through the production
`quantise()`, so it cannot fail on arithmetic: it pins the *plumbing* — that the reservation carries
**this** estimate and not another number — and nothing about the arithmetic that produced it. Four
mutants confirm the shape rather than assert it: an accountant that adds one quantum and a
`claude.py` that reserves a different estimate field both **die**; `PROMPT_TOKENS 700 → 701` and the
ledger's rounding mode both **survive**. The survivors are not a gap to be closed but a seam to be
named: the test recomputes the estimate from `estimate_document`, so any mutation *inside* that
function moves both sides of the assertion equally and is structurally invisible to it.

**And the word "pinned" does not apply to hop 4.** Hop 4 is green today with or without the change,
so no ordinary run can demonstrate it; it is a latent divergence closed before it fired, and showing
it requires changing a price. Saying "pinned" would be claiming a failing test that does not exist.
