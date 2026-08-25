"""`tools/review_pass_gate.py`, driven as a subprocess — one test per branch.

A subprocess rather than an import, for the reason `tests/test_status_header_gate.py` gives: it
exercises the same artifact a human runs, argument parsing included, with no `sys.path` surgery.
`--journal` exists so every branch reads a synthetic journal from `tmp_path` and no test ever
depends on a real fan-out having died.

**The defect these tests exist to catch is a gate that counts and never compares** — one that reads
the journal, prints a summary and exits `0` regardless. That would pass any test asserting only
"exit 0 on a good run", which is why every failing branch here asserts the *stated reason* as well
as the status, and why `test_the_gate_can_still_fail` exists at all: a gate that has never been
shown to fail is a claim, not a check.

**The second defect is subtler and cost this repo a real finding once**: treating "returned nothing"
as "found nothing". `test_a_present_but_falsy_result_is_not_empty` is the discriminating case — `0`
and `False` are answers, `[]` and `""` are silence, and a gate that conflates them either fails
every honest zero or passes every silent one.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

TOOL = Path(__file__).parent.parent / "tools" / "review_pass_gate.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False
    )


def journal(tmp_path: Path, *events: dict[str, object]) -> Path:
    path = tmp_path / "journal.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return path


def started(key: str, agent_id: str) -> dict[str, object]:
    return {"type": "started", "key": key, "agentId": agent_id}


def result(key: str, agent_id: str, payload: object) -> dict[str, object]:
    return {"type": "result", "key": key, "agentId": agent_id, "result": payload}


def test_a_complete_pass_is_green(tmp_path: Path) -> None:
    """Every agent started, returned, and returned content — the only case that earns exit 0."""
    path = journal(
        tmp_path,
        started("k1", "a1"),
        started("k2", "a2"),
        result("k1", "a1", "found a real defect in doctor.py"),
        result("k2", "a2", {"findings": [{"id": "F1"}]}),
    )
    out = run("--journal", str(path))
    assert out.returncode == 0, out.stdout + out.stderr
    assert "2 launched, 2 returned" in out.stdout
    assert "actually ran" in out.stdout


def test_the_gate_can_still_fail(tmp_path: Path) -> None:
    """The negative check, named so its absence is visible. A journal recording more `started` than
    `result` is the exact shape of the 20260825 pass that reported a clean bill with four of seven
    agents dead."""
    path = journal(
        tmp_path,
        started("k1", "a1"),
        started("k2", "a2"),
        started("k3", "a3"),
        result("k1", "a1", "a finding"),
    )
    out = run("--journal", str(path), "--assume-finished")
    assert out.returncode == 1
    assert "3 launched, 1 returned" in out.stdout
    assert "2 agent(s) DIED" in out.stdout
    assert "not a clean bill" in out.stdout


def test_a_dead_agent_is_named(tmp_path: Path) -> None:
    """Naming the dead agent is what makes the failure actionable — a count alone tells you the pass
    is invalid but not which lens to re-run."""
    path = journal(
        tmp_path, started("k1", "a1"), started("k2", "deadbeef"), result("k1", "a1", "x")
    )
    out = run("--journal", str(path), "--assume-finished")
    assert out.returncode == 1
    assert "deadbeef" in out.stdout
    assert "a1" not in out.stdout.split("DIED", 1)[1]


def test_an_empty_result_fails_even_though_the_agent_returned(tmp_path: Path) -> None:
    """The quiet failure: the agent completed, so nothing died, and it returned nothing. Resuming
    replays the empty result from cache, so this branch must say re-run rather than resume."""
    path = journal(
        tmp_path,
        started("k1", "a1"),
        started("k2", "a2"),
        result("k1", "a1", "a real finding"),
        result("k2", "a2", {"findings": [], "verdicts": []}),
    )
    out = run("--journal", str(path))
    assert out.returncode == 1
    assert "returned EMPTY" in out.stdout
    assert "re-run it instead" in out.stdout
    assert "DIED" not in out.stdout


def test_a_present_but_falsy_result_is_not_empty(tmp_path: Path) -> None:
    """The discriminating case. `0` and `False` are answers an agent can legitimately return; `[]`
    and `""` are silence. A gate that treats falsiness as emptiness fails every honest zero."""
    path = journal(
        tmp_path,
        started("k1", "a1"),
        started("k2", "a2"),
        result("k1", "a1", 0),
        result("k2", "a2", {"count": 0, "clean": False}),
    )
    out = run("--journal", str(path))
    assert out.returncode == 0, out.stdout
    assert "EMPTY" not in out.stdout


def test_emptiness_is_recognised_through_nesting(tmp_path: Path) -> None:
    """A schema result is a container of containers: `{"confirmed": [], "unverified": []}` is the
    literal shape the 20260825 fan-out returned, and a shallow check would call it content."""
    path = journal(
        tmp_path,
        started("k1", "a1"),
        result("k1", "a1", {"confirmed": [], "unverified": [], "notes": {"detail": ""}}),
    )
    out = run("--journal", str(path))
    assert out.returncode == 1
    assert "returned EMPTY" in out.stdout


def test_a_malformed_line_does_not_hide_a_death(tmp_path: Path) -> None:
    """A truncated journal is exactly the situation this gate is for — an agent killed mid-write.
    Refusing to parse it would hide the failure the gate exists to report."""
    path = tmp_path / "journal.jsonl"
    path.write_text(
        json.dumps(started("k1", "a1"))
        + "\n"
        + json.dumps(started("k2", "a2"))
        + "\n"
        + '{"type":"result","key":"k1","agen'
    )
    out = run("--journal", str(path), "--assume-finished")
    assert out.returncode == 1
    assert "2 launched, 0 returned" in out.stdout


def test_an_empty_journal_is_not_a_clean_bill(tmp_path: Path) -> None:
    """Nothing launched is a broken harness, and it must not share an exit status with a pass that
    ran. Exit 2 keeps 'the gate could not check' distinct from 'the gate checked and refused'."""
    path = tmp_path / "journal.jsonl"
    path.write_text("")
    out = run("--journal", str(path))
    assert out.returncode == 2
    assert "no agents" in out.stderr


def test_artifacts_are_split_by_whether_cleanup_destroys_them(tmp_path: Path) -> None:
    """58% of measured redirect targets are relative paths that `land.py --cleanup` destroys, so the
    two lists are not cosmetic: one tells you what to re-run, the other what to read *before* the
    worktree goes. A single merged list would bury the deadline."""
    path = journal(tmp_path, started("k1", "a1"), started("k2", "a2"), result("k1", "a1", "x"))
    transcript = tmp_path / "agent-a2.jsonl"
    transcript.write_text(
        "\n".join(
            json.dumps(
                {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}
                        ],
                    }
                }
            )
            for cmd in (
                "pytest -q > results.log 2>&1",
                "python3 probe.py > /tmp/probe-out.txt",
                "ruff check . > /dev/null",
            )
        )
    )
    out = run("--journal", str(path), "--transcript-dir", str(tmp_path), "--assume-finished")
    assert out.returncode == 1
    assert "EVIDENCE, NOT FINDINGS" in out.stdout
    assert "/tmp/probe-out.txt" in out.stdout
    assert "DESTROYED by worktree cleanup" in out.stdout
    assert "results.log" in out.stdout
    assert "/dev/null" not in out.stdout


def test_an_agent_that_left_nothing_says_so(tmp_path: Path) -> None:
    """13% of review agents leave nothing on disk. Silence there would read as 'no artifacts listed
    yet', which invites someone to go looking for files that were never written."""
    path = journal(tmp_path, started("k1", "a1"), started("k2", "a2"), result("k1", "a1", "x"))
    out = run("--journal", str(path), "--transcript-dir", str(tmp_path), "--assume-finished")
    assert out.returncode == 1
    assert "left nothing on disk" in out.stdout


def test_the_resume_hint_appears_only_when_an_agent_died(tmp_path: Path) -> None:
    """Resuming replays completed agents from cache, so it is the right remedy for a death and the
    wrong one for an empty result. Printing it in both places would recommend the no-op."""
    dead = journal(tmp_path, started("k1", "a1"), started("k2", "a2"), result("k1", "a1", "x"))
    out = run("--journal", str(dead), "--script", "/path/to/script.js", "--assume-finished")
    assert "resumeFromRunId" in out.stdout
    assert "/path/to/script.js" in out.stdout
    assert "same-session only" in out.stdout

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    only_empty = journal(empty_dir, started("k1", "a1"), result("k1", "a1", []))
    out = run("--journal", str(only_empty), "--assume-finished")
    assert out.returncode == 1
    assert "resumeFromRunId" not in out.stdout


def test_json_output_carries_the_verdict(tmp_path: Path) -> None:
    """`--json` is for a script that gates on the pass, so `pass_is_valid` must be false when
    exit status is non-zero — two representations of one verdict that must not disagree."""
    path = journal(tmp_path, started("k1", "a1"), started("k2", "a2"), result("k1", "a1", "x"))
    out = run("--journal", str(path), "--json", "--assume-finished")
    assert out.returncode == 1
    payload = json.loads(out.stdout)
    assert payload["launched"] == 2
    assert payload["returned"] == 1
    assert payload["pass_is_valid"] is False
    assert payload["dead"][0]["agent_id"] == "a2"


def test_a_running_fan_out_is_not_reported_as_dead(tmp_path: Path) -> None:
    """The regression that a real run found. A fan-out still in flight has outstanding agents and no
    "finished" marker, so it is byte-identical in the journal to one that was killed. Calling it
    is the worst failure available to this gate — a gate that cries wolf on a healthy run gets
    ignored, and then it is not a gate. Recent writes mean *cannot judge*, never *failed*."""
    path = journal(tmp_path, started("k1", "a1"), started("k2", "a2"), result("k1", "a1", "x"))
    out = run("--journal", str(path))
    assert out.returncode == 2
    assert "STILL RUNNING" in out.stderr
    assert "DIED" not in out.stdout


def test_a_quiet_fan_out_is_judged_without_the_override(tmp_path: Path) -> None:
    """The other side of the same branch, and the one that keeps the override honest: once the run
    has gone quiet the gate must judge it alone, or --assume-finished silently becomes mandatory
    and the check only ever runs when someone already suspects a death."""
    path = journal(tmp_path, started("k1", "a1"), started("k2", "a2"), result("k1", "a1", "x"))
    stale = time.time() - 3600
    os.utime(path, (stale, stale))
    out = run("--journal", str(path))
    assert out.returncode == 1
    assert "1 agent(s) DIED" in out.stdout
