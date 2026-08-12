"""`.pinakes/deep/<operation_id>.json` — the record one paid run leaves behind (E5, D-26 A).

Two layers, because the transcript has two jobs and they fail differently.

* **The file**: what it holds, where it lands, and that nothing can file one under a name that is
  not a ULID. Driven against a hand-built `DeepAnswer`, so it needs no run and no transport.
* **The protection**: it is swept by nothing, survives `--rebuild`, and is destroyed only by
  `pnk sync --clear-cache=transcripts`. Driven through `sync()` and through the real CLI, because
  the thing being asserted is that *the other spellings of that flag leave it alone* — and a flag's
  spelling is only real at the command line.

The end-to-end half — a run writes one, a free command does not — lives in `tests/test_cli_ask.py`
beside the fixtures that can drive a scripted `--deep` run.
"""

import json
import os
import sys
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

from pinakes.cli import main
from pinakes.deep import transcript
from pinakes.deep.client import CallTally
from pinakes.deep.estimate import OperationEstimate, RoundEstimate
from pinakes.deep.loop import ANSWERED, SYNTHESIS, AnswerBlock, Citation, DeepAnswer
from pinakes.deep.transcript import FILE_SUFFIX
from pinakes.init import init
from pinakes.manifest import load
from pinakes.sync import CLEAR_TRANSCRIPTS, SyncOptions, sync

OPERATION_ID = "01K2ZQZQZQZQZQZQZQZQZQZQZQ"
"""A well-formed ULID. Spelled out rather than minted, so a test that asserts *where* a transcript
landed names the path it expects instead of the path the code chose."""


def _answer(*, spent: str = "0.2600", calls: int = 1) -> DeepAnswer:
    """One cheap-branch run's result — the smallest `DeepAnswer` that is not degenerate."""
    per_round = RoundEstimate(
        model="claude-opus-5",
        calls=1,
        carried_memory_tokens=0,
        passages=8,
        input_tokens_per_call=5_000,
        output_tokens_per_call=2_000,
        input_eur_per_call=Decimal("0.0231"),
        output_eur_per_call=Decimal("0.2396"),
    )
    return DeepAnswer(
        branch=SYNTHESIS,
        blocks=(
            AnswerBlock(
                round_number=0,
                asked=(),
                text="Sourdough rewards a patient starter [1].",
                citations=(
                    Citation(number=1, doc_id="DOC1", path="docs/b.md", locator="docs/b.md:1-4"),
                ),
            ),
        ),
        rounds_used=1,
        stopped_by=ANSWERED,
        label="answered in one synthesis call",
        estimate=OperationEstimate(
            model="claude-opus-5", branch=SYNTHESIS, rounds=1, per_round=per_round
        ),
        tally=CallTally(
            calls=calls,
            call_ids=[f"CALL{n}" for n in range(calls)],
            input_tokens=4_012,
            output_tokens=311,
            cost_usd=Decimal("0.2808"),
        ),
        spent_eur=Decimal(spent),
        partial=False,
    )


def _record(
    operation_id: str = OPERATION_ID, *, calls: int = 1, **overrides: object
) -> dict[str, object]:
    fields: dict[str, object] = {
        "deep": _answer(calls=calls),
        "operation_id": operation_id,
        "question": "what does sourdough need?",
        "filters": {
            "tags": ["baking"],
            "path_prefix": "docs/",
            "source_type": None,
            "modified_after": "20260101",
            "modified_before": None,
        },
        "final_k": 8,
        "confidence": "high",
        "confidence_reason": "rerank score above the fitted threshold",
        "model": "claude-opus-5",
        "prompt_version": 1,
        "response_schema_version": 1,
        "pinakes_version": "0.24.0",
        "now": "20260812 04:43",
    }
    fields.update(overrides)
    return transcript.record(**fields)  # pyright: ignore[reportArgumentType]


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    return tmp_path / ".pinakes"


# ---------------------------------------------------------------------------------------------
# The file
# ---------------------------------------------------------------------------------------------


def test_a_transcript_lands_under_its_own_operation_id_and_reads_back(state_dir: Path) -> None:
    """The name is the join key: `pnk budget` groups the ledger by `operation_id`, so a reader
    holding a row can open the file that explains it without searching for it."""
    written = transcript.write(state_dir, _record())

    assert written == state_dir / "deep" / f"{OPERATION_ID}.json"
    body = json.loads(written.read_text(encoding="utf-8"))
    assert body["operation_id"] == OPERATION_ID
    assert body["question"] == "what does sourdough need?"
    assert body["answer"]["call_ids"] == ["CALL0"]


def test_the_envelope_records_what_the_run_was_asked_not_only_what_it_answered(
    state_dir: Path,
) -> None:
    """The ledger stores no query text (INVARIANTS), which is the whole reason this file exists —
    so the things that decide what a run *costs* are all recorded beside the prose it produced."""
    body = json.loads(transcript.write(state_dir, _record()).read_text(encoding="utf-8"))

    assert body["schema"] == transcript.SCHEMA_VERSION
    assert body["question"] == "what does sourdough need?"
    assert body["filters"]["tags"] == ["baking"]
    assert body["filters"]["modified_after"] == "20260101", "the typed form, not an epoch float"
    assert body["final_k"] == 8
    # Why this run took the branch it took: D-28 gives the branch to the free signal, so a
    # transcript naming the branch but not the reading behind it cannot explain its own price.
    assert body["confidence"] == "high"
    assert body["confidence_reason"] == "rerank score above the fitted threshold"
    # What a run produced depends on what it was asked, in the wording it was asked it.
    assert body["prompt_version"] == 1
    assert body["response_schema_version"] == 1
    assert body["model"] == "claude-opus-5"
    assert body["written_at"] == "20260812 04:43"
    # Which build wrote it: a prompt version says what was asked, and this says what asked it.
    assert body["pinakes_version"] == "0.24.0"


def test_money_is_a_string_of_cents_never_a_float(state_dir: Path) -> None:
    """JSON has no decimal type, and a float would reintroduce exactly the representation error
    `Decimal` exists to avoid (INVARIANTS). Asserted on the *parsed* value, because a float in the
    file parses back as a float and would pass any check made on the dict before writing."""
    body = json.loads(transcript.write(state_dir, _record()).read_text(encoding="utf-8"))

    assert body["answer"]["spent_eur"] == "0.26"
    assert body["answer"]["estimated_eur"] == "0.26"
    assert isinstance(body["answer"]["spent_eur"], str)
    assert isinstance(body["answer"]["estimated_eur"], str)


# One renderer, two consumers: that the object stored here is the object `--json` prints is
# asserted where both can be produced by one run —
# `test_cli_ask.py::test_the_transcripts_answer_object_is_what_json_printed`. Comparing the two
# functions directly would only restate that one calls the other.


@pytest.mark.parametrize("bad", ["..", "../../etc/passwd", "", "not-a-ulid", OPERATION_ID.lower()])
def test_a_transcript_cannot_be_filed_under_anything_but_a_ulid(state_dir: Path, bad: str) -> None:
    """`Accountant` mints the id, so in production it always is one — but it is also a *parameter*,
    and the one thing a caller-supplied path component must never do is name a directory above this
    one. Lowercase is refused with the rest: `ids` rejects rather than normalises it."""
    with pytest.raises(ValueError, match="not a ULID"):
        transcript.transcript_path(state_dir, bad)
    with pytest.raises(ValueError, match="not a ULID"):
        transcript.write(state_dir, _record(operation_id=bad))
    assert not (state_dir / "deep").exists(), "nothing was created on the way to refusing"


def test_a_body_with_no_operation_id_is_refused_rather_than_filed_somewhere(
    state_dir: Path,
) -> None:
    """The filename comes out of the body, so a body that cannot name itself has no home."""
    with pytest.raises(ValueError, match="no `operation_id`"):
        transcript.write(state_dir, {"schema": 1})


def test_a_half_written_transcript_is_never_counted_as_a_finished_one(
    state_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The temp file is `.tmp`, not `.json`, because `Path.glob("*.json")` matches dot-files — so a
    leftover from an uncatchable kill (SIGKILL, OOM, power loss; `except BaseException` cleans up
    everything else) would otherwise be counted and cleared as a real record. `extract/cache.py`
    carries the same trap and the same note.

    **Asserted on the name the writer actually asks for**, not on a leftover the test invented: a
    planted `.tmp` file proves only that the glob ignores `.tmp` files, and would keep passing if
    the writer started suffixing its temporaries `.json`.
    """
    seen: list[str] = []
    real = os.replace

    def spy(src: str, dst: str) -> None:
        """`os.replace` is handed the temp name — which is precisely the file a kill one
        instruction earlier would have left on disk."""
        seen.append(str(src))
        real(src, dst)

    monkeypatch.setattr(os, "replace", spy)
    transcript.write(state_dir, _record())

    leftover = Path(seen[0])
    assert leftover.suffix != FILE_SUFFIX, "a killed write would leave this behind"
    # And the consequence, with the writer's own name rather than an invented one.
    leftover.write_text("{", encoding="utf-8")
    assert len(transcript.paths(state_dir)) == 1
    assert transcript.stats(state_dir)[0] == 1


def test_call_ids_are_gathered_across_transcripts_and_survive_an_unreadable_one(
    state_dir: Path,
) -> None:
    """What prices them for the confirmation prompt. A file that cannot be read contributes
    nothing — it is also the file whose loss tells a reader least, so under-counting is the safe
    direction here."""
    transcript.write(state_dir, _record(calls=2))
    other = "01K2ZQZQZQZQZQZQZQZQZQZQZR"
    transcript.write(state_dir, _record(operation_id=other))
    (state_dir / "deep" / "01K2ZQZQZQZQZQZQZQZQZQZQZS.json").write_text("{ oh no", encoding="utf-8")

    assert transcript.call_ids(state_dir) == {"CALL0", "CALL1"}


def test_call_ids_and_stats_on_a_kb_that_never_ran_one_are_empty(state_dir: Path) -> None:
    assert transcript.paths(state_dir) == ()
    assert transcript.stats(state_dir) == (0, 0)
    assert transcript.call_ids(state_dir) == set()


def test_clear_all_removes_every_transcript_and_reports_what_went(state_dir: Path) -> None:
    first = transcript.write(state_dir, _record())
    second = transcript.write(state_dir, _record(operation_id="01K2ZQZQZQZQZQZQZQZQZQZQZR"))
    expected_bytes = first.stat().st_size + second.stat().st_size

    assert transcript.clear_all(state_dir) == (2, expected_bytes)
    assert transcript.paths(state_dir) == ()


# ---------------------------------------------------------------------------------------------
# The protection — what removes it, and what must not
# ---------------------------------------------------------------------------------------------


@pytest.fixture
def kb_with_a_transcript(tmp_path: Path) -> Path:
    """A real KB with one transcript and one free cache entry, so a run that clears either can be
    seen not to have cleared the other."""
    from pinakes.extract import ExtractedText
    from pinakes.extract import cache as extract_cache

    root = init(tmp_path / "kb", now="20260812 04:43").root
    transcript.write(root / ".pinakes", _record())
    extract_cache.get_or_extract(
        root / ".pinakes" / "cache" / "extract",
        content_hash="sha256:abc",
        backend="pypdfium2",
        fingerprint="fp1",
        extract=lambda: ExtractedText(
            text="page one", page_spans=((0, 8),), per_page_provenance=({},)
        ),
    )
    return root


def _transcripts(root: Path) -> int:
    return len(transcript.paths(root / ".pinakes"))


def _cache_entries(root: Path) -> int:
    from pinakes.extract import cache as extract_cache

    return extract_cache.total_stats(root / ".pinakes" / "cache" / "extract")[0]


def test_a_sync_sweeps_orphaned_cache_entries_and_leaves_the_transcript(
    kb_with_a_transcript: Path,
) -> None:
    """The sweep is keyed on extraction entries and globs `cache/extract/*.json`; a transcript is
    not in that directory and never was. Asserted rather than assumed, because "spared by the
    sweep" is the property D-26 bought by putting it outside `cache/` — and a later increment that
    moved it inside would break the protection while every test about its *contents* still passed.
    """
    assert _cache_entries(kb_with_a_transcript) == 1
    report = sync(load(kb_with_a_transcript), options=SyncOptions(), now="20260812 04:44")

    assert report.ok
    assert _cache_entries(kb_with_a_transcript) == 0, "the orphan sweep did its own job"
    assert _transcripts(kb_with_a_transcript) == 1


def test_a_rebuild_leaves_the_transcript_alone(kb_with_a_transcript: Path) -> None:
    """`--rebuild` swaps a freshly built index over the old one and clears nothing else."""
    sync(load(kb_with_a_transcript), options=SyncOptions(rebuild=True), now="20260812 04:44")

    assert _transcripts(kb_with_a_transcript) == 1


@pytest.mark.parametrize("paid", [False, True])
def test_clearing_the_extraction_cache_never_touches_a_transcript(
    kb_with_a_transcript: Path, paid: bool
) -> None:
    """Bare `--clear-cache` and `--clear-cache=paid` both empty the *extraction cache*, whole. The
    transcript is a second protected store, and neither spelling names it."""
    report = sync(
        load(kb_with_a_transcript),
        options=SyncOptions(clear_cache=True, clear_cache_paid=paid, yes=True),
    )

    assert report.cache_cleared == 1
    assert _cache_entries(kb_with_a_transcript) == 0
    assert _transcripts(kb_with_a_transcript) == 1


def test_clearing_transcripts_never_touches_the_extraction_cache(
    kb_with_a_transcript: Path,
) -> None:
    """And the other direction, which is the one that would cost money to get wrong."""
    report = sync(
        load(kb_with_a_transcript),
        options=SyncOptions(clear_cache=True, clear_cache_transcripts=True, yes=True),
    )

    assert report.cache_clear_target == CLEAR_TRANSCRIPTS
    assert report.cache_cleared == 1
    assert _transcripts(kb_with_a_transcript) == 0
    assert _cache_entries(kb_with_a_transcript) == 1


def test_clearing_transcripts_without_a_yes_asks_first_and_removes_nothing(
    kb_with_a_transcript: Path,
) -> None:
    report = sync(
        load(kb_with_a_transcript),
        options=SyncOptions(clear_cache=True, clear_cache_transcripts=True),
    )

    assert report.cache_clear_aborted
    assert report.cache_clear_target == CLEAR_TRANSCRIPTS
    assert report.cache_pending_entries == 1
    assert _transcripts(kb_with_a_transcript) == 1


def test_clearing_transcripts_on_a_kb_that_has_none_is_a_no_op_not_a_prompt(tmp_path: Path) -> None:
    root = init(tmp_path / "kb", now="20260812 04:43").root
    report = sync(load(root), options=SyncOptions(clear_cache=True, clear_cache_transcripts=True))

    assert report.cache_cleared == 0
    assert not report.cache_clear_aborted


# ---------------------------------------------------------------------------------------------
# ... through the command line, where the flag's spelling is real
# ---------------------------------------------------------------------------------------------


def test_the_cli_target_removes_the_transcripts_and_says_so(
    kb_with_a_transcript: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = ["sync", "--kb", str(kb_with_a_transcript), "--clear-cache=transcripts", "--yes"]
    assert main(argv) == 0
    out = capsys.readouterr().out

    assert "removed 1 transcripts" in out
    assert _transcripts(kb_with_a_transcript) == 0
    assert _cache_entries(kb_with_a_transcript) == 1


def test_the_cli_refuses_unattended_without_a_yes_and_names_the_flags_that_would_work(
    kb_with_a_transcript: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No terminal and no `--yes` is the cron case: it must refuse, and the remedy it prints must
    be the one for the store it was asked about — `--clear-cache=paid` would be about the other."""
    argv = ["sync", "--kb", str(kb_with_a_transcript), "--clear-cache=transcripts"]
    assert main(argv) == 1
    captured = capsys.readouterr()

    assert "this will remove 1 transcripts" in captured.out
    assert "they are the record of 1 paid run(s)" in captured.out
    # The count leads: the euro figure is a join against the ledger, and a join resolving
    # nothing would otherwise open the warning with "€0.0000".
    assert "Nothing re-creates them" in captured.out
    assert "re-run with --yes --clear-cache=transcripts" in captured.err
    assert _transcripts(kb_with_a_transcript) == 1


def test_an_unknown_clear_cache_value_is_a_usage_error(kb_with_a_transcript: Path) -> None:
    """`choices` is the guard: a typo must not fall through to clearing the extraction cache."""
    with pytest.raises(SystemExit) as exit_info:
        main(["sync", "--kb", str(kb_with_a_transcript), "--clear-cache=transcript"])

    assert exit_info.value.code == 2
    assert _transcripts(kb_with_a_transcript) == 1
    assert _cache_entries(kb_with_a_transcript) == 1


@pytest.fixture
def at_a_terminal(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    """Pretend a terminal is attached and answer its one question.

    The confirm-then-re-call path has no coverage at all otherwise — `sys.stdin.isatty()` is
    `False` under pytest, so every existing `--clear-cache` test takes the `--yes` route past it.
    It is also the destructive path a person actually walks.
    """

    def _answering(reply: str) -> None:
        def _input(prompt: str = "") -> str:
            assert "proceed?" in prompt, "the reply is to the confirmation, not to anything else"
            return reply

        monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
        monkeypatch.setattr("builtins.input", _input)

    return _answering


def test_a_confirmed_prompt_removes_the_transcripts_and_nothing_else(
    kb_with_a_transcript: Path,
    at_a_terminal: Callable[[str], None],
    capsys: pytest.CaptureFixture[str],
) -> None:
    at_a_terminal("y")
    assert main(["sync", "--kb", str(kb_with_a_transcript), "--clear-cache=transcripts"]) == 0
    out = capsys.readouterr().out

    assert "removed 1 transcripts" in out
    assert _transcripts(kb_with_a_transcript) == 0
    # The re-call after `y` carries the target the prompt described, not the other one.
    assert _cache_entries(kb_with_a_transcript) == 1


def test_declining_the_prompt_removes_nothing(
    kb_with_a_transcript: Path,
    at_a_terminal: Callable[[str], None],
    capsys: pytest.CaptureFixture[str],
) -> None:
    at_a_terminal("n")
    assert main(["sync", "--kb", str(kb_with_a_transcript), "--clear-cache=transcripts"]) == 0

    assert "aborted; nothing removed." in capsys.readouterr().out
    assert _transcripts(kb_with_a_transcript) == 1
    assert _cache_entries(kb_with_a_transcript) == 1


def test_a_confirmed_cache_clear_still_leaves_the_transcript(
    kb_with_a_transcript: Path,
    at_a_terminal: Callable[[str], None],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The same walk on the other store: answering `y` to the cache prompt authorises the cache,
    including its paid entries — and reaches nothing under `.pinakes/deep/`."""
    at_a_terminal("y")
    assert main(["sync", "--kb", str(kb_with_a_transcript), "--clear-cache"]) == 0

    assert "removed 1 entries" in capsys.readouterr().out
    assert _cache_entries(kb_with_a_transcript) == 0
    assert _transcripts(kb_with_a_transcript) == 1
