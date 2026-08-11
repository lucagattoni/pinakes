"""The deep release's estimator (E2): what one `pnk ask --deep` may cost, before the first call.

Nothing here spends, and nothing here needs a client — the module under test is pure by
construction, and the import-graph tests at the bottom are what keep it that way once E3 puts a
paid client in the same package.
"""

import ast
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

from pinakes.budget.prices import ModelPrice, Prices
from pinakes.deep.estimate import (
    CALLS_PER_ROUND,
    CARRIED_MEMORY_TOKENS,
    DECOMPOSITION,
    MAX_TOKENS,
    PASSAGE_ENVELOPE_TOKENS,
    PROMPT_TOKENS,
    QUESTION_CHAR_CEILING,
    QUESTION_TOKENS,
    SYNTHESIS,
    UNKNOWN,
    VENDOR_TOKENS_PER_CHUNK_TOKEN,
    OperationEstimate,
    RoundEstimate,
    estimate_operation,
    estimate_round,
    estimate_synthesis,
    passage_tokens,
)
from pinakes.errors import ContextWindowExceededError, StalePricesError, UnknownModelPriceError
from pinakes.ids import mint_kb_id
from pinakes.manifest import load as load_manifest

DEEP_DIR = Path(__file__).parent.parent / "src" / "pinakes" / "deep"
MODEL = "claude-opus-5"
NOW = "20260728 16:31"
MILLION = Decimal(1_000_000)

#: The shipped `notes` defaults, so the worked numbers below are the ones a stock KB would see.
FINAL_K = 8
CHUNK_MAX_TOKENS = 510

#: No `[budget]`, `[chunking]` or `[retrieval]` section at all — so `manifest.py`'s own defaults
#: answer, which is what "a stock KB" means. The `notes` template stamps the same three values.
DEFAULTS_MANIFEST = """\
[kb]
name = "stock"
id   = "{kb_id}"

[sources]
roots = ["docs/"]

[embedding]
provider = "fastembed"
model    = "BAAI/bge-small-en-v1.5"
dim      = 384
"""


def prices(*, as_of: str = NOW, usd_per_eur: str = "1.08") -> Prices:
    return Prices(
        as_of=as_of,
        usd_per_eur=Decimal(usd_per_eur),
        models={MODEL: ModelPrice(Decimal("5.00"), Decimal("25.00"))},
    )


def a_round(
    *,
    final_k: int = FINAL_K,
    chunk_max_tokens: int = CHUNK_MAX_TOKENS,
    model: str = MODEL,
    table: Prices | None = None,
    now: str = NOW,
    max_price_age_days: int = 30,
) -> RoundEstimate:
    return estimate_round(
        final_k=final_k,
        chunk_max_tokens=chunk_max_tokens,
        model=model,
        prices=table or prices(),
        now=now,
        max_price_age_days=max_price_age_days,
    )


def a_synthesis(
    *,
    final_k: int = FINAL_K,
    chunk_max_tokens: int = CHUNK_MAX_TOKENS,
    model: str = MODEL,
    table: Prices | None = None,
) -> RoundEstimate:
    return estimate_synthesis(
        final_k=final_k,
        chunk_max_tokens=chunk_max_tokens,
        model=model,
        prices=table or prices(),
        now=NOW,
        max_price_age_days=30,
    )


def an_operation(
    *,
    branch: str,
    max_rounds: int = 5,
    final_k: int = FINAL_K,
    chunk_max_tokens: int = CHUNK_MAX_TOKENS,
) -> OperationEstimate:
    return estimate_operation(
        branch=branch,
        max_rounds=max_rounds,
        final_k=final_k,
        chunk_max_tokens=chunk_max_tokens,
        model=MODEL,
        prices=prices(),
        now=NOW,
        max_price_age_days=30,
    )


def eur(*, input_tokens: int, output_tokens: int) -> Decimal:
    """What a call of exactly this shape really costs, at the fixture's prices.

    Each side is converted to EUR separately, matching the estimator: `Decimal` division is exact
    to 28 significant digits, so `(a + b) / rate` and `a / rate + b / rate` can differ in the last
    one — a difference this file would otherwise report as a pricing bug.
    """
    model_price = prices().for_model(MODEL)
    rate = Decimal("1.08")
    return (Decimal(input_tokens) / MILLION) * model_price.input_per_mtok_usd / rate + (
        Decimal(output_tokens) / MILLION
    ) * model_price.output_per_mtok_usd / rate


# --- the two branches ---------------------------------------------------------------------------


def test_the_cheap_branch_is_one_call_over_the_passages_with_no_carried_memory() -> None:
    """D-28 option B: a confident question costs one synthesis call — not a fraction of a round."""
    est = a_synthesis()
    assert est.calls == 1
    assert est.carried_memory_tokens == 0
    assert (
        est.input_tokens_per_call
        == passage_tokens(final_k=FINAL_K, chunk_max_tokens=CHUNK_MAX_TOKENS)
        + QUESTION_TOKENS
        + PROMPT_TOKENS
    )


def test_the_question_is_priced_and_not_folded_into_the_prompt() -> None:
    """A question arrives as an argv string with no length limit and is carried into *every* call.
    Folding it into `PROMPT_TOKENS` would price a 50,000-token question at 1,500 tokens; pricing it
    separately makes `QUESTION_CHAR_CEILING` the thing E4 has to enforce, and names it."""
    assert QUESTION_TOKENS > 0
    # 2 characters per vendor token is the pessimistic conversion the ceiling is derived at.
    assert QUESTION_TOKENS >= QUESTION_CHAR_CEILING / 2
    est = a_synthesis()
    without_question = est.input_tokens_per_call - QUESTION_TOKENS
    assert (
        without_question
        == passage_tokens(final_k=FINAL_K, chunk_max_tokens=CHUNK_MAX_TOKENS) + PROMPT_TOKENS
    )


def test_a_round_prices_both_of_its_calls_at_the_full_worst_case_input() -> None:
    """The plan's formula counts a round's input **once**; a round makes two calls, so counting it
    once under-prices a round by everything the second call also carries — the memory, the question
    and the prompt — which is the direction a budget may never be wrong in. Pricing both calls
    alike also buys what `per_call_eur` needs: whichever of the two `Accountant.paid_call` is about
    to make, one number bounds it."""
    est = a_round()
    assert est.calls == CALLS_PER_ROUND
    assert est.carried_memory_tokens == CARRIED_MEMORY_TOKENS
    assert est.input_eur_per_call == eur(input_tokens=est.input_tokens_per_call, output_tokens=0)
    # Exact, not approximately: a per-call reservation that sums to less than the operation it
    # belongs to is an under-count, so the total is the per-call price multiplied up.
    assert CALLS_PER_ROUND * est.per_call_eur == est.total_eur
    assert est.total_eur == CALLS_PER_ROUND * (
        eur(input_tokens=est.input_tokens_per_call, output_tokens=MAX_TOKENS)
    )


def test_the_shipped_defaults_price_to_the_cent() -> None:
    """Worked by hand at $5.00/$25.00 per MTok and 1.08 USD/EUR, `final_k = 8`,
    `[chunking] max_tokens = 510`:

    * a passage is `510 * 3 + 250 = 1,780` tokens, so eight are `14,240`;
    * a synthesis call is `14,240 + 1,000 + 1,500 = 16,740` in and `8,000` out
      -> `$0.0837 + $0.2000 = $0.2837` -> **EUR 0.2627**;
    * a round is two calls of `4,000 + 14,240 + 1,000 + 1,500 = 20,740` in and `8,000` out
      -> `$0.1037 + $0.2000 = $0.3037` a call -> **EUR 0.5624**.

    Pinned to the cent *and* to four places: the cent is what a user sees, the four places are what
    catch a constant that moves a call by less than a cent and an operation by euros.
    """
    synthesis = a_synthesis()
    assert synthesis.input_tokens_per_call == 16_740
    assert synthesis.output_tokens_per_call == MAX_TOKENS
    assert synthesis.total_eur.quantize(Decimal("0.01")) == Decimal("0.26")
    assert synthesis.total_eur.quantize(Decimal("0.0001")) == Decimal("0.2627")

    est = a_round()
    assert est.input_tokens_per_call == 20_740
    assert est.total_eur.quantize(Decimal("0.01")) == Decimal("0.56")
    assert est.total_eur.quantize(Decimal("0.0001")) == Decimal("0.5624")


def test_a_passage_is_priced_from_the_manifest_not_from_a_fixed_constant() -> None:
    """Neither `[retrieval] final_k` nor `[chunking] max_tokens` has an upper bound in the
    manifest, so a KB retrieving twenty 2,000-token passages must price as one — a fixed
    per-passage constant would under-reserve exactly the KBs that cost the most."""
    wide = passage_tokens(final_k=20, chunk_max_tokens=2_000)
    assert wide == 20 * (2_000 * VENDOR_TOKENS_PER_CHUNK_TOKEN + PASSAGE_ENVELOPE_TOKENS)
    assert wide > passage_tokens(final_k=FINAL_K, chunk_max_tokens=CHUNK_MAX_TOKENS)


def test_the_passage_ceiling_stays_above_its_own_measurement() -> None:
    """`tools/measure_passage_tokens.py`, 20260811 15:55, over 2,424 chunks: the widest real chunk
    at `max_tokens = 510` holds 2,131 characters in 499 embedding tokens. At a pessimistic 3
    characters per vendor token that is ~710 vendor tokens, against the 1,497 the ceiling reserves
    for the same chunk. A ceiling below its own measurement is not a ceiling (`PAGE_TOKEN_CEILING`
    records the same refusal)."""
    widest_chars, widest_tokens = 2_131, 499
    pessimistic_chars_per_vendor_token = 3
    reserved = widest_tokens * VENDOR_TOKENS_PER_CHUNK_TOKEN
    assert reserved >= widest_chars / pessimistic_chars_per_vendor_token


def test_the_citation_envelope_stays_above_its_own_measurement() -> None:
    """The same command reports the longest `path — heading_path` a passage is wrapped in: **220
    characters** (20260811 16:17). At 2 characters per vendor token — pessimistic, because a path
    fragments into more tokens than prose — that is ~110 tokens. The first draft asserted "under
    120 characters" without running it and sized the constant at 100, which was a ceiling below a
    measurement nobody had taken."""
    longest_envelope_chars = 220
    needed = longest_envelope_chars / 2
    assert needed <= PASSAGE_ENVELOPE_TOKENS


# --- the operation ------------------------------------------------------------------------------


@pytest.mark.parametrize("branch", [DECOMPOSITION, UNKNOWN])
def test_a_loop_operation_is_exactly_max_rounds_times_one_round(branch: str) -> None:
    """`UNKNOWN` prices identically to `DECOMPOSITION` (D-22 option E): the missing signal changes
    when a run *stops*, never what a round costs."""
    one = a_round()
    operation = an_operation(branch=branch, max_rounds=5)
    assert operation.rounds == 5
    assert operation.calls == 5 * CALLS_PER_ROUND
    assert operation.total_eur == 5 * one.total_eur
    assert operation.per_call_eur == one.per_call_eur


def test_the_cheap_branch_operation_is_one_call_whatever_max_rounds_says() -> None:
    operation = an_operation(branch=SYNTHESIS, max_rounds=99)
    assert operation.rounds == 1
    assert operation.calls == 1
    assert operation.total_eur == a_synthesis().total_eur


def test_a_branch_this_module_will_not_price_is_refused_and_names_why() -> None:
    """`cli.py`'s `_escalation` has a fourth branch, `none` — nothing matched. A run with no
    evidence to reason over is not a cheaper run; it is one that must not be offered."""
    with pytest.raises(ValueError, match="none") as exc_info:
        an_operation(branch="none")
    assert SYNTHESIS in str(exc_info.value)


def test_the_shipped_defaults_now_leave_the_whole_loop_inside_every_budget_window(
    write_manifest: Callable[[str], Path],
) -> None:
    """**E4 answered this, and the assertion is inverted rather than deleted** (D-30).

    E2 pinned the finding that at the shipped defaults a `--deep` loop priced *above*
    `per_operation_eur`, so a stock KB would meet a refusal on the release's headline feature —
    D-22 option A's outcome, explicitly rejected, arriving through the caps instead of through the
    signal. D-30 raised the defaults until the loop fits: `per_operation_eur` 0.30 to 2.00,
    `daily_eur` 1.00 to 6.00, and `[deep] max_rounds` fixed at 3 because six calls is what 2.00 has
    to cover.

    Every number is still read out of the *manifest defaults* rather than restated, so the day one
    of them moves this fails instead of drifting. **Both windows are checked, and that is the
    point**: raising `per_operation_eur` alone does nothing, because all three are checked before
    every call and nothing warns that a lower one binds — `daily_eur` was the one that would have
    bound silently.
    """
    manifest = load_manifest(write_manifest(DEFAULTS_MANIFEST.format(kb_id=mint_kb_id())))
    widths = {
        "final_k": manifest.retrieval.final_k,
        "chunk_max_tokens": manifest.chunking.max_tokens,
    }

    cheap = an_operation(branch=SYNTHESIS, **widths)
    loop = an_operation(branch=DECOMPOSITION, max_rounds=manifest.deep.max_rounds, **widths)
    for window in (manifest.budget.per_operation_eur, manifest.budget.daily_eur):
        assert cheap.total_eur <= window
        assert loop.total_eur <= window

    # The `unknown` branch is the one a stock KB actually takes (M6) and it is priced identically —
    # a missing signal changes when a run stops, never what a round costs. Asserted rather than
    # assumed, because it is the branch D-30 was taken for.
    uncalibrated = an_operation(branch=UNKNOWN, max_rounds=manifest.deep.max_rounds, **widths)
    assert uncalibrated.total_eur == loop.total_eur

    # Headroom, not merely fit: a cap a fraction of a cent above the estimate would satisfy every
    # assertion above and still refuse the second question of the day.
    assert manifest.budget.per_operation_eur - loop.total_eur > Decimal("0.30")
    assert manifest.budget.daily_eur >= 3 * loop.total_eur


# --- prices, staleness and the context window ----------------------------------------------------


def test_a_stale_price_table_refuses_and_names_the_age() -> None:
    """The deep path inherits the refusal; it does not get its own policy (§3 of the plan)."""
    with pytest.raises(StalePricesError) as exc_info:
        a_round(table=prices(as_of="20260101 00:00"))
    assert "20260101 00:00" in exc_info.value.message
    assert "30" in exc_info.value.message
    assert "Upgrade pinakes" in exc_info.value.remedy


def test_exactly_at_the_max_price_age_boundary_still_estimates() -> None:
    est = a_round(table=prices(as_of="20260101 00:00"), now="20260131 00:00")
    assert est.calls == CALLS_PER_ROUND


def test_an_unknown_model_price_refuses_rather_than_estimating_at_zero() -> None:
    with pytest.raises(UnknownModelPriceError):
        a_round(model="gpt-5")


def test_the_context_window_precheck_names_the_keys_a_user_can_actually_turn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The PDF path's remedy says K is not a knob — true there, misleading here: a deep round's
    input *is* `final_k` passages of `max_tokens` each, and both are the user's to set."""
    import pinakes.budget.estimate as budget_estimate

    monkeypatch.setitem(budget_estimate.MAX_INPUT_TOKENS, MODEL, 1_000)
    with pytest.raises(ContextWindowExceededError) as exc_info:
        a_round()
    assert "20,740" in exc_info.value.message
    assert "1,000" in exc_info.value.message
    assert "final_k" in exc_info.value.remedy
    assert "max_tokens" in exc_info.value.remedy
    assert "K is a fixed request-shape constant" not in exc_info.value.remedy


def test_a_manifest_alone_can_reach_the_context_window_check() -> None:
    """Unlike the PDF estimator's, this pre-check is reachable without monkeypatching anything:
    374 passages of 800 tokens is 997,600 vendor tokens against a documented 1,000,000, and one
    more passage crosses it. That is why the remedy names two keys rather than calling it a defect
    to report."""
    import pinakes.budget.estimate as budget_estimate

    assert budget_estimate.MAX_INPUT_TOKENS[MODEL] == 1_000_000
    inside = a_round(final_k=374, chunk_max_tokens=800)
    assert inside.input_tokens_per_call < 1_000_000
    with pytest.raises(ContextWindowExceededError):
        a_round(final_k=375, chunk_max_tokens=800)


def test_a_model_with_no_documented_window_skips_the_check() -> None:
    """Mirrors `estimate_document`: nothing to check is not a reason to refuse an otherwise-fine
    estimate."""
    unlisted = Prices(
        as_of=NOW,
        usd_per_eur=Decimal("1.08"),
        models={"some-future-model": ModelPrice(Decimal("1.00"), Decimal("1.00"))},
    )
    est = a_round(model="some-future-model", table=unlisted)
    assert est.calls == CALLS_PER_ROUND


# --- the arithmetic must never be wrong downwards ------------------------------------------------


@pytest.mark.parametrize(
    ("final_k", "chunk_max_tokens", "named"),
    [
        (0, CHUNK_MAX_TOKENS, "final_k"),
        (-3, CHUNK_MAX_TOKENS, "final_k"),
        (FINAL_K, 0, "chunk_max_tokens"),
        (FINAL_K, -1, "chunk_max_tokens"),
    ],
)
def test_a_zero_or_negative_width_is_rejected_by_name(
    final_k: int, chunk_max_tokens: int, named: str
) -> None:
    """A zero `final_k` prices a paid run at output only; a negative one prices it *below zero*.
    Both understate real spend, the one direction a budget guard may never move."""
    with pytest.raises(ValueError, match=named):
        a_round(final_k=final_k, chunk_max_tokens=chunk_max_tokens)


@pytest.mark.parametrize("max_rounds", [0, -1])
def test_a_zero_or_negative_round_cap_is_rejected(max_rounds: int) -> None:
    with pytest.raises(ValueError, match="max_rounds"):
        an_operation(branch=DECOMPOSITION, max_rounds=max_rounds)


def test_every_money_field_is_decimal_end_to_end() -> None:
    """INVARIANTS: money is `Decimal`, and nothing here quantises — the ledger does that, once."""
    operation = an_operation(branch=DECOMPOSITION, max_rounds=3)
    for value in (
        operation.total_eur,
        operation.per_call_eur,
        operation.per_round.input_eur_per_call,
        operation.per_round.output_eur_per_call,
        operation.per_round.total_eur,
    ):
        assert isinstance(value, Decimal)
    # Unquantised: 0.5624074074... per round, not 0.56.
    assert operation.per_round.total_eur != operation.per_round.total_eur.quantize(Decimal("0.01"))


def test_the_reservation_bounds_every_plausible_real_usage() -> None:
    """Hypothetical *actual* usages for one call: a reservation a real call could exceed is not a
    bound at all. The last row is the ceiling itself, which must land exactly on the reservation
    rather than above it."""
    est = a_round()
    usages = [
        (0, 0),
        (2_000, 300),  # a decompose call: question, carried memory, a short subproblem list
        (14_000, 6_000),  # an answer call over eight passages
        (est.input_tokens_per_call, MAX_TOKENS),  # exactly at the ceiling
    ]
    for input_tokens, output_tokens in usages:
        actual = eur(input_tokens=input_tokens, output_tokens=output_tokens)
        assert est.per_call_eur >= actual, (input_tokens, output_tokens)


# --- purity: no client, no I/O, and an __init__ that imports nothing -----------------------------


def _imported_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(f"{node.module}.{alias.name}" if node.module else alias.name)
            if node.module:
                names.add(node.module)
    return names


#: What `deep/estimate.py` may import, module by module. **An allowlist, not a denylist of
#: clients**: a denylist of the ways a module can reach a network, a clock or a disk is never
#: finished, and the one that matters next is always the one nobody listed (`check.sh`'s NUL scan
#: records the same lesson about file suffixes).
ESTIMATOR_IMPORTS = {
    "dataclasses",
    "dataclasses.dataclass",
    "decimal",
    "decimal.Decimal",
    "typing",
    "typing.Final",
    "pinakes.budget.estimate",
    "pinakes.budget.estimate.MAX_INPUT_TOKENS",
    "pinakes.budget.estimate.assert_prices_fresh",
    "pinakes.budget.prices",
    "pinakes.budget.prices.Prices",
    "pinakes.errors",
    "pinakes.errors.ContextWindowExceededError",
}


def test_the_estimator_imports_only_what_a_pure_module_needs() -> None:
    """E2's whole claim is "pure, no client, no I/O, no wall clock". Once E3 adds `deep/client.py`
    beside it, the cheapest way to break that is an import added here for convenience — so a new
    import has to be added to this list on purpose, where it can be argued with."""
    unexpected = _imported_names(DEEP_DIR / "estimate.py") - ESTIMATOR_IMPORTS
    assert not unexpected, unexpected


def test_the_deep_package_init_imports_nothing_at_all() -> None:
    """`pnk ask` is free and will import `pinakes.deep.estimate`. A package `__init__` that reached
    for `client` would drag the paid client into the free path through the import system alone,
    with `tools/paid_path_gate.py` still green — it greps for an import statement that would not be
    in any file it inspects."""
    assert _imported_names(DEEP_DIR / "__init__.py") == set()
