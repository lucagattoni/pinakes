"""`tools/review_ledger.py`, driven as a subprocess against synthetic transcripts.

A subprocess rather than an import, for the reason `tests/test_review_pass_gate.py` gives: it
exercises the same artifact a human runs, argument parsing included. `--projects` points every test
at a `tmp_path` tree, so nothing here depends on what any real agent did on this machine.

**Four of these tests exist because the defect was in the tool when it was first run against the
real corpus, and every gate was green.**

- `test_a_package_path_keeps_its_directories` — normalisation anchored on the repository's *name*,
  so `src/pinakes/sync.py` reduced to `sync.py` and collided with every other `sync.py` on disk. The
  tool built to measure overlap between passes was over-reporting it.
- `test_a_killed_pass_is_not_a_pass_that_reported` — a rate-limited agent's last message is
  assistant text reading `You've hit your session limit`. It was quoted under *what each pass
  reported* for four consecutive passes: four deaths presented as four conclusions.
- `test_one_probe_run_in_two_scratch_directories_is_one_probe` — every reviewer builds its own
  `/tmp/p2-…` copy, so deduplication on the raw command found 880 "distinct" probes among 891.
- `test_reading_a_package_file_is_not_executing_the_project` — the verb `pinakes` is also the
  package directory, so `sed -n '1,10p' src/pinakes/pairing.py` classified as *executing* and the
  reading the ranking exists to demote sorted to the top of it.

None of the four changes an exit status, which is why none of them would have been caught by a test
asserting only that the tool runs. Three of them changed a published number.
"""

import json
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).parent.parent / "tools" / "review_ledger.py"

REVIEW_BRIEF = "You are adversarially reviewing increment 20260101_0000-x in the Pinakes repository."
BUILD_BRIEF = (
    "You are the implementing coder on Pinakes. Build increment 20260101_0000-x. "
    "Adversarially review your own work before landing it."
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False
    )


def _assistant(
    stamp: str, context: int, blocks: list[dict[str, object]] | None = None, **extra: object
) -> dict[str, object]:
    return {
        "type": "assistant",
        "timestamp": stamp,
        **extra,
        "message": {
            "role": "assistant",
            "usage": {"input_tokens": 0, "cache_read_input_tokens": context, "output_tokens": 0},
            "content": blocks if blocks is not None else [{"type": "thinking", "thinking": "..."}],
        },
    }


def _bash(identifier: str, command: str) -> dict[str, object]:
    return {"type": "tool_use", "id": identifier, "name": "Bash", "input": {"command": command}}


def _result(identifier: str, output: str) -> dict[str, object]:
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": identifier, "content": output}],
        },
    }


def transcript(
    projects: Path,
    name: str,
    brief: str,
    turns: list[dict[str, object]],
    workflow: str | None = None,
    stamp: str = "2026-01-01T00:00:00Z",
) -> Path:
    """Write one agent transcript where the tool looks for them."""
    directory = projects / "-slug" / "subagents"
    if workflow:
        directory = directory / "workflows" / workflow
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"agent-{name}.jsonl"
    records: list[dict[str, object]] = [
        {"type": "user", "timestamp": stamp, "message": {"content": brief}}
    ]
    records.extend(turns)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return path


def plain_pass(
    projects: Path,
    name: str,
    stamp: str,
    commands: list[str],
    report: str = "Found one issue: the cap is off by one.",
    brief: str = REVIEW_BRIEF,
    workflow: str | None = None,
    contexts: list[int] | None = None,
    killed: bool = False,
) -> Path:
    """A review pass that runs `commands`, then reports (or is killed before it can).

    Padded to eight assistant turns because a run shorter than five is below the cost of starting
    up and the tool declines to call it a pass.
    """
    sizes = contexts or [100, 200, 300, 400, 500, 600, 700, 800]
    turns: list[dict[str, object]] = []
    for index, size in enumerate(sizes):
        if index < len(commands):
            identifier = f"{name}-t{index}"
            turns.append(_assistant(stamp, size, [_bash(identifier, commands[index])]))
            turns.append(_result(identifier, f"output of {commands[index][:40]}"))
        else:
            turns.append(_assistant(stamp, size))
    if killed:
        turns.append(
            _assistant(
                stamp,
                sizes[-1],
                [{"type": "text", "text": "You've hit your session limit · resets 11:40pm"}],
                error="rate_limit",
                isApiErrorMessage=True,
            )
        )
    else:
        turns.append(_assistant(stamp, sizes[-1], [{"type": "text", "text": report}]))
    return transcript(projects, name, brief, turns, workflow, stamp)


def test_a_single_pass_is_a_brief_and_a_clean_exit(tmp_path: Path) -> None:
    """One completed pass: the brief renders, and nothing claims more than it covered."""
    plain_pass(tmp_path, "a1", "2026-01-01T00:00:00Z", ["uv run pytest tests/test_sync.py -q"])
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert out.returncode == 0, out.stdout + out.stderr
    assert "1 earlier review pass(es) over 20260101_0000-x" in out.stdout
    assert "uv run pytest tests/test_sync.py -q" in out.stdout
    assert "Found one issue: the cap is off by one." in out.stdout


def test_an_increment_with_nothing_on_disk_says_so_and_exits_two(tmp_path: Path) -> None:
    """Exit 2 is the honest answer, and it is not exit 0.

    `0` and `2` are different claims — "every pass finished" against "there were no passes" — and a
    tool that returned `0` for both would tell a caller its ledger was clean when it was absent.
    """
    out = run("20260101_0000-nothing", "--projects", str(tmp_path))
    assert out.returncode == 2, out.stdout + out.stderr
    assert "does start from zero" in out.stderr


def test_a_killed_pass_is_not_a_pass_that_reported(tmp_path: Path) -> None:
    """A rate-limited agent's last words are not its findings, and the exit status says so.

    The transcript is read structurally — the record carries `error` and `isApiErrorMessage` — never
    by matching the prose, because the prose is ordinary assistant text and a future harness will
    word it differently.
    """
    plain_pass(tmp_path, "a1", "2026-01-01T00:00:00Z", ["uv run pytest -q"], killed=True)
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert out.returncode == 1, out.stdout + out.stderr
    assert "KILLED by the harness (rate_limit)" in out.stdout
    assert "LAST WORDS" in out.stdout
    assert "1 of 1 pass(es) did NOT finish" in out.stdout


def test_a_pass_that_finished_and_said_nothing_is_incomplete(tmp_path: Path) -> None:
    """Silence is the quieter failure: it reads as a clean bill and replays from cache as one."""
    turns: list[dict[str, object]] = [
        _assistant("2026-01-01T00:00:00Z", size) for size in (100, 200, 300, 400, 500, 600)
    ]
    transcript(tmp_path, "a1", REVIEW_BRIEF, turns)
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert out.returncode == 1, out.stdout + out.stderr
    assert "died before a final message" in out.stdout


def test_an_implementer_is_not_a_review_pass(tmp_path: Path) -> None:
    """The classifier trap this repository sets for itself.

    `CLAUDE.md` instructs every implementer to adversarially review its own work, so a coder's brief
    contains the reviewer vocabulary. Counting it as a pass puts the work under review into the
    evidence for reviewing it — and coder runs are the most expensive in the corpus, so it moves
    every derived share.
    """
    plain_pass(tmp_path, "a1", "2026-01-01T00:00:00Z", ["uv run pytest -q"], brief=BUILD_BRIEF)
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert out.returncode == 2, out.stdout + out.stderr


def test_a_package_path_keeps_its_directories(tmp_path: Path) -> None:
    """`src/pinakes/sync.py` must not reduce to `sync.py`.

    Anchoring normalisation on the repository's name matched the *package* directory just as
    readily as the checkout. Two passes reading two different files then looked like two passes
    reading one, in the tool whose headline number is how often that happens.
    """
    plain_pass(
        tmp_path,
        "a1",
        "2026-01-01T00:00:00Z",
        ["cat /Users/x/Pinakes-worktrees/br/src/pinakes/sync.py"],
    )
    out = run("20260101_0000-x", "--projects", str(tmp_path), "--json")
    assert out.returncode == 0, out.stdout + out.stderr
    files = json.loads(out.stdout)["passes"][0]["files"]
    assert files == ["src/pinakes/sync.py"], files


def test_a_branch_named_directory_does_not_leak_into_the_path(tmp_path: Path) -> None:
    """The *last* top-level directory wins, or a branch name becomes part of the file's identity.

    `Pinakes-worktrees/20260807_2143-docs-audit-findings/docs/README.md` contains `docs/` twice.
    Taking the first would keep the branch, and one file read from two branches would be two.
    """
    plain_pass(
        tmp_path,
        "a1",
        "2026-01-01T00:00:00Z",
        ["cat /Users/x/Pinakes-worktrees/20260807_2143-docs-audit/tools/land.py"],
    )
    out = run("20260101_0000-x", "--projects", str(tmp_path), "--json")
    assert json.loads(out.stdout)["passes"][0]["files"] == ["tools/land.py"]


def test_one_probe_run_in_two_scratch_directories_is_one_probe(tmp_path: Path) -> None:
    """Two passes running the same command in their own copies have run the same probe once each.

    Every reviewer here stands up an isolated worktree with its own name, so comparing raw command
    strings made deduplication a no-op: 891 probes, 880 of them "distinct", and the ranking that
    was meant to surface the most-repeated work degenerated into insertion order.
    """
    plain_pass(
        tmp_path, "a1", "2026-01-01T00:00:00Z", ["cd /tmp/p2-quokka && uv run pytest -q"]
    )
    plain_pass(
        tmp_path, "a2", "2026-01-01T02:00:00Z", ["cd /tmp/p2-marlin && uv run pytest -q"]
    )
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert out.returncode == 0, out.stdout + out.stderr
    assert "cd <dir> && uv run pytest -q [2 passes]" in out.stdout


def test_reading_a_package_file_is_not_executing_the_project(tmp_path: Path) -> None:
    """`pinakes` is a directory as well as a command, so paths are stripped before verbs match.

    Without that, `sed -n '1,10p' src/pinakes/pairing.py` counted as an executing probe — and with
    it 586 of 762 probes on one increment, which put the file reading at the top of the section
    whose whole purpose is to rank running above reading.
    """
    plain_pass(
        tmp_path, "a1", "2026-01-01T00:00:00Z", ["sed -n '1,10p' src/pinakes/pairing.py"]
    )
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert "0" == out.stdout.split("distinct, ")[1].split()[0], out.stdout


def test_a_workflow_fanouts_agents_are_found(tmp_path: Path) -> None:
    """Fan-out agents live one directory deeper, and they are 81% of the corpus here.

    A glob written for the shallow layout alone finds a fifth of the transcripts while looking
    entirely healthy — the same near-miss `tools/review_pass_gate.py` records against its own
    discovery, which is why it is asserted rather than assumed.
    """
    plain_pass(tmp_path, "a1", "2026-01-01T00:00:00Z", ["uv run pytest -q"], workflow="wf_abc123")
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert out.returncode == 0, out.stdout + out.stderr
    assert "1 earlier review pass(es)" in out.stdout


def test_the_repeat_share_is_the_arithmetic_it_claims(tmp_path: Path) -> None:
    """`--measure` on a fixture whose answer can be computed by hand.

    Pass 2 has six probing turns of context 100..600 and a seventh that reports, so raw is 2700
    over seven turns. Each turn adds 100 and that 100 is re-transmitted by every turn after it, so
    turn 0's weight is 100 x 6 = 600 and turn 1's is 100 x 5 = 500. Turn 0 re-opens the file pass 1
    opened (600 / 2700 = 22.2%); turn 1 opens one no pass has (500 / 2700 = 18.5%). Both must come
    out of the tool unchanged, or the cost model in the docstring is not the one in the code.

    The seventh turn is the reason this test was wrong before it was right: the first version
    computed 23.8% by hand over six turns and the tool said 22.2%. The tool was correct — the
    fixture reports, as every real pass does.
    """
    sizes = [100, 200, 300, 400, 500, 600]
    plain_pass(
        tmp_path,
        "a1",
        "2026-01-01T00:00:00Z",
        ["cat src/pinakes/sync.py"],
        contexts=sizes,
    )
    plain_pass(
        tmp_path,
        "a2",
        "2026-01-01T01:00:00Z",
        ["cat src/pinakes/sync.py", "cat src/pinakes/store.py"],
        contexts=sizes,
    )
    out = run("--measure", "--json", "--projects", str(tmp_path))
    assert out.returncode == 0, out.stdout + out.stderr
    numbers = json.loads(out.stdout)
    assert numbers["later_passes"] == 1.0
    assert numbers["increments"] == 1.0
    assert numbers["repeat_share_pct"] == 22.2, numbers
    assert numbers["new_share_pct"] == 18.5, numbers


def test_concurrent_members_of_one_fanout_are_measured_apart(tmp_path: Path) -> None:
    """Passes minutes apart cannot carry from each other, so they are not counted as if they could.

    Reporting them together would credit a sequential carry-forward with spend it could never have
    recovered. They are counted — a *shared* brief is exactly what helps them — under their own key.
    """
    sizes = [100, 200, 300, 400, 500, 600]
    plain_pass(tmp_path, "a1", "2026-01-01T00:00:00Z", ["cat src/pinakes/sync.py"], contexts=sizes)
    plain_pass(tmp_path, "a2", "2026-01-01T00:01:00Z", ["cat src/pinakes/sync.py"], contexts=sizes)
    out = run("--measure", "--json", "--projects", str(tmp_path))
    numbers = json.loads(out.stdout)
    assert numbers["later_passes"] == 0.0, numbers
    assert numbers["repeat_share_pct"] == 0.0, numbers
    assert numbers["concurrent_repeat_share_pct"] == 22.2, numbers


def test_housekeeping_is_not_carried_as_evidence(tmp_path: Path) -> None:
    """`cd`, `ls` and worktree setup are how a pass reaches the work, not what it found."""
    plain_pass(
        tmp_path,
        "a1",
        "2026-01-01T00:00:00Z",
        ["git worktree add --detach /tmp/p2-x HEAD", "uv run pytest -q"],
    )
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert "git worktree add" not in out.stdout
    assert "uv run pytest -q" in out.stdout


def test_the_brief_always_states_what_it_is_not(tmp_path: Path) -> None:
    """The three disclaimers are load-bearing, so their absence is a failure and not a style note.

    A carried-forward map is the cheapest way yet invented to make a later pass inherit an earlier
    pass's mistake: a file listed as opened reads as covered, a command reads as a verdict, a
    finding reads as a fact. Every one of those three is wrong, and the brief is the only place a
    reader is told so.
    """
    plain_pass(tmp_path, "a1", "2026-01-01T00:00:00Z", ["uv run pytest -q"])
    out = run("20260101_0000-x", "--projects", str(tmp_path))
    assert "OPENED, never reviewed" in out.stdout
    assert "Exit status is not in the transcript" in out.stdout
    assert "CLAIM of the pass that made it" in out.stdout


def test_the_listing_ranks_increments_by_what_they_cost(tmp_path: Path) -> None:
    """`--list` is how a reader finds an increment worth a brief, so it leads with the expensive."""
    plain_pass(tmp_path, "a1", "2026-01-01T00:00:00Z", ["uv run pytest -q"], contexts=[10] * 6)
    plain_pass(
        tmp_path,
        "b1",
        "2026-01-02T00:00:00Z",
        ["uv run pytest -q"],
        brief="Adversarially reviewing increment 20260102_0000-y in Pinakes.",
        contexts=[9000] * 6,
    )
    out = run("--list", "--projects", str(tmp_path))
    assert out.returncode == 0, out.stdout + out.stderr
    rows = [line for line in out.stdout.splitlines() if "20260" in line]
    assert rows[0].endswith("20260102_0000-y"), out.stdout
