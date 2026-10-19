"""A Stop hook: a turn cannot end over a fan-out that lost agents while nobody has said so.

**The failure it answers** is the one `tools/review_pass_gate.py` was written for: a review fan-out
that lost 17 of its 19 agents to a session limit returned `{"raised":0}`, and the session that read
it reported a clean pass. The gate can tell the two apart, but a gate nobody runs is a claim. This
hook runs it for you, at the one moment that is always reached — the turn ending — over every
workflow run of **this session**, and refuses the end while a run that did not finish cleanly has
not been acknowledged. (Step 2 of *Framing, Not Roles* § 9, plan
`plans/20261018_2354-option-a-review-coverage-and-claude-md.md` § 4.)

**It is a nudge and not a lock, and the plan says so rather than discovering it.** Claude Code
overrides a Stop hook after eight consecutive continuations (the count resets whenever Claude calls
a tool; `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises it). `stop_hook_active` — true while Claude is
already continuing because of a stop hook — is read only to say "again" in the message. It never
turns the block off, because the user chose *block until acknowledged* (D2) and the cap is the
bound; the condition resolves because acknowledging is one command.

**What it judges, and what it does not.** It reads the *journal*: agents that started and never
returned (dead), and agents that returned nothing (empty). `VACUOUS` here means no agent returned
anything, `PARTIAL` means some did not. That is **not** the workflow's own `coverage`
(`.claude/workflows/adversarial-review.js`), which also sees a lens that reported `not_run`, a reply
that came back unusable, a finding over the cap and a guess. A run can pass this hook and be
`PARTIAL` there, and the message says to read it. The journal is the part that is ground truth even
when the workflow's return value never arrived.

**Acknowledging.** The block message prints the command. It writes `gate-acknowledged.json` into the
run's own directory, carrying what the session told the user (`--told`: a sentence of at least three
words, and not the placeholder the message prints) and the verdict it covers: `launched`,
`returned`, `empty` and a digest of the journal. The digest is what makes "covers only the verdict
it was given for" true: a resume appends to the same journal in the same run directory (seen in
real journals, and the reason a counts-only fingerprint would not do), so any later line is a
different verdict that is judged again.

**Never in `check.sh` or CI.** There is no journal there, and a gate over no journal passes
vacuously. It reads `transcript_path` from the hook payload, so it only ever looks at the session
that is ending, never at every fan-out on the machine.

**Quiet failure is the thing being prevented, so this hook does not do it.** An internal error
exits `1` with the cause on stderr — a non-blocking error Claude Code shows — and does not block
(a hook bug would otherwise trap every turn for eight rounds). A gate that exits `1` without the
verdict it promises is treated as a crash, not as a failed review, for the same reason: `1` is also
what an uncaught traceback exits with.

**It runs while a workflow is in flight, so it must not mistake that for a death.** The gate's
"quiet for 180 s" rule cannot tell a slow agent from a dead one. When the payload's
`background_tasks` lists a workflow, nothing is judged — the notification that ends the run starts a
new turn, and that turn's Stop judges it. When the list is present and holds no workflow, every
run is judged with `--assume-finished`, because a run that is not in flight and has outstanding
agents has none that will return; without that, a fan-out killed seconds before the turn ended
would read "probably still running" and pass. When the list is absent the gate's own window decides.

**What it cannot see, stated so nobody reads silence as a clean review.** (1) The workflow's own
`coverage` is not in the journal, so a run whose every agent returned passes here even when the
review reported `PARTIAL` — the first live run did exactly that, over 24 probes it could not run.
(2) The gate pairs agents by journal key: a key that returned and was later started again without
returning still reads as returned, so a resumed pass that loses already-returned agents can pass
(a gate limit, open; the hook re-judges the run after a resume but the gate may still say the same
thing). (3) The command in `settings.json` runs the script from the working directory's git
top-level, so a session that `cd`s into another checkout runs that checkout's copy at every Stop,
with no prompt: the price of following a worktree, accepted because the alternative is the original
checkout's stale copy.

**Written to run on whatever `python3` the hook's environment finds.** On this machine that has been
the Xcode 3.9, and a hook that does not even start is a silent non-blocking error — the failure this
file exists to remove. So: standard library only, `from __future__ import annotations`, no
`datetime.UTC`, no `match`, no `zip(strict=)`; `tests/test_review_stop_hook.py` parses it as 3.9 and
runs it under `/usr/bin/python3` where there is one.

**The command in `.claude/settings.json` finds this file from the working directory's git
top-level, not from `${CLAUDE_PROJECT_DIR}`**, which stays at the original checkout inside a
worktree and would run that checkout's copy — a stale one, or none. A checkout without the file
exits `0`; `python3` on a missing script exits `2`, which for a Stop hook is a block.

    python3 tools/hooks/review_stop_hook.py                # hook mode: the payload is on stdin
    python3 tools/hooks/review_stop_hook.py --acknowledge RUN_DIR --told "what the user was told"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

GATE: Final = Path(__file__).resolve().parent.parent / "review_pass_gate.py"
"""The gate this hook runs. A sibling, so there is nothing to import and nothing for `sys.path` to
get wrong: it is run as a subprocess, which is also the artifact a person runs."""

ACK: Final = "gate-acknowledged.json"
"""Written into a run's own directory, so it dies with the run and is found by the same path."""

GATE_TIMEOUT: Final = 20
"""Seconds a single gate run may take. A journal is read once; this is generous."""

PLACEHOLDER: Final = "<what you told the user>"
"""What the block message prints in `--told`. Pasting it unchanged is not an acknowledgement."""

MIN_TOLD_WORDS: Final = 3


class HookError(Exception):
    """Something the hook could not do. Reported on stderr with exit `1`; never a block."""


@dataclass(frozen=True)
class Verdict:
    """A run that did not finish cleanly, as the gate's `--json` reports it."""

    run: str
    directory: Path
    launched: int
    returned: int
    dead: tuple[tuple[str, str], ...]
    """`(agent id, last tool)` for every agent that started and never returned."""
    empty: tuple[str, ...]
    """Ids of agents that returned, with nothing in the result."""
    digest: str
    """SHA-256 of the journal as the gate read it: any later line changes it."""
    labels: dict[str, str]
    """Agent id to the label its `started` event carried (`lens:runtime`), where it had one."""

    @property
    def usable(self) -> int:
        return self.launched - len(self.dead) - len(self.empty)

    @property
    def label(self) -> str:
        """`VACUOUS` when nobody returned anything, `PARTIAL` when some did."""
        return "VACUOUS" if self.usable <= 0 else "PARTIAL"

    def named(self, agent_id: str) -> str:
        return self.labels.get(agent_id) or "no label"

    def covered_by(self) -> dict[str, object]:
        """What an acknowledgement records: the run it was given for, down to its last line."""
        return {
            "launched": self.launched,
            "returned": self.returned,
            "empty": len(self.empty),
            "digest": self.digest,
        }


@dataclass(frozen=True)
class Judged:
    """What the gate said about one run: `clean`, `bad`, or `unjudged` (cannot tell yet)."""

    status: str
    verdict: Verdict | None = None
    note: str = ""


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise HookError(f"expected a JSON object, got {type(value).__name__}")
    return cast(dict[str, object], value)


def _list(value: object, what: str) -> list[object]:
    if not isinstance(value, list):
        raise HookError(f"{what}: expected a list, got {type(value).__name__}")
    return cast(list[object], value)


def _int(value: object, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise HookError(f"{what}: expected an integer, got {value!r}")
    return value


def _text(value: object) -> str:
    return value if isinstance(value, str) else ""


def journal_labels(journal: Path) -> dict[str, str]:
    """Agent id to label, from the journal's `started` events; empty where it carries none.

    Split on a newline only (`str.splitlines` also splits on U+2028, which JSON allows raw inside a
    string). A line that does not parse is skipped: the gate has already said what it thinks of it.
    """
    labels: dict[str, str] = {}
    for line in journal.read_text(encoding="utf-8", errors="replace").split("\n"):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        body = cast(dict[str, object], event)
        agent, label = body.get("agentId"), body.get("label")
        if body.get("type") == "started" and isinstance(agent, str) and isinstance(label, str):
            labels.setdefault(agent, label)
    return labels


def judge(directory: Path, assume_finished: bool) -> Judged:
    """Run the gate over one run directory and read its answer.

    Its exit status is the point: `0` clean, `1` not clean (with `--json`, a verdict on stdout),
    `2` cannot judge. `1` without a parseable verdict is a crash — an uncaught traceback exits `1`
    too — and raises rather than being believed.
    """
    command = [sys.executable, str(GATE), "--journal", str(directory / "journal.jsonl"), "--json"]
    if assume_finished:
        command.append("--assume-finished")
    try:
        done = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=GATE_TIMEOUT
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise HookError(f"could not run the gate on {directory.name}: {error}") from error
    if done.returncode == 0:
        return Judged("clean")
    if done.returncode == 2:
        return Judged("unjudged", note=done.stderr.strip())
    if done.returncode != 1:
        raise HookError(f"the gate exited {done.returncode} on {directory.name}: {_tail(done)}")
    try:
        body = _object(json.loads(done.stdout))
        dead = tuple(
            (_text(item.get("agent_id")) or "?", _text(item.get("last_tool")) or "none")
            for item in (_object(raw) for raw in _list(body.get("dead"), "dead"))
        )
        empty = tuple(_text(raw) or "?" for raw in _list(body.get("empty"), "empty"))
        verdict = Verdict(
            run=directory.name,
            directory=directory,
            launched=_int(body.get("launched"), "launched"),
            returned=_int(body.get("returned"), "returned"),
            dead=dead,
            empty=empty,
            digest=hashlib.sha256((directory / "journal.jsonl").read_bytes()).hexdigest(),
            labels=journal_labels(directory / "journal.jsonl"),
        )
    except (OSError, ValueError, HookError) as error:
        raise HookError(
            f"the gate exited 1 on {directory.name} without a verdict ({error}): {_tail(done)}"
        ) from error
    return Judged("bad", verdict)


def _tail(done: subprocess.CompletedProcess[str]) -> str:
    lines = (done.stderr or done.stdout).strip().splitlines()
    return lines[-1] if lines else "no output"


def acknowledged(verdict: Verdict) -> bool:
    """Whether the run's acknowledgement covers exactly this verdict, and says what was told."""
    try:
        recorded = json.loads((verdict.directory / ACK).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(recorded, dict):
        return False
    body = cast(dict[str, object], recorded)
    told = body.get("told")
    return (
        isinstance(told, str)
        and told.strip() != ""
        and body.get("verdict") == (verdict.covered_by())
    )


def session_runs(payload: dict[str, object]) -> list[Path]:
    """The workflow run directories of the session that is ending, oldest name first.

    The layout is `<projects>/<slug>/<session>.jsonl` for the transcript and
    `<projects>/<slug>/<session>/subagents/workflows/wf_*/journal.jsonl` for the runs, so the
    session's directory is the transcript path without its suffix. No `transcript_path`, or no
    directory beside it, means no run to look at — the ordinary case, and silent.
    """
    transcript = payload.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        return []
    root = Path(transcript).with_suffix("") / "subagents" / "workflows"
    if not root.is_dir():
        return []
    return sorted(journal.parent for journal in root.glob("wf_*/journal.jsonl"))


def workflow_in_flight(payload: dict[str, object]) -> bool | None:
    """Whether a workflow is running now: `True`, `False`, or `None` when the payload cannot say.

    The hooks reference says both arrays "are present when the task registry is reachable and are
    empty when nothing is in flight or scheduled". Absent is not empty, and treating it as empty
    would call every live run dead.
    """
    tasks = payload.get("background_tasks")
    if not isinstance(tasks, list):
        return None
    return any(
        isinstance(task, dict) and cast(dict[str, object], task).get("type") == "workflow"
        for task in cast(list[object], tasks)
    )


def unacknowledged(payload: dict[str, object]) -> tuple[list[Verdict], list[str]]:
    """Every run of this session that did not finish cleanly and has not been acknowledged, and the
    runs that could not be judged at all.

    One run the gate chokes on must not hide a dead run beside it, so a failure is collected per
    run and the others are still judged.
    """
    in_flight = workflow_in_flight(payload)
    if in_flight:
        return [], []
    found: list[Verdict] = []
    errors: list[str] = []
    for directory in session_runs(payload):
        try:
            judged = judge(directory, assume_finished=in_flight is False)
        except HookError as error:
            errors.append(str(error))
            continue
        if judged.verdict is not None and not acknowledged(judged.verdict):
            found.append(judged.verdict)
    return found, errors


def message(verdicts: list[Verdict], again: bool) -> str:
    """What Claude is told when the turn may not end yet."""
    script = shlex.quote(str(Path(__file__).resolve()))
    python = shlex.quote(sys.executable)
    lines = [
        "A workflow run of this session did not finish cleanly, and no acknowledgement says the "
        "user was told. A review that lost agents is not a clean pass, whatever its result reads."
    ]
    if again:
        lines.append("(This hook already stopped this turn once; it stops again until it is done.)")
    for verdict in verdicts:
        plural = "" if verdict.launched == 1 else "s"
        lines.append(
            f"\n{verdict.run}: {verdict.label} - {verdict.launched} agent{plural} launched: "
            f"{verdict.usable} returned something, {len(verdict.empty)} returned nothing, "
            f"{len(verdict.dead)} never returned."
        )
        lines.extend(
            f"  - never returned: {verdict.named(agent)} ({agent}, last tool: {tool})"
            for agent, tool in verdict.dead
        )
        lines.extend(
            f"  - returned nothing: {verdict.named(agent)} ({agent})" for agent in verdict.empty
        )
        lines.append(
            "  This is the journal's count of agents, not the review's own `coverage`: read the "
            "result's `coverage`, `lenses.died_why` and `not_run` as well. Resuming "
            "(`resumeFromRunId`) may retry an agent that never returned; one that returned nothing "
            "is replayed as it was and must be re-run."
        )
        lines.append(
            f"  Then acknowledge it: {python} {script} --acknowledge "
            f"{shlex.quote(str(verdict.directory))} --told {shlex.quote(PLACEHOLDER)}"
        )
    lines.append(
        "\nTell the user in your reply which agents died or came back empty and that the review "
        "is not a clean pass, then run the command above. Do not report these runs as clean."
    )
    return "\n".join(lines)


def run_hook(stdin: str) -> int:
    """Hook mode: print a block decision when a run needs saying, nothing otherwise."""
    try:
        payload = _object(json.loads(stdin))
    except (ValueError, HookError) as error:
        raise HookError(f"the Stop payload is not a JSON object: {error}") from error
    verdicts, errors = unacknowledged(payload)
    for error in errors:
        print(f"review_stop_hook: {error}", file=sys.stderr)
    if verdicts:
        again = payload.get("stop_hook_active") is True
        print(json.dumps({"decision": "block", "reason": message(verdicts, again)}))
        return 0
    return 1 if errors else 0


def acknowledge(directory: Path, told: str) -> int:
    """Record that the user was told about this run's current verdict.

    The run is judged as finished: someone who says they have told the user is saying it has ended,
    and the acknowledgement covers only the verdict it was given for, so a run that goes on to
    change is not hidden by it.
    """
    if not told.strip():
        print("--told is empty: say what the user was told, in a sentence.", file=sys.stderr)
        return 1
    if told.strip() == PLACEHOLDER or len(told.split()) < MIN_TOLD_WORDS:
        print(
            f"--told must say what the user was told, in a sentence of at least {MIN_TOLD_WORDS} "
            f"words; {told.strip()!r} is the placeholder or too short to be one.",
            file=sys.stderr,
        )
        return 1
    if not (directory / "journal.jsonl").is_file():
        print(f"{directory} is not a workflow run: no journal.jsonl in it.", file=sys.stderr)
        return 1
    judged = judge(directory, assume_finished=True)
    if judged.status == "clean":
        print(f"{directory.name} finished cleanly; there is nothing to acknowledge.")
        return 0
    if judged.verdict is None:
        print(f"{directory.name} cannot be judged yet: {judged.note}", file=sys.stderr)
        return 1
    record = {
        "run": judged.verdict.run,
        "verdict": judged.verdict.covered_by(),
        "label": judged.verdict.label,
        "told": told.strip(),
        "at": time.strftime("%Y%m%d %H:%M UTC", time.gmtime()),
    }
    (directory / ACK).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"{directory.name} ({judged.verdict.label}) acknowledged.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="review_stop_hook", description=__doc__)
    parser.add_argument("--acknowledge", type=Path, metavar="RUN_DIR", help="record what you told")
    parser.add_argument("--told", default="", help="what the user was told about the run")
    args = parser.parse_args(argv)
    try:
        if args.acknowledge is not None:
            return acknowledge(args.acknowledge, args.told)
        return run_hook(sys.stdin.read())
    except Exception as error:  # noqa: BLE001 — any failure here is reported, never a block
        print(f"review_stop_hook: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
