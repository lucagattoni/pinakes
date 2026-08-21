"""E6's instrument: how far `pnk ask --deep`'s reservation sits above what it really costs.

**Two subcommands, because the measurement has two halves and only one of them spends**
(docs/MEASUREMENT-RUN.md § The deep-loop run):

    count    free.  `messages.count_tokens` over the *real* requests `deep/client.py` builds,
                    against the real passages a real free search returned. Settles every input
                    constant in `deep/estimate.py` exactly.
    report   free.  Joins the transcripts a measured run left behind to the ledger and publishes
                    the over-reservation factor per branch.

**Token counting is free** — "free to use but subject to requests per minute rate limits", on a
pool independent of message creation. So the input half costs nothing and the euros go only where
nothing else can answer: the output ceiling, the branch behaviour, and the reconciled spend.

**Every constant is measured by *differencing*, never by re-deriving.** A request is counted twice
under shapes that differ in exactly one term, and the difference is that term's real cost. Reading
a total and attributing it to a constant by arithmetic would be a re-derivation, which is the exact
mistake `PAGE_TOKEN_CEILING`'s comment records — and the extractor run's own step (a) forbids it in
so many words: *compare against the measurement, not against a re-derivation*.

**Nothing here ever lowers a constant.** It prints `measured` beside `reserved` and the factor
between them; changing a ceiling is a human's decision, made in the knowledge that these numbers
come from a synthetic corpus (E6's exit criterion). A tool that edited `estimate.py` would be
doing the one thing the ceiling exists to prevent.

**The paid client is imported lazily, inside the one function that calls it** — the pattern
`tools/record_claude_fixtures.py` established. `.paid-path-allowlist` governs `src/` and this file
is not in it; keeping the import out of module scope means `report`, which spends nothing and
needs no key, never loads the SDK at all.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

if TYPE_CHECKING:  # imports for annotations only — nothing here loads at runtime
    from collections.abc import Sequence

    from pinakes.deep.client import Passage
    from pinakes.manifest import Manifest

# --- the shapes a measurement comes in --------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Row:
    """One constant, as measured against what E2 reserved for it."""

    name: str
    reserved: int
    measured: int
    unit: str = "tokens"

    @property
    def factor(self) -> float:
        """How many times the reservation exceeds the measurement. `inf` when nothing was used."""
        return float("inf") if self.measured <= 0 else self.reserved / self.measured

    @property
    def marker(self) -> str:
        """Two characters that say which of three things this row is.

        **`inf` is not a passing grade, and it used to print like one.** Three code paths clamp a
        measurement to zero — `max(floor, 0)` and `_ratio`'s two guards — and a zero measurement
        makes `factor` infinite, which sailed past the old `reserved >= measured` test wearing the
        calm marker. An infinite ratio never means *the reservation is infinitely safe*; it means
        **the differencing produced nothing and this row measured nothing**, which is the one
        outcome an operator must not paste into a release note. It gets its own marker rather than
        sharing either of the others.
        """
        if self.measured <= 0:
            return "??"
        return "  " if self.reserved >= self.measured else "!!"

    def describe(self) -> str:
        return (
            f"{self.marker} {self.name:<32} reserved {self.reserved:>7,}  "
            f"measured {self.measured:>7,} {self.unit:<6}  {self.factor:>6.2f}x"
        )


#: The branch name given to a transcript that could not be read or carries no branch.
#:
#: **Deliberately not `"unknown"`.** `estimate.UNKNOWN` is that exact string and names a *real*
#: branch — the uncalibrated loop, which is one of the three figures this run publishes. A fallback
#: sharing its name folds every unreadable file into that branch's statistics: on a KB whose runs
#: are genuinely `unknown`, a stray JSON file adds a phantom run and EUR 0.00 to a published total
#: with nothing in the output to say so. The parentheses are not decoration — no branch constant
#: can ever collide with a name that is not an identifier.
UNREADABLE: Final = "(unreadable)"


@dataclass(frozen=True, slots=True)
class Spend:
    """One transcript, priced from the ledger rather than from its own copy of the number."""

    operation_id: str
    branch: str
    calls: int
    estimated_eur: Decimal
    actual_eur: Decimal
    reconciled_calls: int = 0
    voided_calls: int = 0
    unresolved_calls: int = 0
    """Reserved, with neither a reconciliation nor a void. **Priced at its reservation** by
    `Call.effective_eur`, which is right for a budget guard and wrong for a measurement: it lands
    in the `spent` column and pulls the published factor towards 1.0."""
    unrecorded_calls: int = 0
    """Named by the transcript and absent from the ledger entirely — contributes nothing, so it
    pulls the factor the *other* way. Reachable when a ledger is truncated or a KB is copied
    without it."""

    @property
    def settled(self) -> bool:
        """True when every call this run named reached a terminal outcome in the ledger.

        A **voided** call is settled: it is closed at zero because it never billed, which is
        exactly what the deep path does to a reservation whose request was refused — all of
        0.22.0-0.25.0's `400`s ended this way. An **unresolved** or **unrecorded** one is not, and
        a factor computed over either is not the number this tool claims to print.
        """
        return self.unresolved_calls == 0 and self.unrecorded_calls == 0

    @property
    def factor(self) -> float:
        return float("inf") if not self.actual_eur else float(self.estimated_eur / self.actual_eur)


def _as_json(row: Row | Spend) -> dict[str, Any]:
    """One measured row, as JSON — **`asdict`, never `vars`**, and carrying its `factor`.

    Two defects in one line, both found by this tool's own first test run (20260821 08:15) and
    neither reachable from the human-readable output that every earlier run used:

    * **`vars()` raises on both of these types.** `Row` and `Spend` are `slots=True`, so neither
      instance has a `__dict__` for `vars` to return — `--json` did not print a worse answer, it
      raised `TypeError` on the first row of either subcommand. It shipped that way because
      nothing had ever called it: the measurement runs read the printed table.
    * **`factor` is the published number and is not a field.** It is a property on both types, so
      no field-dumping call reaches it, and the JSON a machine reads would have omitted the one
      figure the whole run exists to produce while the table beside it printed it.

    `float("inf")` is preserved as the string `Infinity` by `json.dumps` — not valid JSON, but the
    honest rendering of a division by a zero spend, and the alternative (`null`) is
    indistinguishable from a row that was never measured.
    """
    return {**asdict(row), "factor": row.factor}


# --- the free half: count_tokens over the requests the loop really builds ----------------------


def _counter(model: str):
    """A `count_tokens` callable, with the SDK imported here and nowhere else.

    The key goes through `paid.resolve_api_key`, so this obeys the same rule every paid surface
    does: `PINAKES_ANTHROPIC_API_KEY` and never the SDK's own variable, however the machine is
    configured. `surface` names *this tool*, because that is what the operator ran.
    """
    import anthropic

    from pinakes.paid import build_client_kwargs, resolve_api_key

    key = resolve_api_key(surface="tools/deep_reservation.py (token counting, free)")
    client = anthropic.Anthropic(api_key=key, **build_client_kwargs())

    def count(request: dict[str, Any]) -> int:
        """Count the request `deep/client.py` really builds, minus only its output cap.

        **Everything that shapes the input is passed through, `output_config` included.** The
        schema rides in there, and a filter that kept only `messages` would silently exclude the
        instructions-plus-schema half of `PROMPT_TOKENS` — measuring a fraction of the constant
        while reporting it as the whole. `max_tokens` is dropped because it bounds *output*, which
        this endpoint does not price.
        """
        payload = {k: v for k, v in request.items() if k != "max_tokens"}
        return int(client.messages.count_tokens(**payload).input_tokens)

    return count


def _retrieval_args(kb: Path) -> argparse.Namespace:
    """The Namespace `cli._retrieval` reads, with every filter at its neutral value.

    Built rather than parsed, because the measurement wants the *unfiltered* pipeline: D-27 gives
    `--deep` every one of `pnk search`'s filters, and a filter left set would silently measure a
    narrower corpus than the one being reported on.
    """
    return argparse.Namespace(
        kb=kb,
        offline=False,
        tag=[],
        path_prefix=None,
        source_type=None,
        modified_after=None,
        modified_before=None,
        k=None,
    )


def _passages(kb: Path, question: str) -> tuple[Manifest, tuple[Passage, ...]]:
    """The real passages a real free search returns — never a fixture.

    E2 prices the evidence term at `final_k` passages of `[chunking] max_tokens`; measuring it
    against invented text would measure the invention. **This goes through `cli._retrieval`, the
    same §4.1 pipeline the loop's own retrieval step opens** — a second wiring of `search()` here
    would be a second pipeline wearing one name, which is the thing that helper exists to prevent.
    """
    # Deliberately the private helper: see the docstring above. A public re-wiring of `search()`
    # here would be the second pipeline this exists to avoid, so the underscore is accepted rather
    # than worked around.
    from pinakes.cli import _retrieval  # pyright: ignore[reportPrivateUsage]

    with _retrieval(_retrieval_args(kb)) as pipeline:
        found = tuple(pipeline.search(question).passages)[: pipeline.final_k]
        return pipeline.manifest, found


def measure_inputs(kb: Path, question: str, model: str) -> tuple[list[Row], dict[str, Any]]:
    """Difference the real requests to isolate every input constant E2 declares."""
    from dataclasses import replace

    from pinakes.deep import estimate as est
    from pinakes.deep.client import SYNTHESIS, build_answer_request, build_decompose_request

    manifest, found = _passages(kb, question)
    if len(found) < 2:
        raise SystemExit(
            f"deep_reservation: {kb} returned {len(found)} passages for {question!r}; "
            "the differencing needs at least two. Index the KB, or pick a question that retrieves."
        )
    count = _counter(model)

    def answer_req(passages: Sequence[Passage], q: str) -> dict[str, Any]:
        return build_answer_request(
            model=model, kind=SYNTHESIS, question=q, passages=passages, passage_cap=len(found)
        )

    # Each pair differs in exactly one term; the difference is that term's real cost.
    full = count(answer_req(found, question))
    one_fewer = count(answer_req(found[:-1], question))
    per_passage = full - one_fewer

    hollow = replace(found[-1], text="")
    envelope = count(answer_req((*found[:-1], hollow), question)) - one_fewer

    # Filled to the bound E2 reserves for, exactly as the memory probe below is. Differencing
    # against an arbitrary long question would measure the probe -- append 200 words and the answer
    # comes back 200 -- rather than what a question at its ceiling actually costs.
    long_q = ("word " * est.QUESTION_CHAR_CEILING)[: est.QUESTION_CHAR_CEILING]
    per_question = count(answer_req(found, long_q)) - count(answer_req(found, "?"))

    # The floor: everything that is neither the question nor the evidence.
    floor = full - per_passage * len(found) - (full - count(answer_req(found, "?")))

    # Filled to exactly the bound a round is priced at, so this measures what E2 actually
    # reserved for carried memory rather than what some smaller sample happened to use.
    memory = ("word " * est.CARRIED_MEMORY_CHAR_CEILING)[: est.CARRIED_MEMORY_CHAR_CEILING]
    with_memory = count(
        build_decompose_request(model=model, question=question, memory=memory, max_subproblems=6)
    )
    without_memory = count(
        build_decompose_request(model=model, question=question, memory="", max_subproblems=6)
    )
    memory_tokens = with_memory - without_memory

    backend_tokens = _embedding_tokens(manifest, found[-1].text)
    rows = [
        Row("PROMPT_TOKENS", est.PROMPT_TOKENS, max(floor, 0)),
        Row("QUESTION_TOKENS", est.QUESTION_TOKENS, per_question),
        Row("PASSAGE_ENVELOPE_TOKENS", est.PASSAGE_ENVELOPE_TOKENS, envelope),
        Row(
            "VENDOR_TOKENS_PER_CHUNK_TOKEN",
            est.VENDOR_TOKENS_PER_CHUNK_TOKEN,
            _ratio(per_passage - envelope, backend_tokens),
            unit="x",
        ),
        Row("CARRIED_MEMORY_TOKENS", est.CARRIED_MEMORY_TOKENS, memory_tokens),
    ]
    context = {
        "kb": str(kb),
        "model": model,
        "question": question,
        "passages": len(found),
        "per_passage_tokens": per_passage,
        "chunk_max_tokens": manifest.chunking.max_tokens,
        "reserved_per_passage": manifest.chunking.max_tokens * est.VENDOR_TOKENS_PER_CHUNK_TOKEN
        + est.PASSAGE_ENVELOPE_TOKENS,
    }
    return rows, context


def _ratio(vendor: int, embedding: int) -> int:
    """Vendor tokens per embedding token, rounded **up** — a ratio floored is a ceiling breached.

    Both guards return 0, which `Row.marker` renders `??` rather than as an infinitely safe
    reservation. **The negative guard is not theoretical**: `vendor` is a difference of two counted
    requests, so a counter that returned the pair out of order makes it negative — and `-(-v // e)`
    is a true ceiling, which for a negative numerator rounds *towards zero*. `_ratio(-150, 100)`
    returned `-1`, and a reservation of 3 against a measurement of -1 compares as comfortable.
    """
    if embedding <= 0 or vendor <= 0:
        return 0
    return -(-vendor // embedding)


def _embedding_tokens(manifest: Any, text: str) -> int:
    """The chunk's width in the *embedding* tokenizer — the unit `[chunking] max_tokens` is in."""
    from pinakes.embed import load_backend

    return int(load_backend(manifest.embedding).count_tokens(text))


def manifest_final_k(kb: Path) -> int:
    from pinakes.manifest import load as load_manifest

    return load_manifest(kb).retrieval.final_k


# --- the free half: the transcripts, priced from the ledger ------------------------------------


def _read_body(path: Path) -> dict[str, object] | None:
    """One transcript, or `None` if it is not a JSON object this can read.

    **The comment that used to sit here claimed this was defensive and it was not.** `json.loads`
    was unguarded and `cast` does nothing at runtime, so a single unreadable file aborted the whole
    report before one row printed — losing the reconciliation for every *other* run, after the
    money was spent. Four shapes were reproduced doing it: a truncated file, a zero-byte file, a
    top-level JSON list (`AttributeError` on `.get`), and a macOS AppleDouble sidecar
    `._<ulid>.json` which `transcript.paths()` globs because it applies no ULID check on read —
    and which appears
    whenever a KB is copied to exFAT or SMB, an ordinary way to move one.

    **`transcript.call_ids()` already swallows exactly these**, which is why `pnk sync
    --clear-cache=transcripts` could price a store this tool died on. Diverging from the helper
    whose behaviour this module's own docstring cites was the defect, not a design choice.
    """
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return cast(dict[str, object], body) if isinstance(body, dict) else None


def _int(value: object, *, default: int = 0) -> int:
    """A count from a file on disk — accepted only if it really is one.

    `int(cast(int, ...))` was neither a check nor a conversion: `"calls": 3.9` truncated silently to
    3 and summed into a published call count, `"calls": "3"` was accepted, and `null` or `"many"`
    raised out of the whole run. The two silent ones are worse than the two loud ones, because they
    move a number an operator then pastes into a release note. `bool` is excluded deliberately —
    it is an `int` subclass, and `"calls": true` counting as one call is not a reading anyone meant.
    """
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _decimal(value: object, *, default: str = "0") -> Decimal:
    """A money figure from a file on disk. `Decimal(str(None))` is `InvalidOperation`, not zero."""
    if isinstance(value, str | int) and not isinstance(value, bool):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return Decimal(default)
    return Decimal(default)


def _settlement(manifest: Manifest, ids: set[str]) -> tuple[int, int, int, int]:
    """`(reconciled, voided, unresolved, unrecorded)` for exactly these `call_id`s.

    **Asked separately from the money, and deliberately so.** `sync.ledger_spend` stays the one
    place a euro figure comes from — a second expression of that arithmetic here would be a second
    answer to *what did this cost*. This asks a different question, *did the ledger finish
    answering it*, which `ledger_spend` cannot report because it returns a single string.
    """
    from pinakes.budget import ledger

    resolved = ledger.resolve(ledger.read(ledger.ledger_path(manifest.state_dir)).records)
    states = {call.call_id: call.state for call in resolved.calls if call.call_id in ids}
    counted = collections.Counter(states.values())
    return (
        counted[ledger.CallState.RECONCILED],
        counted[ledger.CallState.VOIDED],
        counted[ledger.CallState.UNKNOWN],
        len(ids - set(states)),
    )


def collect_spend(kb: Path) -> tuple[list[Spend], int]:
    """Every transcript on disk joined to the ledger, and how many were unreadable.

    **The ledger is asked what a run cost, never the transcript** — a transcript's `spent_eur` is a
    snapshot taken at write time and a later `pnk budget --resolve` moves the number without
    touching the file. `transcript.call_ids()` + `sync.ledger_spend()` is the join E5 left for this,
    and it is the same one `paid_cache_spend` already used.

    **And the ledger is asked *how* it settled, not only the total.** `Call.effective_eur` prices a
    reservation with no outcome at the reservation — correct for a budget guard, which must assume
    an in-flight call billed, and wrong for a measurement, which would report a reserved amount in
    a column headed `spent`. Measured on this repository's own run: dropping one reconciliation
    line took the published synthesis factor from **29.75x to 4.40x**, silently, at exit 0.
    `pnk budget` says loudly that unknown outcomes hold that money; this said nothing at all.
    """
    from pinakes.deep import transcript
    from pinakes.manifest import load as load_manifest
    from pinakes.sync import ledger_spend

    manifest = load_manifest(kb)
    out: list[Spend] = []
    unreadable = 0
    for path in transcript.paths(manifest.state_dir):
        body = _read_body(path)
        if body is None:
            unreadable += 1
            continue
        raw = body.get("answer")
        answer = cast(dict[str, object], raw) if isinstance(raw, dict) else {}
        listed = answer.get("call_ids")
        ids: set[str] = set()
        if isinstance(listed, list):
            ids = {c for c in cast(list[object], listed) if isinstance(c, str)}
        raw_branch = answer.get("branch")
        branch = raw_branch if isinstance(raw_branch, str) and raw_branch else UNREADABLE
        reconciled, voided, unresolved, unrecorded = _settlement(manifest, ids)
        out.append(
            Spend(
                operation_id=str(body.get("operation_id", path.stem)),
                branch=branch,
                calls=_int(answer.get("calls")),
                estimated_eur=_decimal(answer.get("estimated_eur")),
                actual_eur=Decimal(ledger_spend(manifest, ids)),
                reconciled_calls=reconciled,
                voided_calls=voided,
                unresolved_calls=unresolved,
                unrecorded_calls=unrecorded,
            )
        )
    return out, unreadable


def summarise(rows: list[Spend]) -> dict[str, dict[str, Any]]:
    """Per branch, because a blended figure hides the whole return on a calibrated signal (D-28).

    Each branch also carries `settled`: false when any run in it named a call the ledger has not
    closed. A branch's factor is only the number this tool claims to publish while that is true.
    """
    by: dict[str, dict[str, Any]] = {}
    for row in rows:
        seen = by.setdefault(
            row.branch,
            {
                "runs": 0,
                "calls": 0,
                "estimated_eur": Decimal("0"),
                "actual_eur": Decimal("0"),
                "unresolved_calls": 0,
                "unrecorded_calls": 0,
            },
        )
        seen["runs"] += 1
        seen["calls"] += row.calls
        seen["estimated_eur"] += row.estimated_eur
        seen["actual_eur"] += row.actual_eur
        seen["unresolved_calls"] += row.unresolved_calls
        seen["unrecorded_calls"] += row.unrecorded_calls
    for seen in by.values():
        actual = seen["actual_eur"]
        seen["over_reservation"] = (
            float("inf") if not actual else float(seen["estimated_eur"] / actual)
        )
        seen["settled"] = not (seen["unresolved_calls"] or seen["unrecorded_calls"])
    return by


# --- entry point -------------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="deep_reservation")
    sub = parser.add_subparsers(dest="command", required=True)

    counted = sub.add_parser("count", help="measure E2's input constants (free)")
    counted.add_argument("--kb", type=Path, required=True)
    counted.add_argument("--question", default="How long do items stay in quarantine?")
    counted.add_argument("--model", default="claude-opus-5")
    counted.add_argument("--json", action="store_true")

    reported = sub.add_parser("report", help="publish the over-reservation factor (free)")
    reported.add_argument("--kb", type=Path, required=True)
    reported.add_argument("--json", action="store_true")

    args = parser.parse_args(argv[1:])

    if args.command == "count":
        rows, context = measure_inputs(args.kb, args.question, args.model)
        if args.json:
            print(json.dumps({"context": context, "rows": [_as_json(r) for r in rows]}, indent=2))
            return 0
        print(f"# input constants, measured on {context['kb']} ({context['passages']} passages)")
        print("# synthetic corpus — no constant below is a licence to lower a ceiling.\n")
        for row in rows:
            print(row.describe())
        print(
            f"\n  per passage: measured {context['per_passage_tokens']:,} vendor tokens against "
            f"{context['reserved_per_passage']:,} reserved "
            f"(at [chunking] max_tokens = {context['chunk_max_tokens']})"
        )
        return 0

    rows, unreadable = collect_spend(args.kb)
    if not rows:
        print(f"deep_reservation: no transcripts under {args.kb}/.pinakes/deep/", file=sys.stderr)
        return 1
    summary = summarise(rows)
    if args.json:
        print(
            json.dumps(
                {
                    "runs": [_as_json(r) for r in rows],
                    "by_branch": summary,
                    "unreadable_transcripts": unreadable,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    print("# over-reservation, per branch (estimate / reconciled ledger spend)\n")
    for branch, seen in sorted(summary.items()):
        print(
            f"{'  ' if seen['settled'] else '!!'} {branch:<15} "
            f"{seen['runs']:>2} runs, {seen['calls']:>2} calls   "
            f"reserved EUR {seen['estimated_eur']:>8.4f}   spent EUR {seen['actual_eur']:>8.4f}   "
            f"{seen['over_reservation']:>6.2f}x"
        )
    # Printed *after* the table and never in place of it: the figures are still the best available
    # reading, and an operator who pastes one needs to know which of them is not what it says.
    for branch, seen in sorted(summary.items()):
        if seen["settled"]:
            continue
        print(
            f"\n!! {branch}: {seen['unresolved_calls']} call(s) reserved but never reconciled, "
            f"{seen['unrecorded_calls']} named by a transcript and absent from the ledger.\n"
            "   An unreconciled call is priced at its RESERVATION, so it lands in `spent` and\n"
            "   pulls this factor towards 1.0. Close them with `pnk budget --resolve <call_id>\n"
            "   --actual <eur>` and re-run; until then this row is not the number it claims.",
            file=sys.stderr,
        )
    if unreadable:
        print(
            f"\n!! {unreadable} transcript(s) under {args.kb}/.pinakes/deep/ could not be\n"
            "   read, and are excluded from every figure above.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
