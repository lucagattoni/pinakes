"""`tools/agent_spend.py` reassembles requests correctly, or every number it prints is fiction.

Two properties of the transcript format silently corrupt a naive sum, and both were got wrong on
the first pass at this data. They are pinned here rather than left to a comment, because the
failure mode of getting either wrong is a plausible number with no symptom: spend inflated 2.14x
by counting lines, or output undercounted 1.7755x by trusting the first line of a request.

Everything below builds its own transcripts. Nothing reads `~/.claude`, so these tests say the same
thing on a machine that has never run an agent.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO = Path(__file__).resolve().parent.parent


def _load_tool() -> ModuleType:
    """Import `tools/agent_spend.py` by path — `tools/` is not a package."""
    spec = importlib.util.spec_from_file_location("agent_spend", REPO / "tools" / "agent_spend.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_spend"] = module
    spec.loader.exec_module(module)
    return module


agent_spend = _load_tool()


def _line(
    request_id: str,
    *,
    output: int,
    model: str = "claude-opus-5",
    input_tokens: int = 3,
    write: int = 0,
    read: int = 1_000,
    timestamp: str = "2026-08-31T21:00:00.000Z",
) -> str:
    record: dict[str, Any] = {
        "type": "assistant",
        "requestId": request_id,
        "timestamp": timestamp,
        "message": {
            "model": model,
            "usage": {
                "input_tokens": input_tokens,
                "cache_creation_input_tokens": write,
                "cache_read_input_tokens": read,
                "output_tokens": output,
            },
        },
    }
    return json.dumps(record)


def _write(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_one_response_written_as_several_lines_counts_once(tmp_path: Path) -> None:
    """Every line of one response repeats the same `requestId` and an identical `usage` block.

    Counting lines inflated a real corpus's spend 2.14x. Revert the `requestId` keying in
    `read_requests` and this goes to three.
    """
    transcript = _write(
        tmp_path / "session.jsonl",
        [_line("req_a", output=10), _line("req_a", output=20), _line("req_a", output=30)],
    )
    requests = agent_spend.read_requests(transcript)
    assert len(requests) == 1, "three lines of one response must reassemble into one request"
    assert requests[0].cache_read_tokens == 1_000, "cache fields must not be summed across lines"


def test_output_tokens_is_a_running_partial_so_the_max_is_the_answer(tmp_path: Path) -> None:
    """Taking the first line's `output_tokens` undercounts output by 1.7755x on the real corpus."""
    transcript = _write(
        tmp_path / "session.jsonl",
        [_line("req_a", output=10), _line("req_a", output=20), _line("req_a", output=30)],
    )
    (request,) = agent_spend.read_requests(transcript)
    assert request.output_tokens == 30, "the last (largest) value is the request's real output"


def test_a_line_without_a_request_id_falls_back_to_its_uuid(tmp_path: Path) -> None:
    """About 0.2% of lines carry no `requestId`. Dropping them loses real spend."""
    record: dict[str, Any] = {
        "type": "assistant",
        "uuid": "u-1",
        "message": {"model": "claude-opus-5", "usage": {"output_tokens": 7}},
    }
    transcript = _write(tmp_path / "session.jsonl", [json.dumps(record)])
    (request,) = agent_spend.read_requests(transcript)
    assert request.request_id == "u-1"
    assert request.output_tokens == 7


def test_lines_that_are_not_requests_are_skipped_without_raising(tmp_path: Path) -> None:
    """Transcripts hold user turns, malformed lines and JSON that is not an object."""
    transcript = _write(
        tmp_path / "session.jsonl",
        [
            '{"type":"user","message":{"content":"hello"}}',
            "not json at all",
            "[1, 2, 3]",
            _line("req_a", output=5),
        ],
    )
    assert len(agent_spend.read_requests(transcript)) == 1


def test_fable_bills_at_exactly_twice_opus_on_both_input_and_output() -> None:
    """The ratio a fan-out's model choice turns on. Both directions, not just output."""
    fable_in, fable_out = agent_spend.RATES_USD_PER_MTOK["claude-fable-5"]
    opus_in, opus_out = agent_spend.RATES_USD_PER_MTOK["claude-opus-5"]
    assert fable_in == pytest.approx(2.0 * opus_in)
    assert fable_out == pytest.approx(2.0 * opus_out)


def test_a_model_off_the_rate_card_reports_no_dollars_rather_than_a_guess() -> None:
    """A guessed price is worse than a stated gap — it is a number nobody knows is invented."""
    request = agent_spend.Request(
        request_id="r",
        model="claude-not-a-real-model",
        input_tokens=1_000,
        cache_write_tokens=0,
        cache_read_tokens=0,
        output_tokens=1_000,
        timestamp=None,
        is_sidechain=False,
    )
    assert request.usd is None
    assert request.units > 0, "units are model-independent and must still be reported"


def test_a_full_cache_rewrite_is_only_counted_above_the_context_floor() -> None:
    """Early in a session almost everything is a cache write, which says nothing about waste."""
    small = agent_spend.Request(
        request_id="r",
        model="claude-opus-5",
        input_tokens=0,
        cache_write_tokens=1_000,
        cache_read_tokens=0,
        output_tokens=0,
        timestamp=None,
        is_sidechain=False,
    )
    assert not small.is_full_rewrite, "a 1k-token context is a session booting, not a re-write"

    large = agent_spend.Request(
        request_id="r",
        model="claude-opus-5",
        input_tokens=0,
        cache_write_tokens=80_000,
        cache_read_tokens=1_000,
        output_tokens=0,
        timestamp=None,
        is_sidechain=False,
    )
    assert large.is_full_rewrite, "80k written against an 81k context is a full re-write"


def test_idle_gaps_land_in_the_bucket_that_names_their_cause() -> None:
    """The split that matters is inside vs. outside the cache TTL — expiry vs. a prefix change."""
    assert agent_spend._bucket(6.6) == "<1 min"
    assert agent_spend._bucket(240.0) == "1-5 min"
    assert agent_spend._bucket(1_800.0) == "5-60 min"
    assert agent_spend._bucket(7_200.0) == "1-6 h"
    assert agent_spend._bucket(90_000.0) == ">6 h"


def test_a_started_row_with_no_outcome_is_reported_as_such(tmp_path: Path) -> None:
    """`result` and `failed` overwrite `started`; nothing else does. A run recording no outcome is
    what makes a workflow resume re-run it — it is not evidence the agent died."""
    run = tmp_path / "proj" / "session" / "subagents" / "workflows" / "wf_test"
    run.mkdir(parents=True)
    _write(
        run / "journal.jsonl",
        [
            json.dumps({"type": "started", "agentId": "a1"}),
            json.dumps({"type": "started", "agentId": "a2"}),
            json.dumps({"type": "started", "agentId": "a3"}),
            json.dumps({"type": "result", "agentId": "a1", "result": {}}),
            json.dumps({"type": "failed", "agentId": "a2"}),
        ],
    )
    outcomes = agent_spend.journal_outcomes(tmp_path, None)
    assert set(outcomes) == {"wf_test"}
    assert outcomes["wf_test"].agents == {
        "a1": "result",
        "a2": "failed",
        "a3": "no-terminal-row",
    }
    assert outcomes["wf_test"].orphans == 1, "only the agent with no terminal row is an orphan"


def test_the_project_filter_selects_by_directory_name(tmp_path: Path) -> None:
    """`--project Pinakes` must not also pick up a neighbouring project's sessions."""
    for name in ("-Users-someone-Pinakes", "-Users-someone-other"):
        directory = tmp_path / name
        directory.mkdir()
        _write(directory / "s.jsonl", [_line("req_a", output=1)])
    matched = agent_spend.find_transcripts(tmp_path, "Pinakes", include_subagents=False)
    assert [path.parent.name for path in matched] == ["-Users-someone-Pinakes"]
    assert len(agent_spend.find_transcripts(tmp_path, None, include_subagents=False)) == 2


def test_a_missing_root_returns_nothing_rather_than_raising(tmp_path: Path) -> None:
    """The tool runs on machines that have never run an agent; that is an empty answer, not a
    crash."""
    assert agent_spend.find_transcripts(tmp_path / "absent", None, include_subagents=False) == []
    assert agent_spend.journal_outcomes(tmp_path / "absent", None) == {}
