"""What the agents working on this repository actually spend, read out of their own transcripts.

Claude Code writes every session to `~/.claude/projects/<project>/<session>.jsonl`, and every
subagent to `<session>/subagents/`. Each assistant line carries a `usage` block. That looks like
enough to total, and it is not: **two properties of the format silently corrupt any naive sum**,
and this file exists because both were got wrong first and caught by re-measurement rather than by
reasoning.

    one API response is written as SEVERAL lines
        Every line of one response repeats the *same* `requestId` and an *identical* `usage`
        object. Summing per line inflates spend **2.14x** and makes every multi-tool request look
        single-tool, because each line holds at most one `tool_use` block. Key on `requestId`
        (falling back to `uuid`, which ~0.2% of lines need).

    `output_tokens` is a RUNNING PARTIAL — take the max, never the first
        It is monotonically non-decreasing across a request's lines in 100.00% of the 33,989
        multi-line requests measured. Taking the first line undercounts output by **1.7755x**.
        `input_tokens`, `cache_read_input_tokens` and `cache_creation_input_tokens` never differ
        across the lines of one request (0 cases), so only output is affected.

Both rules are asserted by `tests/test_agent_spend.py`, on synthetic transcripts shaped like the
real ones. A tool whose parser is wrong reports a number nobody can tell is wrong.

**Why this is a committed script and not an analysis.** Every figure this repository has recorded
about agent spend was produced by code that lived in one session's context, and a measurement whose
code dies with its context is one session limit away from being a number nobody can check. That is
not hypothetical here: a claim that "about 21% of reviewer runs die" reached a planner with a
population of 538 attached, and 538 cannot be reproduced from the transcripts by any definition —
the reproducible population is 868 workflow agent runs, of which 18.1% record no terminal row.
The number was not wildly wrong. It was unfalsifiable, which is worse.

**Reads nothing but transcripts, and writes nothing.** No network, no API calls, no cost beyond
disk. It never prints prompt or response text — only counts, models and identifiers — so its output
can be pasted into a public document. The transcripts themselves hold the user's own work and are
never in this repository.

Four subcommands, one per analysis:

**Every subcommand names the population it read.** `--scope all` (the default) counts main-loop
sessions, subagent runs and workflow agents; `--scope main` counts main-loop sessions only. The
default is `all` deliberately: a main-loop-only file list is what produced the false zero above,
because subagent transcripts live under `<session>/subagents/` and simply were not in it. The
restricted population is the one you must ask for by name, and the header repeats which you got.

    models      requests, tokens, price-units and estimated dollars per model
    boot        the fixed context each session re-transmits on every request, over time
    workflows   workflow agent outcomes, and how the runs that record none are distributed
    rewrites    mid-session full cache re-writes, bucketed by how long the session sat idle

Stdlib only, and it imports nothing from this project — the same constraint
`tools/shared_file_overlap.py` and `tools/paid_path_gate.py` carry.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import cast

#: Published $/MTok, (input, output), from the model table bundled with Claude Code 2.1.252, which
#: states its own cache date: "Current Models (cached: 2026-06-24)". **This is a rate card, not a
#: measurement** — it has not been checked against live Anthropic pricing, and a dollar figure
#: derived from it inherits that. The ratio most likely to matter here is that `claude-fable-5`
#: bills at exactly 2.00x `claude-opus-5` on both input and output, so a model share measured in
#: price-units understates fable's share of dollars by half.
RATES_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-fable-5": (10.0, 50.0),
    "claude-mythos-5": (10.0, 50.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

#: A cache write bills at ~1.25x the input rate and a cache read at ~0.1x, per the caching
#: documentation bundled with the `claude-api` skill. Applied to whichever model's rate is in force.
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.1

#: "Price-units" normalise every model onto one scale — input 1.0, output 5.0 — so a *shape* claim
#: ("context transmission is 85% of spend") does not silently become a claim about model mix. Use
#: units to compare where tokens go, and dollars to compare what they cost.
UNIT_OUTPUT_WEIGHT = 5.0

#: A request whose `cache_creation_input_tokens` exceeds this fraction of its whole context re-wrote
#: the cache rather than extending it. Only meaningful above `REWRITE_MIN_CONTEXT`: early in a
#: session almost everything is a write, which says nothing.
REWRITE_FRACTION = 0.5
REWRITE_MIN_CONTEXT = 20_000

#: Idle-gap buckets for `rewrites`, in seconds. The split that matters is inside vs. outside the
#: prompt-cache TTL: a re-write after a long gap is expiry, one after eight seconds is something
#: that changed the prompt prefix mid-turn, and they have different fixes.
GAP_BUCKETS: tuple[tuple[str, float], ...] = (
    ("<1 min", 60.0),
    ("1-5 min", 300.0),
    ("5-60 min", 3600.0),
    ("1-6 h", 21600.0),
    (">6 h", float("inf")),
)

#: Journal row types, and the state a row leaves an agent in. `started` only ever *establishes* an
#: agent; a terminal row overwrites it. An agent left in `NO_OUTCOME` recorded no result — which is
#: what makes a workflow resume re-run it, and is NOT by itself evidence that the agent died.
NO_OUTCOME = "no-terminal-row"


@dataclass(frozen=True)
class Request:
    """One API request, reassembled from the several transcript lines that carry it."""

    request_id: str
    model: str
    input_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    output_tokens: int
    timestamp: datetime | None
    is_sidechain: bool

    @property
    def context_tokens(self) -> int:
        """Everything the model was sent — the number re-transmitted on every turn."""
        return self.input_tokens + self.cache_write_tokens + self.cache_read_tokens

    @property
    def units(self) -> float:
        return (
            self.input_tokens
            + self.cache_write_tokens * CACHE_WRITE_MULTIPLIER
            + self.cache_read_tokens * CACHE_READ_MULTIPLIER
            + self.output_tokens * UNIT_OUTPUT_WEIGHT
        )

    @property
    def usd(self) -> float | None:
        """`None` when the model is not on the rate card — never a guessed price."""
        rate = RATES_USD_PER_MTOK.get(self.model)
        if rate is None:
            return None
        rate_in, rate_out = rate
        return (
            self.input_tokens * rate_in
            + self.cache_write_tokens * rate_in * CACHE_WRITE_MULTIPLIER
            + self.cache_read_tokens * rate_in * CACHE_READ_MULTIPLIER
            + self.output_tokens * rate_out
        ) / 1e6

    @property
    def is_full_rewrite(self) -> bool:
        context = self.context_tokens
        return (
            context >= REWRITE_MIN_CONTEXT and self.cache_write_tokens > REWRITE_FRACTION * context
        )


@dataclass
class _Partial:
    """A request under construction, before the last of its lines has been read."""

    model: str
    input_tokens: int
    cache_write_tokens: int
    cache_read_tokens: int
    output_tokens: int
    timestamp: datetime | None
    is_sidechain: bool


def _mapping(value: object) -> dict[str, object] | None:
    """A JSON object as a typed mapping, or `None` for anything else.

    `json.loads` returns `Any`, and letting that spread turns every downstream type into
    `Unknown` under pyright strict. Narrowing once here is what keeps the rest of the file typed.
    """
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    return None


def _decode(line: str) -> dict[str, object] | None:
    """One transcript line as a JSON object, or `None`.

    A transcript holds user turns, tool results and — when a session was killed mid-write — a
    truncated final line. Every one of those is a line to skip, not a crash: this tool's whole
    purpose is reading transcripts that other agents died in the middle of writing.
    """
    if not line.strip():
        return None
    try:
        return _mapping(json.loads(line))
    except ValueError:
        return None


def _int(mapping: dict[str, object], key: str) -> int:
    value = mapping.get(key)
    return value if isinstance(value, int) else 0


def _text(*candidates: object) -> str | None:
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def _parse_timestamp(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _read_lines(path: Path) -> list[str]:
    """Every line of a transcript, or none when it cannot be read.

    A transcript may be mid-write, on a disappeared volume, or simply absent; that is an empty
    answer, not a crash. Narrow, because a blind `except Exception` here would swallow the bugs
    this file exists to avoid.
    """
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def read_requests(path: Path) -> list[Request]:
    """Every request in one transcript, in the order it was first seen.

    The two format rules live here and nowhere else: the first line carrying a `requestId`
    establishes the request, and later lines may only ever raise `output_tokens`.
    """
    order: list[str] = []
    seen: dict[str, _Partial] = {}
    for line in _read_lines(path):
        record = _decode(line)
        if record is None:
            continue
        message = _mapping(record.get("message"))
        usage = _mapping(message.get("usage")) if message is not None else None
        if usage is None:
            continue
        request_id = _text(record.get("requestId"), record.get("uuid"))
        if request_id is None:
            continue
        partial = seen.get(request_id)
        if partial is None:
            order.append(request_id)
            model = _text(message.get("model") if message else None, record.get("model"))
            seen[request_id] = _Partial(
                model=model or "(unknown)",
                input_tokens=_int(usage, "input_tokens"),
                cache_write_tokens=_int(usage, "cache_creation_input_tokens"),
                cache_read_tokens=_int(usage, "cache_read_input_tokens"),
                output_tokens=_int(usage, "output_tokens"),
                timestamp=_parse_timestamp(record.get("timestamp")),
                is_sidechain=record.get("isSidechain") is True,
            )
        else:
            # The ONLY field a later line may change. Taking the first undercounts 1.7755x.
            partial.output_tokens = max(partial.output_tokens, _int(usage, "output_tokens"))
    return [
        Request(
            request_id=request_id,
            model=seen[request_id].model,
            input_tokens=seen[request_id].input_tokens,
            cache_write_tokens=seen[request_id].cache_write_tokens,
            cache_read_tokens=seen[request_id].cache_read_tokens,
            output_tokens=seen[request_id].output_tokens,
            timestamp=seen[request_id].timestamp,
            is_sidechain=seen[request_id].is_sidechain,
        )
        for request_id in order
    ]


def find_transcripts(root: Path, project: str | None, include_subagents: bool) -> list[Path]:
    """Main-loop transcripts, plus subagent and workflow-agent ones when asked for.

    A project is a directory under `root` whose name encodes the working directory it was started
    in; `project` matches a substring of that name, so `--project Pinakes` is enough.
    """
    if not root.is_dir():
        return []
    found: list[Path] = []
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or (project is not None and project not in directory.name):
            continue
        found.extend(sorted(directory.glob("*.jsonl")))
        if include_subagents:
            found.extend(sorted(directory.glob("*/subagents/*.jsonl")))
            found.extend(sorted(directory.glob("*/subagents/workflows/*/agent-*.jsonl")))
    return found


def command_models(paths: Sequence[Path], population: str) -> int:
    """Requests, price-units and estimated dollars per model.

    Units and dollars answer different questions and can disagree by a factor of two — a model
    that bills at 2x shows the same units and twice the cost.
    """
    requests: Counter[str] = Counter()
    units: defaultdict[str, float] = defaultdict(float)
    dollars: defaultdict[str, float] = defaultdict(float)
    unpriced: set[str] = set()
    for path in paths:
        for request in read_requests(path):
            requests[request.model] += 1
            units[request.model] += request.units
            usd = request.usd
            if usd is None:
                unpriced.add(request.model)
            else:
                dollars[request.model] += usd
    if not requests:
        print("no requests found — check --root and --project")
        return 1
    total_units = sum(units.values())
    total_usd = sum(dollars.values())
    print(f"{sum(requests.values()):,} requests over {len(paths):,} transcripts  [{population}]")
    print(f"{total_units:,.0f} price-units   ${total_usd:,.2f} estimated\n")
    for model in sorted(units, key=lambda name: units[name], reverse=True):
        share = units[model] / total_units * 100 if total_units else 0.0
        priced = f"${dollars[model]:>10,.2f}" if model in dollars else "  (no rate)"
        print(
            f"   {model:<22} {requests[model]:>7,} req  "
            f"{units[model]:>16,.0f} units  {share:>5.2f}%  {priced}"
        )
    if unpriced:
        print(f"\n   not on the rate card, excluded from dollars: {', '.join(sorted(unpriced))}")
    print("\n   dollars are an estimate from a cached rate card — see RATES_USD_PER_MTOK.")
    return 0


def command_boot(paths: Sequence[Path]) -> int:
    """The context a session sends on its FIRST request — the fixed cost of existing in a project.

    It is re-transmitted on every later request, so it is the one number that multiplies by
    session length without anybody choosing it.
    """
    rows: list[tuple[str, int, str]] = []
    for path in paths:
        requests = read_requests(path)
        if len(requests) < 2:
            continue
        first = requests[0]
        if first.is_sidechain or first.context_tokens == 0:
            continue
        stamp = first.timestamp.isoformat()[:16] if first.timestamp else "(undated)"
        rows.append((stamp, first.context_tokens, path.stem[:8]))
    if not rows:
        print("no session had a datable first request")
        return 1
    rows.sort()
    print(f"{len(rows)} sessions, oldest first  [main-loop sessions only]\n")
    for stamp, context, name in rows:
        print(f"  {stamp}  {context:>8,}  {name}")
    first_boot, last_boot = rows[0][1], rows[-1][1]
    change = (last_boot / first_boot - 1) * 100 if first_boot else 0.0
    print(f"\n  first {first_boot:,} -> latest {last_boot:,}   ({change:+.1f}%)")
    print("  Every request in a session re-reads this. A 50k boot over 100 requests is 500k units.")
    return 0


@dataclass
class _RunOutcomes:
    """One workflow run's agents, and the state each was left in."""

    agents: dict[str, str] = field(default_factory=dict[str, str])

    @property
    def orphans(self) -> int:
        return sum(1 for state in self.agents.values() if state == NO_OUTCOME)


def journal_outcomes(root: Path, project: str | None) -> dict[str, _RunOutcomes]:
    """`{workflow run: outcomes}`, where a state is result | failed | no-terminal-row.

    A `started` row with no later row is not proof an agent died — the workflow may still be
    running, or have been killed before the journal was flushed. It is proof the run recorded no
    outcome, which is what makes a resume re-run it.
    """
    outcomes: dict[str, _RunOutcomes] = {}
    if not root.is_dir():
        return outcomes
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or (project is not None and project not in directory.name):
            continue
        for journal in sorted(directory.glob("*/subagents/workflows/*/journal.jsonl")):
            run = outcomes.setdefault(journal.parent.name, _RunOutcomes())
            for line in _read_lines(journal):
                record = _decode(line)
                if record is None:
                    continue
                agent = _text(record.get("agentId"))
                kind = _text(record.get("type"))
                if agent is None or kind is None:
                    continue
                if kind == "started":
                    run.agents.setdefault(agent, NO_OUTCOME)
                else:
                    run.agents[agent] = kind
    return outcomes


def command_workflows(root: Path, project: str | None) -> int:
    """Workflow agent outcomes, and — the part that reframes them — how the losses are distributed.

    A flat percentage reads as a per-agent death rate. It is not one: the runs that lose agents
    tend to lose all of them at once, which is a killed workflow rather than a dying agent, and a
    different defect with a different fix.
    """
    outcomes = journal_outcomes(root, project)
    if not outcomes:
        print("no workflow journals found — check --root and --project")
        return 1
    tally: Counter[str] = Counter()
    for run in outcomes.values():
        tally.update(run.agents.values())
    total = sum(tally.values())
    if not total:
        print("workflow journals found, but no agent runs recorded")
        return 1
    orphans, failed = tally[NO_OUTCOME], tally["failed"]
    print(f"{len(outcomes)} workflow runs, {total:,} agent runs started\n")
    print(f"  {'result rows':<18} {tally['result']:>5}  ({tally['result'] / total * 100:>4.1f}%)")
    print(f"  {'failed rows':<18} {failed:>5}  ({failed / total * 100:>4.1f}%)")
    print(f"  {'NO terminal row':<18} {orphans:>5}  ({orphans / total * 100:>4.1f}%)")
    print(
        f"\n  produced no result: {orphans + failed} of {total} "
        f"({(orphans + failed) / total * 100:.1f}%) — the two figures answer different questions"
    )
    ranked = sorted(
        ((name, run.orphans, len(run.agents)) for name, run in outcomes.items() if run.orphans),
        key=lambda row: row[1],
        reverse=True,
    )
    clean = len(outcomes) - len(ranked)
    print(
        f"\n  {orphans} orphans sit in {len(ranked)} of {len(outcomes)} runs; "
        f"{clean} runs lost nothing"
    )
    print(f"\n  {'workflow run':<22} {'lost':>5} {'of':>5}")
    for name, lost, size in ranked[:10]:
        print(f"  {name:<22} {lost:>5} {size:>5}")
    if len(ranked) > 10:
        top_ten = sum(lost for _, lost, _ in ranked[:10])
        print(f"  ... {len(ranked) - 10} more runs; the ten above hold {top_ten} of {orphans}")
    print("\n  Losing every agent in a run at once is a killed workflow, not agents dying.")
    return 0


def _bucket(gap_seconds: float) -> str:
    for name, ceiling in GAP_BUCKETS:
        if gap_seconds < ceiling:
            return name
    return GAP_BUCKETS[-1][0]


def command_rewrites(paths: Sequence[Path], population: str) -> int:
    """Mid-session requests that re-wrote the whole cache, and what they cost above a cache read.

    A re-written token bills at 1.25x instead of 0.1x, so this is a 12.5x multiplier on whatever
    it touches. Bucketing by idle gap separates cache expiry — a session left sitting — from
    something that changed the prompt prefix while the session was actively working.
    """
    events: Counter[str] = Counter()
    excess: defaultdict[str, float] = defaultdict(float)
    total_units = 0.0
    request_count = 0
    for path in paths:
        previous: datetime | None = None
        for index, request in enumerate(read_requests(path)):
            total_units += request.units
            request_count += 1
            if index and request.is_full_rewrite and previous and request.timestamp:
                name = _bucket((request.timestamp - previous).total_seconds())
                events[name] += 1
                # What it cost ABOVE serving the same tokens from cache.
                excess[name] += request.cache_write_tokens * (
                    CACHE_WRITE_MULTIPLIER - CACHE_READ_MULTIPLIER
                )
            previous = request.timestamp or previous
    if not request_count:
        print("no requests found — check --root and --project")
        return 1
    total_events = sum(events.values())
    total_excess = sum(excess.values())
    share = total_excess / total_units * 100 if total_units else 0.0
    print(f"{request_count:,} requests, {total_units:,.0f} price-units  [{population}]\n")
    print(
        f"  {total_events} mid-session full cache re-writes "
        f"({total_events / request_count * 100:.2f}% of requests)"
    )
    print(f"  excess over a cache read: {total_excess:,.0f} units ({share:.2f}% of all spend)\n")
    print(f"  {'idle gap':>10}  {'events':>6}  {'excess units':>14}  share of excess")
    for name, _ in GAP_BUCKETS:
        if not events[name]:
            continue
        portion = excess[name] / total_excess * 100 if total_excess else 0.0
        print(f"  {name:>10}  {events[name]:>6}  {excess[name]:>14,.0f}  {portion:>5.1f}%")
    print("\n  Long gaps are cache expiry: close a session rather than leaving it parked.")
    print("  Short gaps are a prefix change mid-turn, and are NOT explained by idleness.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.home() / ".claude" / "projects",
        help="transcript root (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="only projects whose directory name contains this (e.g. Pinakes)",
    )
    parser.add_argument(
        "--scope",
        choices=("all", "main"),
        default="all",
        help=(
            "which transcripts to count: 'all' (default) includes subagent runs and workflow "
            "agents; 'main' is main-loop sessions only. `boot` is always main-loop -- a subagent's "
            "first request is not a session boot -- and says so in its output."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("models", "requests, price-units and estimated dollars per model"),
        ("boot", "the fixed context each session re-transmits on every request"),
        ("workflows", "workflow agent outcomes and how the losses are distributed"),
        ("rewrites", "mid-session full cache re-writes, by idle gap"),
    ):
        subparsers.add_parser(name, help=help_text)
    args = parser.parse_args(argv)
    root = cast("Path", args.root)
    project = cast("str | None", args.project)
    command = cast("str", args.command)
    scope = cast("str", args.scope)

    if command == "workflows":
        return command_workflows(root, project)

    # `boot` is main-loop by definition, so it opts out rather than silently reporting a population
    # nobody asked for -- 1,088 subagent transcripts would swamp 65 sessions.
    with_subagents = scope == "all" and command != "boot"
    paths = find_transcripts(root, project, include_subagents=with_subagents)
    if not paths:
        print(f"no transcripts under {root} (project filter: {project!r})", file=sys.stderr)
        return 1
    population = (
        "main loop + subagents + workflow agents" if with_subagents else "main-loop sessions only"
    )
    if command == "models":
        return command_models(paths, population)
    if command == "boot":
        if scope == "all":
            print("note: `boot` reads main-loop sessions only; --scope all does not apply to it\n")
        return command_boot(paths)
    return command_rewrites(paths, population)


if __name__ == "__main__":
    raise SystemExit(main())
