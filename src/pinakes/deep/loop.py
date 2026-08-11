"""The loop behind `pnk ask --deep` (E4) — free retrieval first, then bounded paid rounds.

It decides *which* calls are made and how many; `deep/client.py` (E3) makes them and
`deep/estimate.py` (E2) prices them. Nothing here talks to a vendor, opens a database or reads the
clock: it is handed a retriever, a sufficiency signal, a transport and an accountant, which is what
lets the whole loop run against recorded fixtures with `anthropic` absent.

**Round 0 is free and has already happened.** The caller runs §4.1's pipeline, reads §4.2's
confidence off it, and passes both in. That is D-28 as taken: **confidence sizes the work, it does
not authorise it.** A `high` or `medium` question takes the cheap branch — one synthesis call over
round 0's own passages, which is what most `--deep` runs actually cost. A `low` one takes the loop.
An `unknown` one takes the loop *with no early stop*, because the step that would end it early is
the very signal that is missing (D-22 option E) — so it ends at the round cap or at the budget, and
`DeepAnswer.label` says which.

**Every bound is checked before the first call.** `estimate_operation` prices the branch that is
about to run, `Accountant.check_run` refuses it against all three windows at once with the exact
`[budget]` edit that would admit it, and `confirm_above_eur` is put once. After that each call is
reserved and reconciled individually by the client. The operation is one `pnk ask --deep` and the
cap is a running total across every call it makes (DESIGN §5).

**Three properties come from the research notes and none of them are code** (M10 of the plan):

* a subproblem is never re-asked once it has been asked — the cursor advances, and `_asked` is it;
* carried memory is **re-folded** rather than appended, so a round's cost is constant and
  `max_rounds x per-round` really is the operation's ceiling;
* the round cap ends in a best-effort answer rather than a failure.

**The re-fold is free, and that is a constraint rather than an oversight.** §5 marks step 4 free, so
it can only select and truncate — a model call that summarised the memory would be a third paid call
in a round priced for two, which is the one thing that would make the estimate wrong.

**Prompt injection: a subproblem is a query string, and there is no code path by which it becomes
anything else.** The structural half is E3's — the decomposition schema has one field, an array of
plain strings — and the behavioural half is here: every subproblem reaches exactly one function,
the `retrieve` callable the caller bound to `search()` over *this* KB with the *caller's* filters.
Nothing in this module opens a path, chooses a KB or builds a filter, so hostile text in a retrieved
document has nothing to steer.
"""

import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from pinakes.budget.accountant import Accountant
from pinakes.budget.prices import ModelPrice
from pinakes.deep.client import (
    SUBANSWER,
    SYNTHESIS,
    Answer,
    CallTally,
    DeepBudgetRefusedError,
    QuestionTooLongError,
    Transport,
    answer,
    decompose,
)
from pinakes.deep.estimate import (
    BRANCHES,
    CARRIED_MEMORY_CHAR_CEILING,
    QUESTION_CHAR_CEILING,
    UNKNOWN,
    OperationEstimate,
    estimate_operation,
)
from pinakes.errors import DeepError
from pinakes.search import HIGH, MEDIUM, Passage, SearchResult

#: What `retrieve` is: one subproblem in, one §4.1 result out. Bound by the caller to `search()`
#: over this KB with this invocation's filters, so a subproblem cannot reach anything else.
Retrieve = Callable[[str], SearchResult]

#: What `sufficiency` is: §4.2's own `search.confidence_of`, closed over the manifest and the
#: reranker actually in use. Passed in rather than imported so the loop reads the same thresholds
#: `pnk search` reports, against the same reranker, with no second copy to disagree.
Sufficiency = Callable[[Sequence[Passage]], tuple[str, str]]

ANSWERED: Final = "answered"
"""The cheap branch: one synthesis call, because the free signal said the evidence was there."""

SUFFICIENT: Final = "sufficient"
"""The loop's early stop — the accumulated evidence cleared §4.2's threshold. The step an
uncalibrated KB cannot take (D-22 option E), which is why an `unknown` run costs more."""

ROUND_CAP: Final = "round-cap"

EXHAUSTED: Final = "no-new-subproblems"
"""Decomposition returned nothing that had not already been asked. A stop, not a failure: the
cursor never re-asks, so a round with nothing new is a round with nothing to do."""

NO_EVIDENCE: Final = "no-evidence"
"""A round's subproblems retrieved nothing. Stopping beats paying a decompose call to be told the
same thing again — the next round would carry the same memory and produce the same list."""

BUDGET: Final = "budget"

STOP_REASONS: Final = (ANSWERED, SUFFICIENT, ROUND_CAP, EXHAUSTED, NO_EVIDENCE, BUDGET)
"""Every value `DeepAnswer.stopped_by` can take. Enumerated so a consumer — and E5's transcript —
discriminates on a name this module owns rather than on a sentence written for a human."""

DEEP_CLOSING: Final = (
    "Raising a cap is a permanent, ongoing exposure to every future run at that ceiling. Two "
    "cheaper routes exist first: lower `[deep] max_rounds`, which is what the estimate multiplies; "
    "or fit `[retrieval.confidence]` with `python -m pinakes.calibrate`, after which a confident "
    "question costs one call instead of a loop."
)
"""The advice a budget refusal ends on — the deep path's counterpart to the extractor's
`--extract=` override line, which has no equivalent here: there is no one-run way to make a
question cheaper. Both alternatives named are real and neither is a cap raise, which is the point.
"""

MEMORY_ROUND_MINIMUM: Final = 200
"""Characters below which a truncated round is dropped from the carried memory rather than kept.

A 40-character fragment of a sub-answer is not evidence of anything, and it costs the same per
round as carrying nothing would. Chosen rather than measured; E6 is where a memory this loop has
actually filled can say whether it is right.
"""


@dataclass(frozen=True, slots=True)
class Citation:
    """One cited passage, resolved from the number the model returned back to a document.

    **E4 owns this mapping and E3 made it safe to own** (its point 3): the model is shown numbered
    passages and never a document identifier, and `parse_answer` refuses a number outside the range
    it was sent. So a citation cannot name a document this run did not retrieve — not because
    anything filters the model's output, but because the wire format gave it no identifier to
    invent. E7's rule for suggested links inherits that property rather than re-checking it.
    """

    number: int
    """The number as it appears in this block's own answer text — an index into the passages *that
    call* was handed, never a global one. Blocks are numbered independently because renumbering
    would mean rewriting prose the model wrote, and a `[3]` inside a quotation would be rewritten
    into a lie."""

    doc_id: str
    path: str
    locator: str
    """`Passage.citation()` — what `pnk search` prints, so a citation can be checked against the
    evidence the user was shown."""


@dataclass(frozen=True, slots=True)
class AnswerBlock:
    """One paid answer call's output: what was asked, what came back, and what it cited."""

    round_number: int
    """`0` for the cheap branch's single call; `1..max_rounds` inside the loop."""

    asked: tuple[str, ...]
    """The subproblems this call answered. Empty on the cheap branch, where the question itself
    was asked."""

    text: str
    citations: tuple[Citation, ...]


@dataclass(frozen=True, slots=True)
class DeepAnswer:
    """What one `pnk ask --deep` produced, and which bound ended it.

    There is no final synthesis call, and that is a cost decision rather than an oversight: the
    operation's ceiling is `max_rounds x per-round`, so a closing call over the accumulated blocks
    would be a call nothing reserved. The answer is therefore the rounds' own cited prose, in
    order.
    """

    branch: str
    blocks: tuple[AnswerBlock, ...]
    rounds_used: int
    stopped_by: str

    label: str
    """One sentence naming the bound that ended the run — required of an uncalibrated run by D-22
    option E, and printed on every run because a reader cannot otherwise tell an answer that
    finished from one that ran out."""

    estimate: OperationEstimate
    tally: CallTally

    spent_eur: Decimal
    """What the run actually cost, reconciled from every response's own usage.

    Carried rather than derived by the caller: the conversion needs `Prices.usd_per_eur`, the tally
    is in USD because that is what the vendor bills in, and a caller doing the division itself
    would be a second place the two could be paired with the wrong rate.
    """

    partial: bool
    """The run stopped at a budget window with blocks already produced, and `[budget] on_exceed`
    is `partial` (D-23 option A). Never true for a run that ended at sufficiency or the round
    cap — those are complete runs of a bounded loop, not truncated ones."""

    @property
    def answered(self) -> bool:
        return bool(self.blocks)


class NothingToAnswerError(DeepError):
    """`--deep` on a question the KB matched nothing for.

    Refused rather than run cheaply, for the reason `deep/estimate.py` gives for pricing no `none`
    branch: a run with no evidence to reason over is not a cheaper run, it is one that must not be
    offered. The free `pnk ask` says the same thing without spending.
    """

    def __init__(self) -> None:
        super().__init__(
            "nothing in this knowledge base matched the question, so there is nothing to reason "
            "over.",
            remedy=(
                "Nothing was sent or spent. Widen the question or drop a filter — `pnk ask` "
                "without `--deep` shows what retrieval returns, free."
            ),
        )


class DeepDeclinedError(DeepError):
    """The `confirm_above_eur` prompt was answered with anything but `y`."""

    def __init__(self) -> None:
        super().__init__(
            "the run was not confirmed, so nothing was sent or spent.",
            remedy=(
                "Answer `y` to spend, or raise `[budget] confirm_above_eur` above the estimate to "
                "stop being asked. `--yes` answers the prompt for an unattended run."
            ),
        )


class DeepBudgetHaltedError(DeepError):
    """A budget window stopped the run, and `[budget] on_exceed` is `abort` (D-23 option A).

    `partial` returns what the rounds already produced, labelled; `abort` is this. The distinction
    is the user's existing preference for `pnk sync`, reused rather than re-asked — one concept,
    one key, already in the manifest.
    """

    def __init__(self, message: str, *, rounds_used: int) -> None:
        super().__init__(
            message,
            remedy=(
                f"{rounds_used} round(s) were paid for and are recorded in `pnk budget`. "
                '`[budget] on_exceed = "partial"` would have returned what they found, labelled, '
                "rather than discarding it; raising the named cap lets the run finish."
            ),
        )
        self.rounds_used = rounds_used


@dataclass(frozen=True, slots=True)
class _Caller:
    """Everything a paid call needs that does not change between calls of one run.

    A value rather than seven parameters threaded through three functions — and frozen, because the
    reservation is the one of them that must be identical for every call: E2 prices both kinds at
    the same worst case precisely so that `per_call_eur` bounds whichever is about to be made.
    """

    transport: Transport
    accountant: Accountant
    model: str
    reserved_eur: Decimal
    price: ModelPrice
    tally: CallTally = field(default_factory=CallTally)
    sleep: Callable[[float], None] = time.sleep

    @property
    def spent_eur(self) -> Decimal:
        """What the calls made so far reconciled to, in the currency every cap is written in."""
        return self.tally.cost_usd / self.accountant.prices.usd_per_eur

    def decompose(self, *, question: str, memory: str, max_subproblems: int) -> tuple[str, ...]:
        return decompose(
            transport=self.transport,
            accountant=self.accountant,
            question=question,
            memory=memory,
            max_subproblems=max_subproblems,
            model=self.model,
            reserved_eur=self.reserved_eur,
            price=self.price,
            tally=self.tally,
            sleep=self.sleep,
        )

    def answer(
        self, *, kind: str, question: str, passages: Sequence[Passage], passage_cap: int
    ) -> Answer:
        return answer(
            transport=self.transport,
            accountant=self.accountant,
            kind=kind,
            question=question,
            passages=passages,
            passage_cap=passage_cap,
            model=self.model,
            reserved_eur=self.reserved_eur,
            price=self.price,
            tally=self.tally,
            sleep=self.sleep,
        )


def run_deep(
    *,
    question: str,
    round0: SearchResult,
    branch: str,
    final_k: int,
    retrieve: Retrieve,
    sufficiency: Sufficiency,
    transport: Transport,
    accountant: Accountant,
    now: str,
    sleep: Callable[[float], None] = time.sleep,
) -> DeepAnswer:
    """Answer `question` with paid reasoning, bounded by `[deep]` and by `[budget]`.

    `round0` is the free retrieval the caller already ran and `branch` is what §4.2's confidence
    made of it — both passed in, never recomputed, so the branch that was *priced* and the branch
    that *runs* cannot differ. `final_k` is the effective passage limit for this invocation (`-k`
    when the user gave one, else `[retrieval] final_k`), because that is what the estimate is
    priced at and what every answering call is capped to.

    Everything else the run needs — the caps, the ledger, the model, the round cap, `on_exceed` and
    the price table — is read off `accountant`, which already holds the manifest whose caps it
    enforces. Passing a second copy of any of them would be a second thing that can disagree with
    the numbers the reservation was checked against.
    """
    manifest = accountant.manifest
    if branch not in BRANCHES:
        raise ValueError(
            f"run_deep: branch={branch!r} is not one of {', '.join(BRANCHES)} — a question with "
            "no evidence is refused before this, never priced."
        )
    if not round0.passages:
        raise NothingToAnswerError
    # Before the estimate, not after: the question rides in every call of the run, so a question
    # nothing bounds is not a run that can be priced. `deep/client.py` enforces the same ceiling at
    # the wire (E3), and this is the same error raised as early as it can be seen — one limit, one
    # message, one number, rather than a second sentence about the same 2,000 characters.
    if len(question) > QUESTION_CHAR_CEILING:
        raise QuestionTooLongError(len(question))

    estimate = estimate_operation(
        branch=branch,
        max_rounds=manifest.deep.max_rounds,
        final_k=final_k,
        chunk_max_tokens=manifest.chunking.max_tokens,
        model=manifest.deep.model,
        prices=accountant.prices,
        now=now,
        max_price_age_days=manifest.budget.max_price_age_days,
    )
    _authorise(accountant, estimate)

    caller = _Caller(
        transport=transport,
        accountant=accountant,
        model=manifest.deep.model,
        reserved_eur=estimate.per_call_eur,
        price=accountant.prices.for_model(manifest.deep.model),
        sleep=sleep,
    )

    if branch == SYNTHESIS:
        return _cheap_branch(
            question=question, round0=round0, final_k=final_k, estimate=estimate, caller=caller
        )
    return _loop_branch(
        question=question,
        branch=branch,
        final_k=final_k,
        retrieve=retrieve,
        sufficiency=sufficiency,
        estimate=estimate,
        caller=caller,
        max_rounds=manifest.deep.max_rounds,
        on_exceed=manifest.budget.on_exceed,
    )


def _authorise(accountant: Accountant, estimate: OperationEstimate) -> None:
    """The whole-operation check, before the first call: the caps, then the confirmation.

    In that order because a cap is a refusal and a confirmation is a question — asking someone to
    approve €1.69 and *then* telling them a window forbids it is the sequence `reserve_document`
    was written to avoid.
    """
    decision = accountant.check_run(
        total_eur=estimate.total_eur,
        headline=(
            f"answering this question with {estimate.model} is estimated at "
            f"€{estimate.total_eur:.2f} (the {estimate.branch} branch: {estimate.calls} paid "
            f"call(s) across {estimate.rounds} round(s), worst case)"
        ),
        closing=DEEP_CLOSING,
    )
    if not decision.allowed:
        raise DeepBudgetRefusedError(decision.message or "refused by the budget")
    if not accountant.confirm_run(decision, estimate.total_eur):
        raise DeepDeclinedError


def _cheap_branch(
    *,
    question: str,
    round0: SearchResult,
    final_k: int,
    estimate: OperationEstimate,
    caller: _Caller,
) -> DeepAnswer:
    """One synthesis call over round 0's own passages (D-28 option B).

    Not a degenerate loop: it carries no memory, asks no subproblem and cannot stop early, because
    there is nothing after it to stop. Under D-28 this is the common case, and the whole return on
    having a calibrated signal is that it costs one call rather than `2 x max_rounds`.
    """
    passages = round0.passages[:final_k]
    result = caller.answer(
        kind=SYNTHESIS, question=question, passages=passages, passage_cap=final_k
    )
    return DeepAnswer(
        branch=estimate.branch,
        blocks=(_block(0, (), result, passages),),
        rounds_used=1,
        stopped_by=ANSWERED,
        label=_label(ANSWERED, rounds_used=1, max_rounds=1, branch=estimate.branch),
        estimate=estimate,
        tally=caller.tally,
        spent_eur=caller.spent_eur,
        partial=False,
    )


def _loop_branch(
    *,
    question: str,
    branch: str,
    final_k: int,
    retrieve: Retrieve,
    sufficiency: Sufficiency,
    estimate: OperationEstimate,
    caller: _Caller,
    max_rounds: int,
    on_exceed: str,
) -> DeepAnswer:
    """§5's loop: decompose, retrieve, answer, re-fold, and — unless `unknown` — check sufficiency.

    `stopped_by` starts at `ROUND_CAP` and is overwritten by whichever bound actually bites, so
    falling out of the `for` needs no `else` clause: reaching the end of the range *is* the round
    cap.
    """
    blocks: list[AnswerBlock] = []
    evidence: tuple[Passage, ...] = ()
    asked: set[str] = set()
    memory = ""
    rounds_used = 0
    stopped_by = ROUND_CAP
    halt_message: str | None = None

    for round_number in range(1, max_rounds + 1):
        try:
            subproblems = caller.decompose(
                question=question, memory=memory, max_subproblems=final_k
            )
        except DeepBudgetRefusedError as exc:
            stopped_by, halt_message = BUDGET, exc.message
            break
        # Counted the moment its first call is made, not when it produces a block: a round that
        # decomposed and then found nothing still cost a call, and a count that hid it would make
        # `pnk budget`'s rows unexplainable against the answer they paid for.
        rounds_used = round_number

        fresh = _fresh(subproblems, asked)
        if not fresh:
            stopped_by = EXHAUSTED
            break
        asked.update(_key(item) for item in fresh)

        found = _merge((retrieve(item).passages for item in fresh), final_k=final_k)
        if not found:
            stopped_by = NO_EVIDENCE
            break

        try:
            result = caller.answer(
                kind=SUBANSWER,
                question="\n".join(fresh),
                passages=found,
                passage_cap=final_k,
            )
        except DeepBudgetRefusedError as exc:
            stopped_by, halt_message = BUDGET, exc.message
            break

        blocks.append(_block(round_number, fresh, result, found))
        evidence = _merge((evidence, found), final_k=final_k)
        memory = refold(blocks)

        # The step `unknown` cannot take (D-22 option E). Skipped rather than run and ignored, so
        # nothing in a transcript can read as an early stop that was declined.
        if branch != UNKNOWN and sufficiency(evidence)[0] in (HIGH, MEDIUM):
            stopped_by = SUFFICIENT
            break

    if stopped_by == BUDGET and (on_exceed == "abort" or not blocks):
        # No blocks means `partial` has nothing to return, so `on_exceed` has nothing to choose
        # between and the halt is a refusal whichever way it is set.
        raise DeepBudgetHaltedError(
            halt_message or "refused by the budget", rounds_used=rounds_used
        )

    return DeepAnswer(
        branch=branch,
        blocks=tuple(blocks),
        rounds_used=rounds_used,
        stopped_by=stopped_by,
        label=_label(stopped_by, rounds_used=rounds_used, max_rounds=max_rounds, branch=branch),
        estimate=estimate,
        tally=caller.tally,
        spent_eur=caller.spent_eur,
        partial=stopped_by == BUDGET,
    )


def _block(
    round_number: int, asked: tuple[str, ...], result: Answer, passages: Sequence[Passage]
) -> AnswerBlock:
    """Resolve a call's citation numbers back to the documents they indexed.

    Safe by construction: `parse_answer` has already refused any number outside `1..len(passages)`,
    so the indexing below cannot reach past the list — a check here would be a second reading of a
    bound already enforced where the response is parsed, and the two could disagree.
    """
    return AnswerBlock(
        round_number=round_number,
        asked=asked,
        text=result.text,
        citations=tuple(
            Citation(
                number=number,
                doc_id=str(passages[number - 1].doc_id),
                path=passages[number - 1].path,
                locator=passages[number - 1].citation(),
            )
            for number in result.citations
        ),
    )


def _key(subproblem: str) -> str:
    """The cursor's identity for a subproblem: case- and whitespace-insensitive.

    Exact-string matching would let one round re-ask the previous round's question with a capital
    letter, which is the ~35% token waste the published artifact this loop's shape comes from
    measured (M10). It is deliberately not fuzzier than this — a near-duplicate a looser match
    would swallow is still a different search, and dropping it silently would be the loop quietly
    doing less than the round cap says it may.
    """
    return " ".join(subproblem.lower().split())


def _fresh(subproblems: Sequence[str], asked: set[str]) -> tuple[str, ...]:
    """Subproblems not already asked, in order, cut to what one answering call can carry.

    **The cut is a length bound, not a count bound**, and it exists because these become that
    call's question: the client refuses a question over `QUESTION_CHAR_CEILING` rather than
    truncating it, so a round handing it a too-long join would waste the decompose call it has just
    paid for. Whatever does not fit stays *unasked* so a later round's cursor can still reach it —
    dropping it from the list and marking it asked in one step is what would lose it.
    """
    kept: list[str] = []
    keys = set(asked)
    used = 0
    for item in subproblems:
        if _key(item) in keys:
            continue
        separator = 1 if kept else 0  # the newline that will join it
        if not kept and len(item) > QUESTION_CHAR_CEILING:
            # One subproblem longer than a whole question is a model that ignored its instructions.
            # Truncated rather than dropped, because dropping the only item would end a round that
            # has already been paid for.
            item = item[:QUESTION_CHAR_CEILING]
        elif used + separator + len(item) > QUESTION_CHAR_CEILING:
            continue
        kept.append(item)
        keys.add(_key(item))
        used += separator + len(item)
    return tuple(kept)


def _merge(groups: Iterable[Sequence[Passage]], *, final_k: int) -> tuple[Passage, ...]:
    """Every subproblem's retrieval, deduplicated and cut to the `final_k` a call is priced for.

    **The cut is what E2's price assumes** (its point 3): a round that retrieved for three
    subproblems and fed all three retrievals in whole would spend three times what was reserved for
    it. The client refuses that rather than trimming silently, so the merge has to be right here.

    Ordered by rerank score — the same order `search()` returns and the order `confidence_of` reads
    its top score from. **The comparison is approximate, and worth naming rather than hiding**: a
    cross-encoder score is conditioned on the query it was computed for, so two subproblems' scores
    are not strictly comparable. Both still measure how well a passage answers the query it was
    found for, which is the property the cut wants; E6 is where the approximation gets measured
    instead of assumed.
    """
    seen: set[tuple[str, int, int]] = set()
    merged: list[Passage] = []
    for group in groups:
        for passage in group:
            identity = (passage.path, passage.char_start, passage.char_end)
            if identity in seen:
                continue
            seen.add(identity)
            merged.append(passage)
    merged.sort(
        key=lambda p: (
            -(p.rerank_score if p.rerank_score is not None else float("-inf")),
            -p.fused_score,
            p.path,
            p.char_start,
        )
    )
    return tuple(merged[:final_k])


def refold(blocks: Sequence[AnswerBlock]) -> str:
    """§5 step 4: what the next round is told earlier rounds established, within a fixed budget.

    **Re-folded, not appended** — the whole reason a round's cost is constant. The budget is
    `CARRIED_MEMORY_CHAR_CEILING`, the same number `deep/estimate.py` prices a round's memory at and
    `deep/client.py` refuses a longer one against, imported rather than restated: a re-fold cutting
    to a different number would be cutting to a different price.

    **Newest first when choosing, oldest first when writing.** A round that no longer fits is
    dropped from the *front*, because the later rounds were asked in the light of the earlier ones
    and are what the next decomposition has to build on; the text itself stays chronological, which
    is how it reads as a record rather than as a stack.
    """
    kept: list[str] = []
    remaining = CARRIED_MEMORY_CHAR_CEILING
    for block in reversed(blocks):
        rendered = (
            f"Round {block.round_number} asked: {'; '.join(block.asked)}\nEstablished: {block.text}"
        )
        separator = 2 if kept else 0  # the blank line that will join it
        if separator + len(rendered) <= remaining:
            kept.append(rendered)
            remaining -= separator + len(rendered)
            continue
        room = remaining - separator
        if room >= MEMORY_ROUND_MINIMUM:
            kept.append(rendered[:room])
        break
    return "\n\n".join(reversed(kept))


def _label(stopped_by: str, *, rounds_used: int, max_rounds: int, branch: str) -> str:
    """One sentence naming the bound that ended the run.

    **Required of an uncalibrated run** (D-22 option E: bounded by the caps rather than by the
    signal, and say which) **and printed on every run anyway**, because "the loop stopped" and "the
    loop finished" are different outcomes that would otherwise look identical in the output.
    """
    if stopped_by == ANSWERED:
        return (
            "answered in one synthesis call — the calibrated signal said the retrieved evidence "
            "was already enough, so no decomposition was paid for."
        )
    uncalibrated = (
        " There is no calibrated signal on this KB, so the run could not stop at sufficiency: it "
        "was bounded by the caps rather than by the evidence (`python -m pinakes.calibrate`)."
        if branch == UNKNOWN
        else ""
    )
    if stopped_by == SUFFICIENT:
        return (
            f"stopped after {rounds_used} of {max_rounds} round(s): the accumulated evidence "
            "cleared the confidence threshold."
        )
    if stopped_by == EXHAUSTED:
        return (
            f"stopped after {rounds_used} of {max_rounds} round(s): decomposition returned nothing "
            f"that had not already been searched for.{uncalibrated}"
        )
    if stopped_by == NO_EVIDENCE:
        return (
            f"stopped after {rounds_used} of {max_rounds} round(s): the subproblems it decomposed "
            f"into matched nothing in this knowledge base.{uncalibrated}"
        )
    if stopped_by == BUDGET:
        return (
            f"stopped at a budget window after {rounds_used} of {max_rounds} round(s) — this is a "
            f"partial answer, bounded by `[budget]` rather than by the evidence.{uncalibrated}"
        )
    return (
        f"stopped at the round cap — {rounds_used} of {max_rounds} round(s) — not at sufficiency. "
        f"`[deep] max_rounds` is what bounds it.{uncalibrated}"
    )
