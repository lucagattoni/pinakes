"""A review fan-out that lost agents reports success — this gate reads the journal and refuses.

**The failure, measured 20260825.** A planner session ran an adversarial review as a `Workflow`
fan-out. It returned `{"confirmed":[],"total_raised":0}` — a clean bill — while **four of its seven
agents had died** on the usage limit. A coder session hit the same thing the same day: six agents
launched, all six killed, `{"survived":[],"unverified":[],"refuted":[],"clean":[]}` returned after
800k tokens. Neither result was wrong about what it found. Both were wrong about having looked.

**It is the documented behaviour, not a bug either session hit.** An agent that dies on a terminal
API error *returns `null`*, and the tool's own recommended idiom for collecting a fan-out is
`.filter(Boolean)`. So the standard way to write the script silently turns a dead agent into an
absent finding. Nothing in the result distinguishes "nobody found anything" from "nobody looked",
which is the same shape as a mutation run with no kills: **a pass that returns zero is a claim about
the pass**, and this repository already refuses that claim everywhere else (`docs/BUILDING.md` §
*Break the code on purpose*, `tools/mutate.py`'s kill-one-first refusal).

**The journal is ground truth and it is already on disk.** Every fan-out writes
`<transcript-dir>/journal.jsonl`, one line per event:

    {"type":"started","key":"v2:<hash>","agentId":"a4b0c38…"}
    {"type":"result", "key":"v2:<hash>","agentId":"a4b0c38…","result":"…"}

A `result` carries the same `key` as its `started`. So `started` keys with no `result` **are** the
dead agents — a count, not a heuristic. Checked against a real run before this gate was written:
`wf_d92d1916-c2c` records 7 `started` and 5 `result`.

**Two failure modes, not one.** A dead agent is the loud case. The quiet one is an agent that
completed and returned *nothing* — an empty string, `null`, or a schema object whose every array is
empty. Resuming does not help there (the empty result is what gets replayed from cache), and it
reads as a clean bill just as convincingly. Both are reported; both fail the gate.

**Why it also lists artifacts, and why they are labelled EVIDENCE.** A dead agent's context is gone,
but its files are not — and re-running a recovered probe is far cheaper than re-running the agent.

Measured over **533 review-classified subagent runs** in this project, and the numbers argue for
*enforcing* a probe convention rather than exploiting one: **only 41% leave any artifact at all, and
59% leave nothing**. Of 6,146 redirect and write targets, **49.2% are not file paths** (a `head -c`
count, a `2>&1`, a dict literal inside a heredoc), 27.1% are `/dev/null` or an fd dup, **12.8% land
somewhere that survives, and 10.9% land where `land.py --cleanup` destroys them** — so of the
artifacts that are real, roughly half die with the worktree. A coder session losing a lens's probes
to cleanup within the hour was an ordinary outcome, not bad luck, and this gate exists to be run
**before** anything cleans up.

**Those figures were wrong in this docstring until 20260826, and both causes are worth naming.**
It first read *"613 review agents, 87% leave some artifact, 58% of 6,015 targets are relative
paths"*. The population was classified by matching the word "review" over each agent's brief — but
this repo instructs every *implementer* to "adversarially review" its own work, so coder agents
counted as reviewers, and coder agents write far more files than reviewers do. And the `is_file`
filter above was added *during this tool's own build*, after a real run reported `0` and `15,}` as
recoverable files; adding it silently falsified the measurement quoted three paragraphs below it,
which nobody re-ran. **A number in a docstring is a claim with no gate on it**, and the fix that
invalidates it will not say so.

They are listed as evidence and never as findings. A recovered probe says what the agent ran, never
what it concluded — one recovered probe in the run that motivated this asserted something its own
agent may have been about to refute. Presenting recovered artifacts as findings would be worse than
the empty result it replaces.

**Exit status is the point.** Run it bare, as the thing that gates believing a pass:

    python3 tools/review_pass_gate.py                      # newest fan-out in this project
    python3 tools/review_pass_gate.py wf_2117df7c-723      # one run
    python3 tools/review_pass_gate.py --json               # for a script

`0` — every agent started, returned, and returned something. `1` — at least one did not, and the
result you are holding is not a clean bill. Never pipe it into anything before reading `$?`:
`check | tail && commit` reports `tail`'s status, and that shape has landed commits over a red gate
here twice (`CLAUDE.md` § *A gate is only a gate when its exit status is what the next command
reads*).

`--journal` and `--transcript-dir` exist for the unit tests and for the negative check that this
gate can still fail; with neither, it finds the newest run itself.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

PROJECTS: Final = Path.home() / ".claude" / "projects"
"""Where every session's transcripts and fan-out journals live, one directory per project."""

REDIRECT: Final = re.compile(r">>?\s*([^\s;&|)\"']+)")
"""Shell redirect targets inside a `Bash` command.

Crude on purpose — this locates candidates for a human to go and read, and it never decides the exit
status. But it is not *credulous*: run against a real fan-out it reported `0`, `c` and `15,}` as
files, picked out of `head -c`, a `2>&1` and a dict literal inside a heredoc. A list a reader learns
to skim is worth less than a shorter true one, so `_looks_like_a_file` filters them."""

FILENAME: Final = re.compile(r"^[\w@.,+~/-]+$")
"""A redirect target worth reporting. Must also carry a `/` or a `.` — a bare word at the end of a
`>` is far more often a shell fragment than a file someone will open."""

FD_DUP: Final = frozenset({"&1", "&2", "/dev/null", "/dev/stdout", "/dev/stderr"})
"""Redirect targets that leave nothing behind. 33% of the 6,015 measured targets were these."""

LIVE_WINDOW: Final = 180.0
"""Seconds of quiet before a fan-out with outstanding agents is called dead rather than running.

**A live run and a killed run look identical in the journal** — neither writes a "finished" line, so
an agent that has not returned yet is indistinguishable from one that never will. The first version
of this gate had no such window and reported all six agents of a *currently running* fan-out as
dead. That is the worst failure available to it: a gate that cries wolf on a healthy run is one
people learn to ignore, and then it is not a gate. So recent write activity means **cannot judge**
(exit 2), never **failed** (exit 1). `--assume-finished` overrides it for a run you know has ended.
"""


@dataclass(frozen=True)
class Artifact:
    """One file a dead agent wrote, and whether it will survive the worktree being removed."""

    path: str
    survives_cleanup: bool
    reason: str


@dataclass
class Agent:
    """One agent in a fan-out, as the journal records it."""

    key: str
    agent_id: str
    returned: bool = False
    result: object = None
    tokens: int = 0
    last_tool: str | None = None
    artifacts: list[Artifact] = field(default_factory=list[Artifact])

    @property
    def empty(self) -> bool:
        """Returned, but with nothing in it.

        A completed agent that returned nothing reads as a clean bill exactly like a dead one, and
        unlike a dead one it cannot be recovered by resuming — the empty result is what replays from
        cache. `0`, `False` and `"0"` are values, not emptiness; only an absent result, blank text,
        an empty container, or a schema object whose every container is empty counts.
        """
        if not self.returned:
            return False
        return _is_empty(self.result)


def _is_empty(value: object) -> bool:
    """Recursively decide whether a returned result carries any content at all."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple)):
        return all(_is_empty(item) for item in cast(list[object], value))
    if isinstance(value, dict):
        return all(_is_empty(item) for item in cast(dict[str, object], value).values())
    return False


def _looks_like_a_file(target: str) -> bool:
    """Reject the shell fragments a bare `>`-scan picks up alongside real paths."""
    if target in FD_DUP or not FILENAME.match(target):
        return False
    if "/" not in target and "." not in target:
        return False
    return not target.replace(".", "").isdigit()


def _classify(target: str) -> Artifact | None:
    """Where a redirect target lands, and whether worktree cleanup destroys it.

    The four buckets are the ones the measurement found, in the proportions it found them: relative
    (58%, fragile), fd-dup or `/dev/null` (33%, nothing to recover), `/tmp` (9%, survives cleanup
    but not a reboot), any other absolute path (0.1%, stable).
    """
    if not _looks_like_a_file(target):
        return None
    if not target.startswith("/"):
        return Artifact(
            target, False, "relative path — lands in the agent's cwd, usually its worktree"
        )
    if "worktrees" in target:
        return Artifact(target, False, "inside a worktree — destroyed by land.py --cleanup")
    if target.startswith(("/tmp/", "/private/tmp/", "/var/folders/")):
        return Artifact(target, True, "/tmp — survives worktree cleanup, not a reboot")
    return Artifact(target, True, "absolute path outside any worktree")


def read_journal(journal: Path) -> list[Agent]:
    """Parse a fan-out journal into one `Agent` per `started` line, in launch order.

    Matching is on `key`, which is what the journal itself pairs a `result` to a `started` with. A
    malformed line is skipped rather than fatal: a truncated journal is exactly the situation this
    gate is for, and refusing to parse it would hide the failure it exists to report.
    """
    agents: dict[str, Agent] = {}
    order: list[str] = []
    for line in journal.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            loaded: object = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(loaded, dict):
            continue
        event = cast(dict[str, object], loaded)
        key = event.get("key")
        if not isinstance(key, str):
            continue
        kind = event.get("type")
        if kind == "started":
            if key not in agents:
                agent_id = event.get("agentId")
                agents[key] = Agent(
                    key=key, agent_id=agent_id if isinstance(agent_id, str) else "?"
                )
                order.append(key)
        elif kind == "result" and key in agents:
            agents[key].returned = True
            agents[key].result = event.get("result")
    return [agents[k] for k in order]


def enrich(agent: Agent, transcript_dir: Path) -> None:
    """Fill in what a dead agent spent and what it left behind, from its own transcript.

    Best-effort by design. A missing transcript is normal — the agent may have died before writing
    one — and must not stop the gate reporting the death, which is the part that matters.
    """
    transcript = transcript_dir / f"agent-{agent.agent_id}.jsonl"
    if not transcript.is_file():
        return
    seen: set[str] = set()
    for line in transcript.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            loaded: object = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(loaded, dict):
            continue
        entry = cast(dict[str, object], loaded)
        raw_message = entry.get("message")
        if not isinstance(raw_message, dict):
            continue
        message = cast(dict[str, object], raw_message)
        usage = message.get("usage")
        if isinstance(usage, dict):
            for field_name in (
                "input_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
                "output_tokens",
            ):
                count = cast(dict[str, object], usage).get(field_name)
                if isinstance(count, int):
                    agent.tokens += count
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for raw_block in cast(list[object], content):
            if not isinstance(raw_block, dict):
                continue
            block = cast(dict[str, object], raw_block)
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if isinstance(name, str):
                agent.last_tool = name
            raw_payload = block.get("input")
            if not isinstance(raw_payload, dict):
                continue
            payload = cast(dict[str, object], raw_payload)
            if name == "Write":
                path = payload.get("file_path")
                if isinstance(path, str) and path not in seen:
                    seen.add(path)
                    found = _classify(path)
                    if found is not None:
                        agent.artifacts.append(found)
            elif name == "Bash":
                command = payload.get("command")
                if not isinstance(command, str):
                    continue
                for target in cast(list[str], REDIRECT.findall(command)):
                    if target in seen:
                        continue
                    seen.add(target)
                    found = _classify(target)
                    if found is not None:
                        agent.artifacts.append(found)


def quiet_for(directory: Path, journal: Path) -> float:
    """Seconds since anything in this fan-out was last written."""
    newest = journal.stat().st_mtime if journal.is_file() else 0.0
    for transcript in directory.glob("agent-*.jsonl"):
        newest = max(newest, transcript.stat().st_mtime)
    return time.time() - newest


def find_runs(projects: Path | None = None) -> list[Path]:
    """Every fan-out directory on this machine, newest first.

    Keyed on the journal rather than on the directory layout. The real path is
    `projects/<project-slug>/<session-uuid>/subagents/workflows/wf_…`, and the first version of this
    function globbed one level too few — every unit test still passed, because they all pass
    `--journal` and never reach discovery. Running it against a real fan-out is what found it, which
    is the standing rule here: a seam built for testability defines a region no test reaches, so
    `test_discovery_finds_a_real_layout` walks a fixture tree of the true shape.
    """
    root = projects if projects is not None else PROJECTS
    if not root.is_dir():
        return []
    runs = [j.parent for j in root.rglob("journal.jsonl") if j.is_file()]
    return sorted(runs, key=lambda p: (p / "journal.jsonl").stat().st_mtime, reverse=True)


def resolve(
    run: str | None, transcript_dir: Path | None, projects: Path | None = None
) -> Path | None:
    """Pick the fan-out to check: an explicit directory, a run id, or the newest one."""
    if transcript_dir is not None:
        return transcript_dir
    runs = find_runs(projects)
    if run is not None:
        for path in runs:
            if path.name == run or path.name.startswith(run):
                return path
        return None
    return runs[0] if runs else None


def report(agents: list[Agent], run_name: str, script_hint: str | None) -> int:
    """Print the verdict and return the exit status.

    `0` only when every agent came back with something.
    """
    dead = [a for a in agents if not a.returned]
    empty = [a for a in agents if a.empty]
    print(f"fan-out {run_name}: {len(agents)} launched, {len(agents) - len(dead)} returned")

    if not dead and not empty:
        print("every agent completed and returned content — the result is a pass that actually ran")
        return 0

    if dead:
        print(
            f"\n{len(dead)} agent(s) DIED — this result is not a clean bill, "
            "it is an unfinished pass:"
        )
        for agent in dead:
            spent = f"{agent.tokens:,} tokens" if agent.tokens else "no usage recorded"
            print(f"  - {agent.agent_id}  ({spent}, last tool: {agent.last_tool or 'none'})")
            recoverable = [a for a in agent.artifacts if a.survives_cleanup]
            fragile = [a for a in agent.artifacts if not a.survives_cleanup]
            if recoverable:
                print("      EVIDENCE, NOT FINDINGS — re-run these rather than the agent:")
                for artifact in recoverable:
                    print(f"        {artifact.path}   ({artifact.reason})")
            if fragile:
                print(
                    f"      {len(fragile)} artifact(s) will be DESTROYED by worktree "
                    "cleanup — read them first:"
                )
                for artifact in fragile:
                    print(f"        {artifact.path}   ({artifact.reason})")
            if not agent.artifacts:
                print("      left nothing on disk — nothing to recover")

    if empty:
        print(f"\n{len(empty)} agent(s) returned EMPTY — completed, but with no content:")
        for agent in empty:
            print(
                f"  - {agent.agent_id}  (resuming replays this empty result from "
                "cache; re-run it instead)"
            )

    if dead:
        hint = f'scriptPath: "{script_hint}", ' if script_hint else "scriptPath: <the script>, "
        print(
            f"\nresume — replays the {len(agents) - len(dead)} completed agent(s) "
            "from cache, re-runs only the dead:"
        )
        print(f'  Workflow({{{hint}resumeFromRunId: "{run_name}"}})')
        print(
            "  (same-session only: if this session has ended, the journal above is what survives)"
        )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="review_pass_gate", description=__doc__)
    parser.add_argument(
        "run", nargs="?", help="workflow run id (wf_…); default: the newest fan-out"
    )
    parser.add_argument("--journal", type=Path, help="read this journal.jsonl directly (tests)")
    parser.add_argument("--transcript-dir", type=Path, help="read this fan-out directory (tests)")
    parser.add_argument("--script", help="script path to print in the resume hint")
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="machine-readable output"
    )
    parser.add_argument(
        "--list", action="store_true", help="list the fan-outs on this machine and stop"
    )
    parser.add_argument(
        "--projects-dir", type=Path, help="search here instead of ~/.claude/projects (tests)"
    )
    parser.add_argument(
        "--assume-finished",
        action="store_true",
        help="judge a run even if it was written to recently — for a run you know has ended",
    )
    args = parser.parse_args(argv)

    if args.list:
        for path in find_runs(args.projects_dir):
            print(path)
        return 0

    if args.journal is not None:
        journal = args.journal
        directory = args.transcript_dir if args.transcript_dir is not None else journal.parent
    else:
        directory = resolve(args.run, args.transcript_dir, args.projects_dir)
        if directory is None:
            print(
                f"no fan-out found for {args.run!r}" if args.run else "no fan-out found",
                file=sys.stderr,
            )
            return 2
        journal = directory / "journal.jsonl"

    if not journal.is_file():
        print(f"no journal at {journal}", file=sys.stderr)
        return 2

    agents = read_journal(journal)
    if not agents:
        print(f"journal at {journal} records no agents — nothing was launched", file=sys.stderr)
        return 2
    for agent in agents:
        if not agent.returned:
            enrich(agent, directory)

    outstanding = [a for a in agents if not a.returned]
    if outstanding and not args.assume_finished:
        quiet = quiet_for(directory, journal)
        if quiet < LIVE_WINDOW:
            print(
                f"fan-out {directory.name}: {len(agents)} launched, "
                f"{len(agents) - len(outstanding)} returned — "
                f"but it was written to {quiet:.0f}s ago, so it is probably STILL RUNNING.\n"
                "Cannot judge this pass yet. Re-run when it is quiet, or pass "
                "--assume-finished if you know it has ended.",
                file=sys.stderr,
            )
            return 2

    if args.as_json:
        dead = [a for a in agents if not a.returned]
        empty = [a for a in agents if a.empty]
        print(
            json.dumps(
                {
                    "run": directory.name,
                    "launched": len(agents),
                    "returned": len(agents) - len(dead),
                    "pass_is_valid": not dead and not empty,
                    "dead": [
                        {
                            "agent_id": a.agent_id,
                            "tokens": a.tokens,
                            "last_tool": a.last_tool,
                            "artifacts": [
                                {
                                    "path": f.path,
                                    "survives_cleanup": f.survives_cleanup,
                                    "reason": f.reason,
                                }
                                for f in a.artifacts
                            ],
                        }
                        for a in dead
                    ],
                    "empty": [a.agent_id for a in empty],
                },
                indent=2,
            )
        )
        return 1 if (dead or empty) else 0

    return report(agents, directory.name, args.script)


if __name__ == "__main__":
    sys.exit(main())
