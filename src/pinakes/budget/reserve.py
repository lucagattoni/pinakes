"""The §5 accountant — pure: given an estimate, the configured caps, and what has already been
spent, decide whether a call (or a whole run) may proceed (I6a).

**Before every call, all three ceilings are checked** — `per_operation_eur`, `daily_eur`, and
`monthly_eur` — and if any of `spent.X + reserved` would exceed its cap, the call is never made.
One operation (one `pnk sync`, one `pnk ask --deep`) bounds a single invocation only; the day and
month windows are what stop a *sequence* of invocations, which is the failure mode a hook-driven KB
actually has.

**The whole run is checked before the first call**, not only per call: per-call reservation alone
bounds each call and nothing else, and a run that will certainly blow through a window by call 15
should be refused at call 0, not discovered by watching it fail partway through. `reserve_run` is
that upfront check — it refuses with all three windows' current headroom, the computed estimate,
the complete manifest edit that would admit this run, and a line on the ongoing exposure that edit
creates.

**Two things are checked that way, and only the sentences differ.** `reserve_document` prices one
PDF under a paid extractor; `pnk ask --deep` prices one whole question, whose unit is a round rather
than a page slice (`deep/estimate.py`). Both refuse against the same three windows and both owe the
reader the same manifest edit, so the walk and the edit block live here once, and each caller
supplies only its own headline and its own closing advice — a raised cap is permanent either way,
but a one-run `--extract=` override exists for the extractor and has no counterpart on the deep
path. A second copy of the window walk would be a second place for a refusal to name the wrong cap.

`confirm_above_eur` is evaluated **once, against the whole-run estimate** — never per call
(`reserve` itself does not touch it): a per-call reading against a several-cent slice would prompt
dozens of times for one multi-page document, which is how a confirmation becomes something a user
learns to hold down `y` through.
"""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from pinakes.budget.estimate import Estimate
from pinakes.budget.window import WindowTotals

_CENT = Decimal("0.01")


def _display(amount: Decimal) -> str:
    """Round-half-up to the cent for a human-facing message only — the comparisons above run at
    full `Decimal` precision throughout; quantisation for *storage* happens once, at ledger-write
    time (I6b), and this is a separate, display-only rounding that never feeds back into a
    decision."""
    return str(amount.quantize(_CENT, rounding=ROUND_HALF_UP))


#: (attribute on `Caps`, attribute on `WindowTotals`, display name) — one row per window, checked
#: in this order everywhere the three are named together.
_WINDOWS: tuple[tuple[str, str, str], ...] = (
    ("per_operation_eur", "operation", "per_operation_eur"),
    ("daily_eur", "day", "daily_eur"),
    ("monthly_eur", "month", "monthly_eur"),
)


@dataclass(frozen=True, slots=True)
class Caps:
    per_operation_eur: Decimal
    daily_eur: Decimal
    monthly_eur: Decimal


@dataclass(frozen=True, slots=True)
class Decision:
    """The outcome of one per-call `reserve()` check."""

    allowed: bool
    blocked_by: str | None = None
    """Which window refused it — `"per_operation_eur"`, `"daily_eur"` or `"monthly_eur"` — `None`
    when `allowed`."""
    message: str | None = None
    """A ready-to-print refusal, set only when `allowed` is `False`."""


@dataclass(frozen=True, slots=True)
class RunDecision:
    """The outcome of a whole-run precheck: `reserve_document()`, or `reserve_run()` directly.

    Named for the *run* and not for the document since E4, when `pnk ask --deep` became the second
    caller. The type never had anything document-shaped in it — a name that describes only the
    first caller is how the second one ends up with a second type.
    """

    allowed: bool
    needs_confirmation: bool
    """`confirm_above_eur` reached — a soft prompt, meaningful only when `allowed`."""
    message: str | None = None
    """The complete, multi-line refusal — every window's headroom, the estimate, the manifest
    edit that would admit this run, and the ongoing-exposure line. Set only when not `allowed`."""


def reserve(reserved_eur: Decimal, caps: Caps, spent: WindowTotals) -> Decision:
    """Check one call's estimated cost against all three windows, in order. The first window it
    would breach is the one named — the call is refused before any of the others are even
    checked, since one honest reason is clearer than three, and the caller cannot make the call
    anyway."""
    for cap_attr, spent_attr, name in _WINDOWS:
        cap = getattr(caps, cap_attr)
        already = getattr(spent, spent_attr)
        would_be = already + reserved_eur
        if would_be > cap:
            message = (
                f"refused: the {name} cap of €{_display(cap)} would be exceeded "
                f"(already spent €{_display(already)} this window, this call would add "
                f"€{_display(reserved_eur)}, total €{_display(would_be)})."
            )
            return Decision(allowed=False, blocked_by=name, message=message)
    return Decision(allowed=True)


DOCUMENT_CLOSING = (
    "Raising a cap is a permanent, ongoing exposure to every future run at that ceiling — a "
    "one-run `--extract=<backend>` override changes only this invocation, not the manifest."
)
"""What `reserve_document`'s refusal ends on. A constant so the extractor's own tests can assert
the sentence without repeating it, the way the deep path's closing is passed in."""


def reserve_document(
    estimate: Estimate, caps: Caps, spent: WindowTotals, *, confirm_above_eur: Decimal
) -> RunDecision:
    """Check a whole document's worst-case estimate against all three windows before the first
    call. Unlike `reserve`, a refusal here names *every* window at once — walking a user through
    one manifest edit, then a second, then a third, to discover the actual ceiling is precisely
    the defect this exists to avoid."""
    return reserve_run(
        total_eur=estimate.total_eur,
        headline=(
            f"extracting {estimate.pages_estimated} page(s) of {estimate.pages_total} with "
            f"{estimate.model} is estimated at €{_display(estimate.total_eur)} "
            f"({estimate.requests} request(s), worst case)"
        ),
        closing=DOCUMENT_CLOSING,
        caps=caps,
        spent=spent,
        confirm_above_eur=confirm_above_eur,
    )


def reserve_run(
    *,
    total_eur: Decimal,
    headline: str,
    closing: str,
    caps: Caps,
    spent: WindowTotals,
    confirm_above_eur: Decimal,
) -> RunDecision:
    """The whole-run check, for anything whose cost is known before its first call.

    `headline` says what the run *is* and what it is estimated at, in the caller's own vocabulary —
    pages and requests for the extractor, rounds and calls for `pnk ask --deep`. `closing` is the
    advice that follows the manifest edit, which genuinely differs: the extractor has a one-run
    `--extract=` override and the deep path has none.

    Everything between the two is this function's, and that is the part that must never be written
    twice: which windows are blocked, each one's headroom, and the exact `[budget]` edit that would
    admit the run. A refusal naming one cap at a time is the defect the message shape exists to
    avoid, and it is reintroduced the moment a second caller writes its own.
    """
    blocked = [
        (cap_attr, name, getattr(caps, cap_attr), getattr(spent, spent_attr))
        for cap_attr, spent_attr, name in _WINDOWS
        if getattr(spent, spent_attr) + total_eur > getattr(caps, cap_attr)
    ]
    if blocked:
        return RunDecision(
            allowed=False,
            needs_confirmation=False,
            message=_refusal_message(
                headline=headline, closing=closing, total_eur=total_eur, blocked=blocked
            ),
        )
    return RunDecision(allowed=True, needs_confirmation=total_eur > confirm_above_eur)


def _refusal_message(
    *,
    headline: str,
    closing: str,
    total_eur: Decimal,
    blocked: list[tuple[str, str, Decimal, Decimal]],
) -> str:
    lines = [
        f"refused: {headline}, which exceeds {len(blocked)} of the three budget windows:",
    ]
    edits: list[str] = []
    for cap_attr, name, cap, already in blocked:
        headroom = cap - already
        # Negative when a cap was lowered below already-recorded spend for this window (the cap
        # check itself never lets `already` alone exceed a cap that held for the whole window) —
        # "headroom €-1.00" reads as a typo, not as already being over.
        headroom_text = (
            f"headroom €{_display(headroom)}"
            if headroom >= 0
            else f"already €{_display(-headroom)} over cap"
        )
        minimum_cap = (already + total_eur).quantize(_CENT, rounding=ROUND_CEILING)
        lines.append(
            f"  - {name}: cap €{_display(cap)}, already spent €{_display(already)} this window, "
            f"{headroom_text} — this run needs €{_display(total_eur)}."
        )
        edits.append(f"{cap_attr} = {minimum_cap}")
    lines.append("The complete manifest edit that would admit this run:")
    lines.append("  [budget]")
    lines.extend(f"  {edit}" for edit in edits)
    lines.append(closing)
    return "\n".join(lines)
