"""`tools/hooks/review_stop_hook.py`, driven as a Stop hook is: a payload in, a decision out.

Every test builds a **synthetic session** of the true layout — `<slug>/<session>.jsonl` beside
`<slug>/<session>/subagents/workflows/wf_*/journal.jsonl` — because a hook that is only ever handed
a `--journal` would never reach the path from `transcript_path` to a run, and that path is the whole
of what the hook adds to the gate (`tests/test_review_pass_gate.py` learned this once: discovery was
a level short and every test still passed). Runs are given an old modification time unless a test
says otherwise, because the gate treats a run written to in the last 180 seconds as possibly alive.

**The defects these tests exist to catch** are the ones that look like working:

- a hook that **blocks and cannot be satisfied** (the acknowledgement does not stop it), which the
  Stop-hook documentation warns about and which would trap a turn for eight rounds;
- a hook that **reads a dead run as a live one** or the reverse — the gate's quiet window against
  the payload's `background_tasks` — and so either blocks a healthy review in flight or passes a
  fan-out that was killed seconds ago;
- a hook that **fails open without a word**: a crash, a bad payload or a gate that exits `1`
  without its verdict must be visible on stderr, and must not be read as a failed review;
- a hook that never starts on the interpreter the hook environment finds — on this machine the
  Xcode 3.9 — which is a non-blocking error nobody reads.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "tools" / "hooks" / "review_stop_hook.py"
GATE = ROOT / "tools" / "review_pass_gate.py"
SETTINGS = ROOT / ".claude" / "settings.json"

SESSION = "7b1c2d3e-0000-4000-8000-aaaaaaaaaaaa"


def started(key: str, agent_id: str) -> dict[str, object]:
    return {"type": "started", "key": key, "agentId": agent_id}


def returned(key: str, agent_id: str, payload: object = "found a defect") -> dict[str, object]:
    return {"type": "result", "key": key, "agentId": agent_id, "result": payload}


def write_run(projects: Path, name: str, *events: dict[str, object], live: bool = False) -> Path:
    """One workflow run in the true layout; quiet for an hour unless `live`."""
    directory = projects / "-some-project" / SESSION / "subagents" / "workflows" / name
    directory.mkdir(parents=True, exist_ok=True)
    journal = directory / "journal.jsonl"
    journal.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    if not live:
        old = time.time() - 3600
        os.utime(journal, (old, old))
    return directory


def payload(projects: Path, **extra: object) -> dict[str, object]:
    transcript = projects / "-some-project" / f"{SESSION}.jsonl"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text("{}\n")
    return {
        "session_id": SESSION,
        "transcript_path": str(transcript),
        "cwd": str(projects),
        "hook_event_name": "Stop",
        "stop_hook_active": False,
        "last_assistant_message": "done",
        "background_tasks": [],
        "session_crons": [],
        **extra,
    }


def hook(
    stdin: object, *args: str, python: str = sys.executable, tool: Path = HOOK
) -> subprocess.CompletedProcess[str]:
    text = stdin if isinstance(stdin, str) else json.dumps(stdin)
    return subprocess.run(
        [python, str(tool), *args], input=text, capture_output=True, text=True, check=False
    )


def blocked(done: subprocess.CompletedProcess[str]) -> str:
    """The reason, asserting the hook blocked and did so the documented way."""
    assert done.returncode == 0, done.stderr
    body = json.loads(done.stdout)
    assert body["decision"] == "block"
    assert isinstance(body["reason"], str)
    return body["reason"]


def silent(done: subprocess.CompletedProcess[str]) -> None:
    """Exit 0 with nothing on stdout is how a Stop hook lets the turn end."""
    assert done.returncode == 0, done.stderr
    assert done.stdout == ""


def three_agents_one_dead(projects: Path, name: str = "wf_aaaa-111") -> Path:
    return write_run(
        projects,
        name,
        started("k1", "a1"),
        started("k2", "a2"),
        started("k3", "dead3"),
        returned("k1", "a1"),
        returned("k2", "a2", {"findings": [{"id": "F1"}]}),
    )


def test_a_session_with_no_workflow_is_silent(tmp_path: Path) -> None:
    """The ordinary turn: nothing to look at, nothing printed, and no gate run at all."""
    silent(hook(payload(tmp_path)))


def test_a_payload_without_a_transcript_path_is_silent(tmp_path: Path) -> None:
    """Nothing to locate is not a failure — and not a block."""
    body = payload(tmp_path)
    del body["transcript_path"]
    silent(hook(body))


def test_a_complete_run_does_not_block(tmp_path: Path) -> None:
    write_run(
        tmp_path,
        "wf_good-000",
        started("k1", "a1"),
        returned("k1", "a1"),
    )
    silent(hook(payload(tmp_path)))


def test_a_run_that_lost_an_agent_blocks_and_names_it(tmp_path: Path) -> None:
    """The case the hook is for: one of three agents never returned, and the reason says which."""
    three_agents_one_dead(tmp_path)
    reason = blocked(hook(payload(tmp_path)))
    assert "wf_aaaa-111" in reason
    assert "PARTIAL" in reason
    assert "dead3" in reason
    assert "3 agents launched, 2 returned, 1 died" in reason


def test_a_run_where_nobody_returned_is_vacuous(tmp_path: Path) -> None:
    """`VACUOUS` is a different outcome from `PARTIAL`, not a smaller one: nobody looked."""
    write_run(tmp_path, "wf_none-222", started("k1", "d1"), started("k2", "d2"))
    reason = blocked(hook(payload(tmp_path)))
    assert "VACUOUS" in reason
    assert "PARTIAL" not in reason


def test_an_agent_that_returned_nothing_counts_as_a_failure(tmp_path: Path) -> None:
    """The quiet death: completed, empty, and replayed from cache as a clean pass."""
    write_run(
        tmp_path,
        "wf_empty-333",
        started("k1", "a1"),
        started("k2", "e2"),
        returned("k1", "a1"),
        returned("k2", "e2", {"findings": []}),
    )
    reason = blocked(hook(payload(tmp_path)))
    assert "PARTIAL" in reason
    assert "returned nothing: e2" in reason


def test_a_run_whose_every_agent_returned_nothing_is_vacuous(tmp_path: Path) -> None:
    """All of them returned and none said anything: nobody looked, whatever the journal counts."""
    write_run(
        tmp_path,
        "wf_hollow-444",
        started("k1", "e1"),
        returned("k1", "e1", ""),
    )
    assert "VACUOUS" in blocked(hook(payload(tmp_path)))


def test_the_reason_says_this_is_not_the_workflows_coverage(tmp_path: Path) -> None:
    """Two different questions: did every agent return, and was the review complete."""
    three_agents_one_dead(tmp_path)
    reason = blocked(hook(payload(tmp_path)))
    assert "not the review's own `coverage`" in reason
    assert "`resumeFromRunId`" in reason


def test_the_reason_carries_a_command_that_acknowledges(tmp_path: Path) -> None:
    run = three_agents_one_dead(tmp_path)
    reason = blocked(hook(payload(tmp_path)))
    assert f"--acknowledge {run}" in reason
    assert "--told" in reason
    assert str(HOOK) in reason


def test_acknowledging_stops_the_block(tmp_path: Path) -> None:
    """Blocking that cannot be satisfied is the documented trap; one command must end it."""
    run = three_agents_one_dead(tmp_path)
    assert blocked(hook(payload(tmp_path)))
    done = hook("", "--acknowledge", str(run), "--told", "told the user one lens died")
    assert done.returncode == 0, done.stderr
    assert (run / "gate-acknowledged.json").is_file()
    silent(hook(payload(tmp_path)))


def test_the_acknowledgement_records_what_was_told_and_the_verdict(tmp_path: Path) -> None:
    run = three_agents_one_dead(tmp_path)
    hook("", "--acknowledge", str(run), "--told", "  one lens died  ")
    record = json.loads((run / "gate-acknowledged.json").read_text())
    assert record["told"] == "one lens died"
    assert record["verdict"] == {"launched": 3, "returned": 2, "empty": 0}
    assert record["run"] == "wf_aaaa-111"
    assert record["label"] == "PARTIAL"


def test_the_acknowledgement_counts_an_empty_result_in_the_shape_it_covers(
    tmp_path: Path,
) -> None:
    """A run that goes from "one died" to "one died and one came back empty" is a new verdict."""
    run = write_run(
        tmp_path,
        "wf_mixed-666",
        started("k1", "a1"),
        started("k2", "e2"),
        started("k3", "dead3"),
        returned("k1", "a1"),
        returned("k2", "e2", []),
    )
    hook("", "--acknowledge", str(run), "--told", "one died, one was empty")
    record = json.loads((run / "gate-acknowledged.json").read_text())
    assert record["verdict"] == {"launched": 3, "returned": 2, "empty": 1}
    silent(hook(payload(tmp_path)))


def test_a_run_the_hook_blocks_can_be_acknowledged_at_once(tmp_path: Path) -> None:
    """The documented trap is a block that cannot be satisfied. A fan-out killed seconds ago is
    blocked (nothing is in flight), so acknowledging it must work inside the gate's quiet window
    too, or the session is stuck for eight rounds."""
    run = write_run(tmp_path, "wf_fresh-555", started("k1", "d1"), live=True)
    assert blocked(hook(payload(tmp_path)))
    done = hook("", "--acknowledge", str(run), "--told", "the review died, told the user")
    assert done.returncode == 0, done.stderr
    silent(hook(payload(tmp_path)))


def test_an_empty_told_is_refused_and_writes_nothing(tmp_path: Path) -> None:
    """An acknowledgement that says nothing was said is not one."""
    run = three_agents_one_dead(tmp_path)
    for told in ("", "   "):
        done = hook("", "--acknowledge", str(run), "--told", told)
        assert done.returncode == 1
        assert "--told is empty" in done.stderr
    assert not (run / "gate-acknowledged.json").exists()
    assert blocked(hook(payload(tmp_path)))


def test_an_acknowledgement_does_not_cover_a_run_that_changes_shape(tmp_path: Path) -> None:
    """A resumed run is a different verdict: telling the user about yesterday's is not today's."""
    run = three_agents_one_dead(tmp_path)
    hook("", "--acknowledge", str(run), "--told", "one died")
    silent(hook(payload(tmp_path)))
    with (run / "journal.jsonl").open("a") as handle:
        handle.write(json.dumps(started("k4", "dead4")) + "\n")
    old = time.time() - 3600
    os.utime(run / "journal.jsonl", (old, old))
    reason = blocked(hook(payload(tmp_path)))
    assert "dead4" in reason


def test_an_acknowledgement_for_one_run_does_not_cover_another(tmp_path: Path) -> None:
    first = three_agents_one_dead(tmp_path, "wf_first-001")
    three_agents_one_dead(tmp_path, "wf_second-002")
    hook("", "--acknowledge", str(first), "--told", "told")
    reason = blocked(hook(payload(tmp_path)))
    assert "wf_second-002" in reason
    assert "wf_first-001:" not in reason


def test_a_malformed_acknowledgement_does_not_silence_the_hook(tmp_path: Path) -> None:
    """Truncated, a list, no `told`, or a different verdict: none of them is an acknowledgement."""
    run = three_agents_one_dead(tmp_path)
    ack = run / "gate-acknowledged.json"
    good_verdict = {"launched": 3, "returned": 2, "empty": 0}
    for text in (
        "{",
        "[]",
        json.dumps({"verdict": good_verdict}),
        json.dumps({"verdict": good_verdict, "told": "  "}),
        json.dumps({"verdict": {"launched": 3, "returned": 3, "empty": 0}, "told": "x"}),
    ):
        ack.write_text(text)
        assert blocked(hook(payload(tmp_path))), text
    ack.write_text(json.dumps({"verdict": good_verdict, "told": "x"}))
    silent(hook(payload(tmp_path)))


def test_acknowledging_a_clean_run_writes_nothing(tmp_path: Path) -> None:
    run = write_run(tmp_path, "wf_good-000", started("k1", "a1"), returned("k1", "a1"))
    done = hook("", "--acknowledge", str(run), "--told", "all fine")
    assert done.returncode == 0, done.stderr
    assert "nothing to acknowledge" in done.stdout
    assert not (run / "gate-acknowledged.json").exists()


def test_acknowledging_something_that_is_not_a_run_is_refused(tmp_path: Path) -> None:
    done = hook("", "--acknowledge", str(tmp_path), "--told", "x")
    assert done.returncode == 1
    assert "not a workflow run" in done.stderr


def test_a_workflow_in_flight_is_never_judged(tmp_path: Path) -> None:
    """A slow agent and a dead one look the same in the journal; the payload says which it is.

    This run is quiet for an hour, so the gate alone would call its outstanding agent dead.
    """
    three_agents_one_dead(tmp_path)
    running = [{"id": "t1", "type": "workflow", "status": "running", "name": "adversarial-review"}]
    silent(hook(payload(tmp_path, background_tasks=running)))


def test_other_background_tasks_do_not_hide_a_dead_run(tmp_path: Path) -> None:
    """A dev server in the registry is not a workflow in flight."""
    three_agents_one_dead(tmp_path)
    shell = [{"id": "t1", "type": "shell", "status": "running", "command": "tail -f x"}]
    assert blocked(hook(payload(tmp_path, background_tasks=shell)))


def test_a_run_killed_seconds_ago_is_judged_when_nothing_is_in_flight(tmp_path: Path) -> None:
    """The gate's 180-second window would call this "probably still running" and pass it."""
    write_run(tmp_path, "wf_fresh-555", started("k1", "d1"), live=True)
    assert "VACUOUS" in blocked(hook(payload(tmp_path, background_tasks=[])))


def test_without_the_registry_the_gates_own_window_decides(tmp_path: Path) -> None:
    """No `background_tasks` is not "nothing running": a recent write means probably alive."""
    body = payload(tmp_path)
    del body["background_tasks"]
    write_run(tmp_path, "wf_fresh-555", started("k1", "d1"), live=True)
    silent(hook(body))
    stale = tmp_path / "-some-project" / SESSION / "subagents" / "workflows" / "wf_fresh-555"
    old = time.time() - 3600
    os.utime(stale / "journal.jsonl", (old, old))
    assert blocked(hook(body))


def test_stop_hook_active_still_blocks_and_says_again(tmp_path: Path) -> None:
    """The user chose block-until-acknowledged; the eight-round cap is the bound, not this flag."""
    three_agents_one_dead(tmp_path)
    reason = blocked(hook(payload(tmp_path, stop_hook_active=True)))
    assert "already stopped this turn once" in reason
    assert "already stopped" not in blocked(hook(payload(tmp_path, stop_hook_active=False)))


def test_only_the_ending_sessions_runs_are_judged(tmp_path: Path) -> None:
    """A dead run in another session is not this turn's business.

    The ending session has a run of its own, clean, so that the hook gets as far as looking: with
    no run directory at all it would return before it could read anyone else's.
    """
    write_run(tmp_path, "wf_good-000", started("k1", "a1"), returned("k1", "a1"))
    other = tmp_path / "-some-project" / "ffffffff-0000-4000-8000-bbbbbbbbbbbb"
    run = other / "subagents" / "workflows" / "wf_other-999"
    run.mkdir(parents=True)
    (run / "journal.jsonl").write_text(json.dumps(started("k1", "d1")) + "\n")
    old = time.time() - 3600
    os.utime(run / "journal.jsonl", (old, old))
    silent(hook(payload(tmp_path)))


def test_a_bad_payload_fails_loudly_and_does_not_block(tmp_path: Path) -> None:
    for text in ("", "not json", "[]", "null"):
        done = hook(text)
        assert done.returncode == 1, text
        assert done.stdout == ""
        assert "review_stop_hook:" in done.stderr
        assert "not a JSON object" in done.stderr


@pytest.mark.parametrize(
    "gate_source",
    [
        "raise SystemExit(1)\n",
        "import sys\nprint('{}')\nsys.exit(1)\n",
        "import sys\nprint('not json')\nsys.exit(1)\n",
        "raise RuntimeError('boom')\n",
        "import sys\nsys.exit(3)\n",
    ],
    ids=["exit1-silent", "exit1-empty-object", "exit1-not-json", "traceback", "exit3"],
)
def test_a_gate_that_crashes_is_not_a_failed_review(tmp_path: Path, gate_source: str) -> None:
    """`1` is what an uncaught traceback exits with too. Without a verdict it is a crash: visible
    on stderr, and never a block — a broken gate must not trap the turn, nor pass it quietly."""
    sandbox = tmp_path / "copy" / "tools"
    (sandbox / "hooks").mkdir(parents=True)
    shutil.copy(HOOK, sandbox / "hooks" / HOOK.name)
    (sandbox / "review_pass_gate.py").write_text(gate_source)
    projects = tmp_path / "projects"
    three_agents_one_dead(projects)
    done = hook(payload(projects), tool=sandbox / "hooks" / HOOK.name)
    assert done.returncode == 1
    assert done.stdout == ""
    assert "review_stop_hook:" in done.stderr
    assert "wf_aaaa-111" in done.stderr


def test_the_script_parses_as_python_3_9() -> None:
    """The hook environment's `python3` has been the Xcode 3.9; a script that does not parse there
    is a non-blocking error nobody reads."""
    ast.parse(HOOK.read_text(encoding="utf-8"), feature_version=(3, 9))


@pytest.mark.skipif(not Path("/usr/bin/python3").is_file(), reason="no system python3")
def test_it_runs_under_the_system_python3(tmp_path: Path) -> None:
    """Parsing is not running: `datetime.UTC` and `zip(strict=)` parse and fail on a 3.9 call.

    Here that interpreter is the Xcode 3.9; on a CI runner it is the distribution's. Either way it
    is a different one from the suite's, which is the point.
    """
    run = three_agents_one_dead(tmp_path)
    reason = blocked(hook(payload(tmp_path), python="/usr/bin/python3"))
    assert "PARTIAL" in reason
    done = hook("", "--acknowledge", str(run), "--told", "told", python="/usr/bin/python3")
    assert done.returncode == 0, done.stderr
    silent(hook(payload(tmp_path), python="/usr/bin/python3"))


def test_no_absolute_home_path_is_committed() -> None:
    """The repository is public: a path under a home directory names a person."""
    for path in (HOOK, SETTINGS):
        text = path.read_text(encoding="utf-8")
        for token in ("/Users/", "/home/"):
            assert token not in text, f"{path.name} contains {token}"


def settings_command() -> str:
    body = json.loads(SETTINGS.read_text(encoding="utf-8"))
    groups = body["hooks"]["Stop"]
    assert len(groups) == 1
    handlers = groups[0]["hooks"]
    assert len(handlers) == 1
    assert handlers[0]["type"] == "command"
    assert isinstance(handlers[0]["timeout"], int)
    return handlers[0]["command"]


def checkout(path: Path, with_hook: bool) -> Path:
    """A throwaway git checkout, with or without the hook and the gate it runs."""
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    if with_hook:
        (path / "tools" / "hooks").mkdir(parents=True)
        shutil.copy(HOOK, path / "tools" / "hooks" / HOOK.name)
        shutil.copy(GATE, path / "tools" / GATE.name)
    return path


def run_command(
    command: str, cwd: Path, stdin: object, **env: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        input=json.dumps(stdin),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **env},
    )


def test_settings_registers_the_hook_on_stop() -> None:
    """The wiring is the increment: a hook nothing calls is a file."""
    command = settings_command()
    assert "tools/hooks/review_stop_hook.py" in command


def test_the_command_runs_the_working_directorys_copy_not_the_project_dirs(
    tmp_path: Path,
) -> None:
    """`${CLAUDE_PROJECT_DIR}` stays at the original checkout inside a worktree, so a command built
    on it would run that checkout's copy. This one follows the directory the session is in."""
    worktree = checkout(tmp_path / "worktree", with_hook=True)
    primary = checkout(tmp_path / "primary", with_hook=False)
    projects = tmp_path / "projects"
    three_agents_one_dead(projects)
    done = run_command(
        settings_command(), worktree, payload(projects), CLAUDE_PROJECT_DIR=str(primary)
    )
    assert "PARTIAL" in blocked(done)


def test_a_checkout_without_the_hook_exits_zero_not_two(tmp_path: Path) -> None:
    """`python3` on a missing script exits 2, and exit 2 on a Stop hook is a block."""
    bare = checkout(tmp_path / "bare", with_hook=False)
    projects = tmp_path / "projects"
    three_agents_one_dead(projects)
    silent(run_command(settings_command(), bare, payload(projects)))


def test_a_directory_that_is_not_a_checkout_exits_zero(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    silent(run_command(settings_command(), elsewhere, payload(tmp_path)))


def test_the_settings_file_is_valid_and_is_the_only_hook_it_declares() -> None:
    body = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert set(body) == {"hooks"}
    assert set(body["hooks"]) == {"Stop"}
