"""`tools/deep_reservation.py` — the CLI as a subprocess, the arithmetic in-process.

A subprocess rather than an import, for the reason `tests/test_measure_sync_cpu.py` gives: it
exercises the same artifact an operator runs by hand, argument parsing included, with no
`sys.path` surgery the type checkers then cannot follow.

**The in-process half exists because some of this is pure arithmetic**, in the sense
`tests/test_eval.py`'s `_load_probe_module` uses: `_ratio`, `Row.marker`, `Spend.settled` and
`summarise` need no CLI run, and asserting a ratio through a JSON round trip would test the
reporting rather than the number.

**The assertion that matters is not "it ran without crashing", and this file exists because that
was the only assertion anything ever made about this tool.** It had no tests at all until
20260821, and three defects had shipped inside it, each invisible to a run that reads the printed
table:

* `--json` called `vars()` on a `slots=True` dataclass and raised `TypeError` on the **first row
  of both subcommands** (fixed in `ad30ab0`). It survived four releases and two measurement
  sessions because every operator read the table. So every output branch here is executed end to
  end, and `--json` is parsed with `json.loads` — never substring-matched, which is exactly the
  assertion that would have passed against the broken version.
* A ledger call left **unresolved** was priced at its *reservation* and printed under a header
  claiming `reconciled ledger spend`. Deleting one reconciliation line from the real measurement
  ledger moved the published figure from `29.75x` to `4.40x`, silently, at exit 0. The number is
  a release deliverable, so *plausible and wrong* is the failure mode this file is mostly about.
* `collect_spend` crashed on any transcript it could not parse — losing the reconciliation for
  every *other* run, after the money was spent — under a comment claiming every read was
  defensive.

**Nothing here needs a key, a network, or model weights, and nothing here spends.** CI holds no
key by ground rule. That puts `count`'s paid half — `_counter`, and the `messages.count_tokens`
requests it issues — out of reach entirely; what stands in for it is the part of `count` that is
not the API: `_ratio`'s rounding, `Row`'s rendering, and `_as_json`'s shape, which is where the
`--json` defect actually lived. The KB fixtures are hand-built files on disk, so `report` runs
against them without an embedding backend ever being resolved.
"""

import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

TOOL = Path(__file__).parent.parent / "tools" / "deep_reservation.py"

KB_ID = "01M0HMR3KCBHY3PJMNKJN6PHDR"
"""A well-formed ULID, spelled out rather than minted: a fixture that names its own ids is one a
failing assertion can quote back."""

MINIMAL_MANIFEST = f"""\
[kb]
name = "probe"
id   = "{KB_ID}"

[sources]

[embedding]
provider = "fake"
model    = "fake"
dim      = 3
"""
"""The smallest manifest `report` accepts.

`[kb]`, `[sources]` and `[embedding]` are the only required tables. **`report` never loads an
embedding backend**, so `provider = "fake"` is never resolved and the whole suite runs on a
`[light]`-free checkout with no weights — which is the property that lets these tests run in CI at
all.
"""


def _module() -> ModuleType:
    """`tools/` is not a package, so the tool is loaded by path rather than imported.

    Copied from `_gate_module` in `tests/test_graph_channel.py`, **including the `sys.modules`
    registration before `exec_module`** — that line is not decoration. `Row` and `Spend` are
    `@dataclass(slots=True)`, and building a slots dataclass re-creates the class and resolves its
    own module out of `sys.modules` to do it, so a module executed outside it raises there.
    """
    spec = importlib.util.spec_from_file_location("deep_reservation", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["deep_reservation"] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Run:
    """One paid run, as the fixture describes it.

    A dataclass rather than a `dict[str, object]`: every field of such a dict types as `object`
    under pyright strict, so `call_ids` is not iterable and a mistyped key is only found at
    runtime — in a fixture whose whole job is to be trusted while the assertions do the work.
    """

    operation_id: str
    branch: str
    call_ids: tuple[str, ...]
    estimated_eur: str
    reserved_usd: str
    actual_usd: str
    spent_eur: str = "0.00"


def _ledger_line(
    *, kind: str, call_id: str, operation_id: str, cost_usd: str, at: str = "2026-08-21T07:15:57"
) -> str:
    """One ledger record, in the shape a real `.pinakes/ledger.jsonl` carries.

    `cost_usd` and `usd_per_eur` are **strings**: a JSON number is rejected as a float, and a line
    that fails to parse is silently counted malformed rather than raised — so a typo in this helper
    would read as a €0.0000 spend and an infinite factor, not as a broken fixture.
    """
    return json.dumps(
        {
            "schema": 1,
            "kind": kind,
            "at": f"{at}+00:00",
            "operation_id": operation_id,
            "call_id": call_id,
            "operation": "ask",
            "kb_id": KB_ID,
            "model": "claude-opus-5",
            "cost_usd": cost_usd,
            "usd_per_eur": "1.00",
            "prices_as_of": "20260728 16:31",
            "input_tokens": None,
            "output_tokens": None,
            "source": "call",
        }
    )


def _kb(
    root: Path,
    *,
    runs: list[Run],
    reconcile: bool = True,
    extra_files: dict[str, str] | None = None,
) -> Path:
    """A KB carrying one transcript per run and a ledger that pays for them.

    `usd_per_eur` is 1.00 throughout, so every euro figure an assertion names is the number written
    into the fixture rather than a conversion of it.
    """
    deep = root / ".pinakes" / "deep"
    deep.mkdir(parents=True, exist_ok=True)
    (root / "pinakes.toml").write_text(MINIMAL_MANIFEST, encoding="utf-8")

    lines: list[str] = []
    for run in runs:
        body: dict[str, object] = {
            "operation_id": run.operation_id,
            "answer": {
                "branch": run.branch,
                "calls": len(run.call_ids),
                "estimated_eur": run.estimated_eur,
                "spent_eur": run.spent_eur,
                "call_ids": list(run.call_ids),
            },
        }
        (deep / f"{run.operation_id}.json").write_text(json.dumps(body, indent=2), encoding="utf-8")
        for call_id in run.call_ids:
            lines.append(
                _ledger_line(
                    kind="reservation",
                    call_id=call_id,
                    operation_id=run.operation_id,
                    cost_usd=run.reserved_usd,
                )
            )
            if reconcile:
                lines.append(
                    _ledger_line(
                        kind="reconciliation",
                        call_id=call_id,
                        operation_id=run.operation_id,
                        cost_usd=run.actual_usd,
                        at="2026-08-21T07:16:01",
                    )
                )
    (root / ".pinakes" / "ledger.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, content in (extra_files or {}).items():
        (deep / name).write_text(content, encoding="utf-8")
    return root


SYNTHESIS_RUN = Run(
    operation_id="01M0HMR3KCBHY3PJMNKJN6PHDS",
    branch="synthesis",
    call_ids=("01M0HMR3KCBHY3PJMNKJN6PHDT",),
    estimated_eur="0.21",
    reserved_usd="0.2100",
    actual_usd="0.0100",
)
DECOMPOSITION_RUN = Run(
    operation_id="01M0HMR3KCBHY3PJMNKJN6PHE0",
    branch="decomposition",
    call_ids=("01M0HMR3KCBHY3PJMNKJN6PHE1", "01M0HMR3KCBHY3PJMNKJN6PHE2"),
    estimated_eur="1.38",
    reserved_usd="0.2300",
    actual_usd="0.0200",
)


_DRIVER = '''\
"""Load the tool, run `report` with stdout swallowed, and report what reached `sys.modules`.

Written to a file and run as its own process so nothing this test suite already imported can
account for a paid module being present.
"""
import importlib.util
import io
import json
import sys

spec = importlib.util.spec_from_file_location("dr", {tool})
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules["dr"] = module
spec.loader.exec_module(module)

held, sys.stdout = sys.stdout, io.StringIO()
code = module.main(["dr", "report", "--kb", {kb}])
sys.stdout = held
print(json.dumps({{"code": code, "paid": sorted(m for m in sys.modules if m == "anthropic")}}))
'''


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False, timeout=120
    )


def _branch_row(stdout: str, branch: str) -> str:
    return next(line for line in stdout.splitlines() if f" {branch} " in line)


# --- the pure arithmetic: what a factor is, and what it must not silently become ---------------


def test_a_factor_is_the_reservation_over_the_measurement_in_that_order() -> None:
    """An inverted ratio is the defect that would not look like one. The release publishes
    `29.75x`; the same numbers divided the other way give `0.03x`, which reads as a **breached**
    ceiling and invites exactly the opposite decision from the one the data supports."""
    row = _module().Row("PROMPT_TOKENS", 1_500, 600)
    assert row.factor == 2.5


def test_a_factor_over_nothing_measured_is_infinite_rather_than_a_crash() -> None:
    """`measured == 0` is reachable in a real run — the `PROMPT_TOKENS` row is built as
    `max(floor, 0)` — and `count` computes it *after* every rate-limited `count_tokens` request has
    already been spent. An unguarded division would throw the measurement away at its last step."""
    assert _module().Row("PROMPT_TOKENS", 1_500, 0).factor == float("inf")


def test_the_marker_separates_a_safe_row_a_breached_one_and_a_failed_measurement() -> None:
    """**Three states, and the third is why this test exists.** `!!` is an under-reservation — a
    measurement *above* its ceiling, the one direction a budget may never be wrong in. `??` is a
    measurement that produced nothing: three code paths clamp to zero, and a zero measurement makes
    `factor` infinite, which sailed past the old `reserved >= measured` test wearing the calm
    two-space marker. An infinite ratio never means *infinitely safe*.

    All three are asserted, because a constant prefix satisfies any one of them alone.
    """
    module = _module()
    assert module.Row("A", 1_500, 376).marker == "  "
    assert module.Row("B", 250, 400).marker == "!!"
    assert module.Row("C", 1_500, 0).marker == "??"


def test_describe_carries_the_name_both_numbers_and_the_ratio() -> None:
    """A pasted table has to stay falsifiable: without `measured`, a reader cannot tell 3x of
    1,500 from 3x of 15."""
    line = _module().Row("PASSAGE_ENVELOPE_TOKENS", 250, 28).describe()
    assert "PASSAGE_ENVELOPE_TOKENS" in line
    assert "reserved     250" in line
    assert "measured      28" in line
    assert "8.93x" in line


def test_a_ratio_rounds_up_because_a_ratio_floored_is_a_ceiling_breached() -> None:
    """5 vendor tokens over 2 embedding tokens is 3, never 2. Flooring understates the conversion,
    and an understated conversion is an under-reservation."""
    assert _module()._ratio(5, 2) == 3
    assert _module()._ratio(4, 2) == 2


def test_a_ratio_refuses_a_degenerate_or_negative_difference() -> None:
    """`vendor` is a *difference* of two counted requests, so a counter returning the pair out of
    order makes it negative — and `-(-v // e)` is a true ceiling, which for a negative numerator
    rounds towards zero. `_ratio(-150, 100)` returned `-1`, and a reservation of 3 against a
    measurement of -1 compares as comfortable and prints the calm marker."""
    module = _module()
    assert module._ratio(150, 0) == 0
    assert module._ratio(-150, 100) == 0
    assert module.Row("VENDOR", 3, module._ratio(-150, 100), unit="x").marker == "??"


def test_spend_divides_decimals_and_floats_only_at_the_end() -> None:
    """Money is `Decimal` end to end (INVARIANTS). Floating both sides first reintroduces the
    representation error `Decimal` exists to prevent, into the one number the release publishes."""
    spend = _module().Spend("op", "synthesis", 1, Decimal("0.21"), Decimal("0.0075"))
    assert spend.factor == 28.0


def test_spend_over_a_zero_ledger_is_infinite_rather_than_a_crash() -> None:
    """Reachable today: a run whose calls were all voided prices at exactly zero. One such run
    would otherwise abort the report for every other branch — after the money was spent."""
    spend = _module().Spend("op", "synthesis", 1, Decimal("0.21"), Decimal("0"))
    assert spend.factor == float("inf")


# --- settlement: the difference between "spent" and "reserved but never closed" ----------------


def test_a_voided_call_is_settled_and_an_unresolved_one_is_not() -> None:
    """**The distinction the published number depends on.** A void closes a call at zero because it
    never billed — which is what happened to every reservation in 0.22.0 through 0.25.0, when the
    API refused the request before it billed. An unresolved call is priced at its *reservation* by
    `Call.effective_eur`, so it lands in the `spent` column; a factor computed over one is not the
    figure this tool claims to print."""
    module = _module()
    voided = module.Spend("op", "synthesis", 1, Decimal("0.21"), Decimal("0"), 0, 1, 0, 0)
    unresolved = module.Spend("op", "synthesis", 1, Decimal("0.21"), Decimal("0.21"), 0, 0, 1, 0)
    unrecorded = module.Spend("op", "synthesis", 1, Decimal("0.21"), Decimal("0"), 0, 0, 0, 1)
    assert voided.settled
    assert not unresolved.settled
    assert not unrecorded.settled


def test_summarise_keeps_the_branches_apart_and_never_blends_them() -> None:
    """D-28's whole argument: one synthesis call against `2 x max_rounds` is the return on having
    a calibrated signal, and a single blended figure hides it. Asserted by giving the two branches
    *different* factors and checking both survive — a blend would produce one number between."""
    module = _module()
    summary = module.summarise(
        [
            module.Spend("a", "synthesis", 1, Decimal("0.21"), Decimal("0.0070")),
            module.Spend("b", "synthesis", 1, Decimal("0.21"), Decimal("0.0070")),
            module.Spend("c", "decomposition", 2, Decimal("1.38"), Decimal("0.0200")),
        ]
    )
    assert set(summary) == {"synthesis", "decomposition"}
    assert summary["synthesis"]["runs"] == 2
    assert summary["synthesis"]["calls"] == 2
    assert summary["decomposition"]["runs"] == 1
    assert summary["synthesis"]["over_reservation"] == pytest.approx(30.0)
    assert summary["decomposition"]["over_reservation"] == pytest.approx(69.0)


def test_one_unsettled_run_marks_its_whole_branch_unsettled() -> None:
    """A branch's factor is a sum over its runs, so a single unresolved call in any of them makes
    the branch total wrong. The flag has to propagate up, or the row prints clean."""
    module = _module()
    summary = module.summarise(
        [
            module.Spend("a", "synthesis", 1, Decimal("0.21"), Decimal("0.0070")),
            module.Spend("b", "synthesis", 1, Decimal("0.21"), Decimal("0.2100"), 0, 0, 1, 0),
        ]
    )
    assert not summary["synthesis"]["settled"]
    assert summary["synthesis"]["unresolved_calls"] == 1


def test_a_count_from_a_file_on_disk_is_accepted_only_if_it_really_is_one() -> None:
    """`int(cast(int, ...))` was neither a check nor a conversion. The two *silent* readings matter
    more than the two loud ones: a truncated float and a numeric string both moved a published call
    count at exit 0. `bool` is excluded deliberately — it is an `int` subclass, and `"calls": true`
    counting as one call is not a reading anyone meant."""
    read = _module()._int
    assert read(3) == 3
    assert read(3.9) == 0
    assert read("3") == 0
    assert read(None) == 0
    assert read(True) == 0


def test_a_money_field_from_a_file_on_disk_never_raises_out_of_the_run() -> None:
    """`Decimal(str(None))` is `InvalidOperation`, not zero — and this runs after the money was
    spent, so a raise here loses the reconciliation rather than preventing a charge."""
    read = _module()._decimal
    assert read("0.21") == Decimal("0.21")
    assert read(None) == Decimal("0")
    assert read({"eur": "0.21"}) == Decimal("0")
    assert read("not a number") == Decimal("0")


# --- `--json`: the branch that shipped broken --------------------------------------------------


def test_as_json_dumps_every_field_and_the_factor_for_both_row_types() -> None:
    """**The exact defect fixed in `ad30ab0`, pinned from the inside.** `vars()` on a `slots=True`
    dataclass raises `TypeError`, so `--json` died on the first row of either subcommand. The
    second half is quieter and would survive a fix that only swapped in `asdict`: `factor` is a
    *property*, so no field-dumping call reaches it, and the machine-readable output would omit the
    one number the whole run exists to publish while the table beside it printed it."""
    module = _module()
    row = module._as_json(module.Row("PROMPT_TOKENS", 1_500, 376))
    assert row["name"] == "PROMPT_TOKENS"
    assert row["reserved"] == 1_500
    assert row["measured"] == 376
    assert row["factor"] == pytest.approx(3.989, abs=0.001)

    spend = module._as_json(module.Spend("op", "synthesis", 1, Decimal("0.21"), Decimal("0.0075")))
    assert spend["operation_id"] == "op"
    assert spend["branch"] == "synthesis"
    assert spend["factor"] == 28.0


def test_a_row_payload_stays_json_native_with_no_serialiser_hook() -> None:
    """The `count` path passes no `default=str`, unlike `report`. Giving `Row` a `Decimal` or
    `Path` field would raise `TypeError` at the very end of a run that has already spent its
    rate-limited budget of `count_tokens` requests — which cannot be re-run cheaply."""
    module = _module()
    json.dumps(module._as_json(module.Row("PROMPT_TOKENS", 1_500, 376)))


# --- the CLI, as an operator runs it ------------------------------------------------------------


def test_report_prints_a_factor_per_branch(tmp_path: Path) -> None:
    kb = _kb(tmp_path / "kb", runs=[SYNTHESIS_RUN, DECOMPOSITION_RUN])
    result = _run("report", "--kb", str(kb))
    assert result.returncode == 0, result.stderr
    assert "21.00x" in _branch_row(result.stdout, "synthesis")
    assert "34.50x" in _branch_row(result.stdout, "decomposition")


def test_report_json_parses_and_carries_the_factor(tmp_path: Path) -> None:
    """Parsed with `json.loads`, never substring-matched: a test asserting `'"factor"' in stdout`
    would pass against output that is not JSON at all, and the defect this pins was a `TypeError`
    raised *inside* `json.dumps` — which no assertion about stdout's text can reach."""
    kb = _kb(tmp_path / "kb", runs=[SYNTHESIS_RUN, DECOMPOSITION_RUN])
    result = _run("report", "--kb", str(kb), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert {run["branch"] for run in payload["runs"]} == {"synthesis", "decomposition"}
    assert payload["by_branch"]["synthesis"]["over_reservation"] == pytest.approx(21.0)
    for run in payload["runs"]:
        assert "factor" in run, "the published number is a property and no field dump reaches it"


def test_the_ledger_prices_a_run_and_the_transcripts_own_number_is_ignored(tmp_path: Path) -> None:
    """**The rule the module docstring states and nothing had ever checked.** A transcript's
    `spent_eur` is a snapshot taken at write time; a later `pnk budget --resolve` moves the real
    figure without touching the file. Driven with a transcript whose `spent_eur` disagrees with its
    own ledger by two orders of magnitude — the report must follow the ledger."""
    kb = _kb(tmp_path / "kb", runs=[replace(SYNTHESIS_RUN, spent_eur="9.99")])
    result = _run("report", "--kb", str(kb), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["runs"][0]["actual_eur"] == "0.0100"
    assert payload["runs"][0]["factor"] == pytest.approx(21.0)


def test_report_refuses_a_kb_with_no_transcripts_and_says_which_directory(tmp_path: Path) -> None:
    """A gate only ever observed passing is a gate nobody has tested. Exit code *and* the stated
    reason: a message naming no directory is compatible with looking in the wrong place."""
    kb = _kb(tmp_path / "kb", runs=[])
    result = _run("report", "--kb", str(kb))
    assert result.returncode == 1
    assert "no transcripts" in result.stderr
    assert str(kb) in result.stderr


def test_an_unresolved_call_is_flagged_rather_than_priced_as_if_it_were_spent(
    tmp_path: Path,
) -> None:
    """**The defect that produced a plausible wrong number.** `Call.effective_eur` falls back to
    the reservation when a call has no outcome — right for a budget guard, which must assume an
    in-flight call billed, and wrong for a measurement, which then reports a *reserved* amount in a
    column headed `spent`. On the real ledger this took the published synthesis figure from
    `29.75x` to `4.40x` at exit 0.

    Both halves are asserted: the row carries the `!!` marker, and stderr says what is wrong and
    how to close it. The figure is still printed — it is the best available reading — so an
    assertion that it disappears would be asserting the wrong fix.
    """
    kb = _kb(tmp_path / "kb", runs=[SYNTHESIS_RUN], reconcile=False)
    result = _run("report", "--kb", str(kb))
    assert result.returncode == 0, result.stderr
    assert _branch_row(result.stdout, "synthesis").startswith("!!")
    assert "never reconciled" in result.stderr
    assert "--resolve" in result.stderr, "the remedy has to be in the message"


def test_a_settled_run_is_not_flagged(tmp_path: Path) -> None:
    """The other direction, without which the marker could be a constant."""
    kb = _kb(tmp_path / "kb", runs=[SYNTHESIS_RUN])
    result = _run("report", "--kb", str(kb))
    assert result.returncode == 0, result.stderr
    assert not _branch_row(result.stdout, "synthesis").startswith("!!")
    assert "never reconciled" not in result.stderr


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("01AAAAAAAAAAAAAAAAAAAAAAAA.json", '{"operation_id": "01AAA", "answer": {"branch": "syn'),
        ("01BBBBBBBBBBBBBBBBBBBBBBBB.json", ""),
        ("01CCCCCCCCCCCCCCCCCCCCCCCC.json", "[1, 2, 3]"),
    ],
)
def test_one_unreadable_transcript_does_not_lose_every_other_reconciliation(
    tmp_path: Path, name: str, content: str
) -> None:
    """**This ran *after* the money was spent, so a crash lost the reconciliation rather than
    preventing a charge** — and it crashed under a comment claiming every read was defensive.

    A truncated file and a zero-byte one raise `JSONDecodeError`; a top-level JSON list raises
    `AttributeError` on `.get`. Each is parametrised rather than merged, because one shape passing
    says nothing about the others — the list case in particular survives `json.loads` entirely and
    fails a line later.
    """
    kb = _kb(tmp_path / "kb", runs=[SYNTHESIS_RUN], extra_files={name: content})
    result = _run("report", "--kb", str(kb))
    assert result.returncode == 0, result.stderr
    assert "21.00x" in _branch_row(result.stdout, "synthesis"), (
        "the readable run's factor must survive its neighbour being unreadable"
    )
    assert "could not be" in result.stderr, "a skipped transcript is reported, never absorbed"


def test_a_transcript_that_is_not_utf8_is_skipped_rather_than_fatal(tmp_path: Path) -> None:
    """A macOS AppleDouble sidecar — `._<ulid>.json` — is matched by `transcript.paths()`, which
    applies no ULID check on read, and appears whenever a KB is copied to exFAT or SMB. That is an
    ordinary way to move a KB, and it produced a `UnicodeDecodeError` that killed the report.
    `transcript.call_ids()` already swallowed it, so `pnk sync --clear-cache=transcripts` could
    price a store this tool died on."""
    kb = _kb(tmp_path / "kb", runs=[SYNTHESIS_RUN])
    (kb / ".pinakes" / "deep" / "._01DDDDDDDDDDDDDDDDDDDDDDDD.json").write_bytes(
        b"\xff\xfe\x00\x01binary"
    )
    result = _run("report", "--kb", str(kb))
    assert result.returncode == 0, result.stderr
    assert "21.00x" in _branch_row(result.stdout, "synthesis")


def test_stray_json_is_never_folded_into_the_real_unknown_branch(tmp_path: Path) -> None:
    """`estimate.UNKNOWN` is the literal string `"unknown"` and names a **real** branch — the
    uncalibrated loop, one of the three figures this run publishes. A fallback sharing its name
    adds a phantom run and €0.00 to that branch's totals with nothing in the output to say so, and
    on a KB whose runs are genuinely `unknown` it would not even create a visible row."""
    unknown_run = replace(SYNTHESIS_RUN, branch="unknown")
    kb = _kb(
        tmp_path / "kb",
        runs=[unknown_run],
        extra_files={"01EEEEEEEEEEEEEEEEEEEEEEEE.json": '{"note": "re-run this"}'},
    )
    result = _run("report", "--kb", str(kb), "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["by_branch"]["unknown"]["runs"] == 1, (
        "the stray file must not be counted as a run of the real `unknown` branch"
    )
    assert "unknown" not in {
        run["branch"] for run in payload["runs"] if run["operation_id"] != unknown_run.operation_id
    }


def test_report_needs_no_api_key_and_never_loads_the_paid_client(tmp_path: Path) -> None:
    """**Observed at runtime, not grepped** — the reason `tests/test_paid_path.py` gives: no
    spelling of an import can hide from `sys.modules`.

    The tool imports `anthropic` inside `_counter` and nowhere else, precisely so `report` — which
    spends nothing and needs no key — never loads the SDK. Asserting that from the source would
    pass against a module-scope import added later inside a `try`.
    """
    kb = _kb(tmp_path / "kb", runs=[SYNTHESIS_RUN])
    driver = tmp_path / "driver.py"
    driver.write_text(_DRIVER.format(tool=repr(str(TOOL)), kb=repr(str(kb))), encoding="utf-8")
    environment = {k: v for k, v in os.environ.items() if k != "PINAKES_ANTHROPIC_API_KEY"}
    result = subprocess.run(
        [sys.executable, str(driver)],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["code"] == 0
    assert verdict["paid"] == [], "`report` loaded the paid SDK it is written never to touch"
