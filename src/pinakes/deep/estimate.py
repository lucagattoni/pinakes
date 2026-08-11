"""Worst-case cost of a `pnk ask --deep` run, before the first call (E2, D-24 option A).

Pure: no client, no I/O, no wall clock. The money side of the loop `deep/loop.py` will run (E4),
priced here so the whole operation can be refused at round 0 rather than discovered halfway
through — DESIGN §5's pre-call reservation, applied to an operation whose unit is a *round* rather
than a page slice.

**The unit is a round, and a round is two calls** (§5 of `plans/20260811_1358-deep-release.md`):
one that decomposes the question against carried memory, one that answers a subproblem from
retrieved passages. Two calls of known maximum size give a constant per-round worst case, so
`max_rounds x per-round` is the operation's ceiling. A single call that both plans and answers has
no bound on how much it retrieves into itself, which is why the shape is not negotiable here.

**Both calls are priced at the same worst-case input, and that is deliberate.** The plan's formula
counts the round's input once — `(carried_memory + final_k x chunk + prompt) x input_price` — but a
round makes *two* calls, each of which carries its own input, so counting it once under-prices a
round by everything the second call also carries: the memory, the question and the prompt.
Under-counting is the one direction a budget may never be wrong in (INVARIANTS), so every call in a
round is priced at the full worst case instead. It
costs an over-reservation on the decompose call, which sends no passages, and it buys the property
`budget/estimate.py` already relies on: **every call costs the same**, so one `per_call_eur` bounds
the per-call reservation `Accountant.paid_call` makes, whichever of the two it is about to make.

**Two branches, both first-class** (D-28 option B). A confident retrieval takes the cheap branch —
one synthesis call over round 0's passages, priced by `estimate_synthesis` — and that is what most
`--deep` runs actually cost. A low-confidence or uncalibrated one takes the loop, priced by
`estimate_round`. The branch is decided by the confidence value read once at round 0 and *passed*
here (`estimate_operation(branch=…)`), never recomputed: two places deciding which branch runs is
two places that can disagree about which one was priced.

**What binds `deep/loop.py` (E4), because the price assumes it.** Two things, and the estimate is
not a suggestion about either:

* **At most `final_k` passages reach the answering call**, however many subproblems the round
  retrieved for. A round that decomposes into three subproblems and feeds all three retrievals in
  whole spends three times what was reserved for it. Merge and cut to `final_k`.
* **A question longer than `QUESTION_CHAR_CEILING` is refused**, because it is carried into every
  call of the run and nothing else bounds it — argv has no length limit.

Money is `Decimal` end to end and **never quantised here** — quantisation to the cent happens at
exactly one point, when a reservation or reconciliation is written to the ledger (I6b).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from pinakes.budget.estimate import MAX_INPUT_TOKENS, assert_prices_fresh
from pinakes.budget.prices import Prices
from pinakes.errors import ContextWindowExceededError

#: Paid calls in one round: decompose, then answer. A semantic constant from §5's loop shape, not a
#: knob — a round with a different call count is a different loop, and its cost would no longer be
#: the constant that makes `max_rounds x` an operation ceiling.
CALLS_PER_ROUND: Final = 2

#: Vendor tokens to reserve per `[chunking] max_tokens` of a retrieved passage.
#:
#: **A chunk is sized in the embedding model's tokenizer and billed in the vendor's**, and the two
#: are different tokenizers over the same text. The conversion cannot be measured without spending,
#: so it is bounded from the character side, which can:
#:
#:     uv run --frozen python3 tools/measure_passage_tokens.py \
#:         tests/demo-kb/docs tests/partner-kb/docs docs
#:
#: **Measured 20260811 15:55** over 2,424 chunks at the template default `max_tokens = 510`: the
#: widest real chunk holds **4.27 chars per embedding token** (2,131 chars at 499 tokens), and the
#: worst ratio anywhere is 7.07 on a 15-token block no full-size chunk could sustain. English prose
#: runs ~3.5-4 characters per vendor token; at a deliberately pessimistic **3**, the widest real
#: chunk converts at 1.42x and even the 7.07 outlier at 2.36x. **3 is above both, and is not
#: lowered to either** — a ceiling below a measurement is not a ceiling (`PAGE_TOKEN_CEILING`
#: records the same refusal, and E6 measures the vendor half rather than assuming it).
VENDOR_TOKENS_PER_CHUNK_TOKEN: Final = 3

#: Per passage, on top of its text: the citation header, the path, the heading path and the
#: numbering the prompt wraps each passage in. Measured from the corpora above, the longest
#: `path — heading_path` pair is under 120 characters; 100 tokens is comfortably past that and is
#: charged per passage rather than per call, so `final_k` scales it the way the text scales.
PASSAGE_ENVELOPE_TOKENS: Final = 100

#: The carried-memory bound: what a round may hand the next one after §5's re-fold.
#:
#: **The one term here that is enforced rather than estimated.** The loop re-folds its memory to
#: this budget instead of appending to it, which is what keeps a round's cost constant; so this is
#: not a ceiling over an unknown, it is the number `deep/loop.py` (E4) must cut to. It lives in the
#: module that prices it so the two cannot disagree — E4 imports it rather than declaring its own.
CARRIED_MEMORY_TOKENS: Final = 4_000

#: The question's own tokens, and the ceiling `deep/loop.py` (E4) must enforce to make them a
#: bound at all.
#:
#: **Found in this increment's own review, and it is a real under-count without the pair.** A
#: question arrives as an argv string — `pnk ask "<question>"` — with no length limit anywhere in
#: the CLI, and it is carried into *every* call of the run. Folding it into `PROMPT_TOKENS` would
#: price a 50,000-token question at the same 1,500 tokens as a one-line one, so it is priced
#: separately and **bounded**: 2,000 characters is a generous CLI question (~300 words), and at a
#: deliberately pessimistic 2 characters per vendor token that is 1,000 tokens.
#:
#: The ceiling is not enforced here — this module refuses nothing but a stale price table and an
#: oversized request. **E4 refuses a longer question**, and until it does, a question past the
#: ceiling is the one input that can cost more than was reserved for it.
QUESTION_TOKENS: Final = 1_000
QUESTION_CHAR_CEILING: Final = 2_000

#: The fixed cost of a call: instructions, the structured-output schema, and the envelope around
#: the question — everything that does not scale with the passages or with the question.
#:
#: **Not yet measured, and above the only measurement this repository has.** The prompts are
#: written in E3/E4, so nothing here can count them; the nearest datum is the paid extractor's
#: instructions-plus-schema, *measured* at 571 tokens and shipped at 700 (`PROMPT_TOKENS` in
#: `budget/estimate.py`). A decompose/answer pair carrying citation rules and a richer schema is
#: larger, so this is set at ~2.6x that measurement. E6 measures the real one.
PROMPT_TOKENS: Final = 1_500

#: Output ceiling per call — the `max_tokens` the client sets on the request. Caps thinking and
#: response text *together* on `claude-opus-5`, so it is the correct and only safe per-call output
#: bound, and the same value the extractor reserves for the same reason.
#:
#: **This dominates a round's price** (~80% of it under the shipped defaults), because output is
#: five times the input rate and a round makes two calls. E6 measures what the two calls actually
#: produce; until then a bound that cannot be exceeded is worth more than one that is close.
MAX_TOKENS: Final = 8_000

#: The cheap branch: one synthesis call over round 0's passages (D-28 option B).
SYNTHESIS: Final = "synthesis"

#: The loop: confidence came back `low`, so the question needs decomposition (§4.2).
DECOMPOSITION: Final = "decomposition"

#: The loop, with no early stop: no calibrated signal, so it ends at the round cap or the budget
#: and the output says which (D-22 option E). Priced identically to `DECOMPOSITION` — the missing
#: signal changes when a run *stops*, never what a round *costs*.
UNKNOWN: Final = "unknown"

#: Every branch this module will price. `pnk ask`'s escalation block (`cli.py`'s `_escalation`)
#: names one more, `none` — nothing matched — which is deliberately absent: a run with no evidence
#: to reason over is not a cheaper run, it is one that must not be offered.
BRANCHES: Final = (SYNTHESIS, DECOMPOSITION, UNKNOWN)

_CONTEXT_REMEDY: Final = (
    "Lower `[retrieval] final_k` or `[chunking] max_tokens` — unlike the PDF path's fixed request "
    "shape, both are yours to set, and a deep round's input is final_k passages of max_tokens "
    "each. Re-chunking (a `max_tokens` change) needs `pnk sync --rebuild`."
)


@dataclass(frozen=True, slots=True)
class RoundEstimate:
    """The worst-case cost of one unit of paid work: a loop round, or the cheap branch's one call.

    **One type for both**, because the cheap branch is a round with one call and no carried memory
    — the same arithmetic over different terms. Two types would be two places to keep the money
    right, and the second one would be the one that drifts.
    """

    model: str
    calls: int
    carried_memory_tokens: int
    passages: int
    input_tokens_per_call: int
    output_tokens_per_call: int
    input_eur_per_call: Decimal
    output_eur_per_call: Decimal

    @property
    def per_call_eur(self) -> Decimal:
        """Every call here costs the same (module docstring) — what `Accountant.paid_call` checks
        before each individual call, whichever of a round's two it is about to make."""
        return self.input_eur_per_call + self.output_eur_per_call

    @property
    def total_eur(self) -> Decimal:
        """**The per-call price multiplied up, never a total divided down.**

        `Decimal` division is exact to 28 significant digits and no further, so a total divided by
        its call count and multiplied back does not always return the total. This module's first
        draft totalled the doubled token counts and divided for the per-call price, and at the
        shipped defaults that produced EUR 0.5420370370370370370370370371 against a doubled
        0.5420370370370370370370370372 — caught by a test asserting they were equal, on the third
        run of the suite.

        Which way that last digit falls is chosen by nothing, and a per-call reservation summing to
        less than the operation it belongs to is an under-count. Deriving the total from the
        per-call price makes `calls * per_call_eur == total_eur` true by construction, so the class
        is gone rather than the one instance: no set of constants can reintroduce it.
        """
        return self.calls * self.per_call_eur


@dataclass(frozen=True, slots=True)
class OperationEstimate:
    """What one whole `pnk ask --deep` may cost — the number checked before round 0.

    An "operation" is one whole invocation and the cap is a running total across every call it
    makes (DESIGN §5), so this is the number `per_operation_eur` is compared against, not any
    single round's.
    """

    model: str
    branch: str
    rounds: int
    per_round: RoundEstimate

    @property
    def calls(self) -> int:
        return self.rounds * self.per_round.calls

    @property
    def total_eur(self) -> Decimal:
        return self.rounds * self.per_round.total_eur

    @property
    def per_call_eur(self) -> Decimal:
        return self.per_round.per_call_eur


def passage_tokens(*, final_k: int, chunk_max_tokens: int) -> int:
    """Vendor tokens to reserve for the `final_k` passages one call is handed.

    Exposed because E4 needs the same number to decide how much evidence fits, and a second
    expression of it would be a second answer.
    """
    _positive(final_k=final_k, chunk_max_tokens=chunk_max_tokens)
    return final_k * (chunk_max_tokens * VENDOR_TOKENS_PER_CHUNK_TOKEN + PASSAGE_ENVELOPE_TOKENS)


def estimate_round(
    *,
    final_k: int,
    chunk_max_tokens: int,
    model: str,
    prices: Prices,
    now: str,
    max_price_age_days: int,
) -> RoundEstimate:
    """Worst case for one loop round: `CALLS_PER_ROUND` calls, each priced at the full round input.

    `final_k` and `chunk_max_tokens` are the caller's manifest values (`[retrieval] final_k`,
    `[chunking] max_tokens`) rather than constants: neither has an upper bound in the manifest, so
    a KB that retrieves twenty 2,000-token passages must be priced as one, not as the default.
    """
    return _estimate(
        calls=CALLS_PER_ROUND,
        carried_memory_tokens=CARRIED_MEMORY_TOKENS,
        final_k=final_k,
        chunk_max_tokens=chunk_max_tokens,
        model=model,
        prices=prices,
        now=now,
        max_price_age_days=max_price_age_days,
    )


def estimate_synthesis(
    *,
    final_k: int,
    chunk_max_tokens: int,
    model: str,
    prices: Prices,
    now: str,
    max_price_age_days: int,
) -> RoundEstimate:
    """The cheap branch: **one** call over round 0's passages, with no carried memory (D-28 B).

    Not a fraction of a round. Under D-28 this is what a confident question actually costs, and the
    whole return on having a calibrated signal is that it is one call against `2 x max_rounds`.
    """
    return _estimate(
        calls=1,
        carried_memory_tokens=0,
        final_k=final_k,
        chunk_max_tokens=chunk_max_tokens,
        model=model,
        prices=prices,
        now=now,
        max_price_age_days=max_price_age_days,
    )


def estimate_operation(
    *,
    branch: str,
    max_rounds: int,
    final_k: int,
    chunk_max_tokens: int,
    model: str,
    prices: Prices,
    now: str,
    max_price_age_days: int,
) -> OperationEstimate:
    """The number checked before round 0, for the branch that is about to run.

    `branch` is the value the confidence signal already decided (`SYNTHESIS`, `DECOMPOSITION` or
    `UNKNOWN`), read once at round 0 and passed in — never recomputed from the confidence here, or
    the branch that was priced and the branch that runs could differ.

    `max_rounds` bounds the loop branches only: the cheap branch is one call and reports
    `rounds == 1` whatever is passed. A cap below 1 is still rejected on either branch — a round
    cap of zero is a mistake wherever it came from, and silently ignoring it on one branch would
    let it reach the other.
    """
    if branch not in BRANCHES:
        raise ValueError(
            f"estimate_operation: branch={branch!r} is not one of {', '.join(BRANCHES)}. "
            "`none` — nothing matched — has nothing to price: a run with no evidence to reason "
            "over must not be offered rather than offered cheaply."
        )
    _positive(max_rounds=max_rounds)

    if branch == SYNTHESIS:
        return OperationEstimate(
            model=model,
            branch=branch,
            rounds=1,
            per_round=estimate_synthesis(
                final_k=final_k,
                chunk_max_tokens=chunk_max_tokens,
                model=model,
                prices=prices,
                now=now,
                max_price_age_days=max_price_age_days,
            ),
        )
    return OperationEstimate(
        model=model,
        branch=branch,
        rounds=max_rounds,
        per_round=estimate_round(
            final_k=final_k,
            chunk_max_tokens=chunk_max_tokens,
            model=model,
            prices=prices,
            now=now,
            max_price_age_days=max_price_age_days,
        ),
    )


def _estimate(
    *,
    calls: int,
    carried_memory_tokens: int,
    final_k: int,
    chunk_max_tokens: int,
    model: str,
    prices: Prices,
    now: str,
    max_price_age_days: int,
) -> RoundEstimate:
    """The one place a `RoundEstimate`'s arithmetic happens — both public estimators route here."""
    # Widths first, prices second: a `final_k` of zero is a defect in the caller whatever the price
    # table's age, and reporting the stale table instead would send the reader to the wrong file.
    evidence = passage_tokens(final_k=final_k, chunk_max_tokens=chunk_max_tokens)
    assert_prices_fresh(prices=prices, now=now, max_price_age_days=max_price_age_days)
    model_price = prices.for_model(model)

    input_per_call = carried_memory_tokens + evidence + QUESTION_TOKENS + PROMPT_TOKENS

    max_input = MAX_INPUT_TOKENS.get(model)
    if max_input is not None and input_per_call > max_input:
        raise ContextWindowExceededError(
            request_tokens=input_per_call,
            max_input_tokens=max_input,
            model=model,
            remedy=_CONTEXT_REMEDY,
        )

    million = Decimal(1_000_000)
    input_usd = (Decimal(input_per_call) / million) * model_price.input_per_mtok_usd
    output_usd = (Decimal(MAX_TOKENS) / million) * model_price.output_per_mtok_usd

    return RoundEstimate(
        model=model,
        calls=calls,
        carried_memory_tokens=carried_memory_tokens,
        passages=final_k,
        input_tokens_per_call=input_per_call,
        output_tokens_per_call=MAX_TOKENS,
        input_eur_per_call=input_usd / prices.usd_per_eur,
        output_eur_per_call=output_usd / prices.usd_per_eur,
    )


def _positive(**values: int) -> None:
    """Reject a zero or negative width, naming the parameter the caller passed.

    A zero `final_k` prices a paid run at output-only, and a negative one prices it *below zero* —
    the direction a budget guard must never move, since it would understate real spend. Neither is
    a real retrieval, and the manifest's own minimum for both keys is 1.
    """
    for name, value in values.items():
        if value < 1:
            raise ValueError(f"deep estimate: {name}={value} must be >= 1")
