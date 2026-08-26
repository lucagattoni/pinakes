"""Every review pass starts from zero. This reconstructs what the earlier ones already did.

**The measurement, over the subagent transcripts on this machine: 910 of them, 5.14B raw tokens,
newest 20260826 11:32 UTC.** That stamp is not decoration — the corpus is live, other sessions write
into it while this runs, and `--measure` prints `transcripts_read` and `newest_transcript` for the
same reason a measurement against a working tree needs a sha. Adversarial review is the largest
single category of that spend — **43.9% by this tool's classifier (469 runs, 2.26B tokens)**,
independently reproducing the 44.0% the retrospective reached by clustering task titles by hand.
Inside it, later passes repeat earlier ones. **Every figure below is what `--measure` prints**,
under the key named beside it, so none of it has to be believed:

- **95.8%** `files_already_opened_median_pct` — of the files a later pass opens, an earlier pass
  over the same increment had already opened. Median, not mean; it read 100% until this tool
  learned to see `Makefile` and `uv.lock`.
- **35.6%** `repeat_share_pct` — of a later pass's raw tokens go to turns whose *only* file access
  was one of those already-opened files.
- 3.0% `new_share_pct` — the same, for its turns that opened a repository file no earlier pass had.
- **40.1%** `repeat_share_over_5m_pct` — the repeat share over the 69 passes that cost more than
  5M raw tokens each. Median per pass, `repeat_share_median_over_5m_pct`, 39.1%.
- 305 `later_passes` over 20 `increments`, 1.12B raw tokens — the population. It read 281 over
  19 until the turn floor stopped hiding passes that were killed early.

**Re-derivation is not the cheap part of a review pass; it is the part that scales** — the share
rises with how expensive the pass is, because a re-read early in a long pass is re-transmitted by
every turn after it. It survived every cut it was given: the long tail of per-finding refuters, the
ordinal-2-to-4 head, passes separated by more than two hours, passes of forty turns or more.
`--measure` exists because **a number in a docstring is a claim with no way to check it** —
`tools/review_pass_gate.py` shipped with three that were wrong and nothing in the repository could
see it. Every figure above moved at least once during this tool's own build and its two
adversarial passes, as five defects in it were fixed; they moved *here* because re-running one
command is what updating them costs.

**What a pass re-derives is not mainly file content.** Read the tool calls rather than counting
them: reviewers here overwhelmingly *run* things — their own detached worktree, their own scratch
KB, `pytest` in it, a throwaway probe script, then `git worktree remove`. Each pass builds that
setup from nothing and destroys it. On one increment, seventeen separate passes wrote and ran
`uv run --frozen pytest tests/test_pairing.py`, and seven independently discovered that `timeout`
is not installed on this machine. So the carry that matters is **the probes**, and this tool leads
with them.

**And the gap is worth more than it looks, which took two measurements to find out.** "Point the
next pass at the changed files nobody has opened" was going to be dropped on a first pass at the
number — 92%, near-total coverage, nothing to say. Re-derived after two defects below were fixed —
the path normalisation, and a scan that could not see an extensionless filename — it is **211 of
248 changed files opened (85%), and 92% on multi-pass increments**.
What goes unopened is not noise: `src/pinakes/__init__.py` — where `__version__` lives — was never
opened across the **41** passes over `20260823_0718-mutation-batteries`, and no pass in this corpus
has ever opened the `changelog.d/` or `retro.d/` fragment its own increment wrote. That section is
last in the brief and it is the only one that names a gap rather than a summary. (This figure needs
git history and is *not* re-derivable by `--measure`; the brief recomputes the per-increment half of
it every time it runs.)

**Why it reads transcripts instead of asking passes to write a ledger.** A convention every pass
must remember is a convention some pass forgets, and this repository's own record is that the
forgetting is silent. The transcripts are already on disk, they record what a pass *did* rather than
what it says it did, and they survive the agent — a pass that died on a usage limit still has its
probes here. Nothing has to cooperate.

**What this is not, and the tool prints all three every time.**

- **Opened is not reviewed.** The map says where attention went. It never says the attention was
  enough, and a later pass that treats a listed file as covered has been made *worse* by this tool.
- **A quoted command's exit status is not recoverable.** The transcript stores what a command
  printed, not what it returned. So probes are shown with their output, never with a verdict — the
  distinction this repository already enforces in the other direction (`CLAUDE.md`: *a gate is only
  a gate when its exit status is what the next command reads*).
- **A quoted finding is the claim of the pass that made it.** Passes 1 to 4 over one increment found
  30, 22, 13 and 6 issues; nothing here says which survived.

**Incomplete passes come first, above everything else.** A pass that died mid-run, or returned
nothing, contributed *some* of the map — and a brief that lists its files without saying it never
finished tells the next pass the ground has been covered when it has not. That is the failure
`tools/review_pass_gate.py` exists for, one layer up: there, an empty fan-out reads as a clean bill;
here, a partial pass reads as coverage. Exit `1` says the brief is real but the coverage it implies
is overstated.

    python3 tools/review_ledger.py 20260825_1828-cheap-closes     # brief for the next pass
    python3 tools/review_ledger.py --list                         # increments with passes on disk
    python3 tools/review_ledger.py <increment> --json             # for a script
    python3 tools/review_ledger.py --measure                      # re-derive the table above

`0` — brief produced, every earlier pass completed. `1` — brief produced, at least one pass did not
finish, so read the incomplete section before trusting the map. `2` — nothing on disk for that
increment; the next pass genuinely does start from zero.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

PROJECTS: Final = Path.home() / ".claude" / "projects"
"""Where every session's subagent transcripts live, one directory per project."""

INCREMENT: Final = re.compile(r"\d{8}_\d{4}-[A-Za-z0-9][A-Za-z0-9._-]*")
"""A branch or plan name in a brief — this repository's `YYYYMMDD_HHMM-name` convention.

The first one a brief mentions is the increment it is about. Trailing `.` and `.md` are stripped:
a brief citing `plans/20260825_1240-run-pinakes-sweep.md` and one citing the branch of the same
name are about the same work, and grouping them apart hides exactly the repetition being measured.
"""

REVIEWER: Final = re.compile(
    r"adversarial|adversarially|skeptical|devil'?s advocate|refute|"
    r"review pass|code review|reviewer|you are reviewing|review of",
    re.I,
)
IMPLEMENTER: Final = re.compile(
    r"implementing coder|you are a coding agent|you are the implementer|build \*\*increment|"
    r"apply .{0,40}fixes|you are drafting|you are revising|you are folding|you are authoring|"
    r"you are building",
    re.I,
)
"""Role, from the opening of a brief — and the `IMPLEMENTER` half is the load-bearing one.

**A keyword classifier over agent briefs counts the repository's own instructions.** `CLAUDE.md`
tells every implementer to "adversarially review" its own work, so matching `review` alone labels
coder agents as reviewers — and coder agents cost far more per turn, which silently inflated every
derived ratio in the measurement that preceded this tool. Matching the *role sentence* a brief opens
with, and subtracting implementer voice, is the repair.

Precision over recall, deliberately: a missed reviewer costs one absent section of a brief, while a
misfiled coder puts the work under review into the evidence for reviewing it.
"""

HEAD: Final = 400
"""Characters of a brief the classifier reads. A brief states its role in its first sentence."""

READS: Final = re.compile(r"\b(cat|sed|head|tail|less|grep|rg|awk|wc)\b|git show|git diff|git log")
PATHISH: Final = re.compile(r"[\w./@+-]*[/.][\w./@+-]+")
SUFFIXES: Final = (
    ".py",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".sh",
    ".json",
    ".jsonl",
    ".cfg",
    ".ini",
    ".txt",
    ".lock",
    ".pyi",
)
"""Extensions that make a token in a shell command worth testing as a path.

**`.lock` and an extensionless name were missing, and that turned a detection gap into a finding.**
`cat uv.lock` and `sed -n '1,5p' Makefile` matched nothing, so both files were reported under
*changed by this increment, opened by nobody* on every increment that touched them —
indistinguishable from a file nobody read. A gap section whose gaps include *what this tool
cannot see* is worse than no gap section: it is confidently wrong about the one thing it exists to
say. Extensionless root files are matched by name below.
"""

TOP: Final = (
    "src/",
    "tests/",
    "tools/",
    "docs/",
    "plans/",
    "stubs/",
    "changelog.d/",
    "retro.d/",
    ".github/",
)
ROOT_FILES: Final = frozenset(
    {
        "pyproject.toml",
        "CLAUDE.md",
        "README.md",
        "CHANGELOG.md",
        "Makefile",
        "check.sh",
        "mkdocs.yml",
        "mkdocs_hooks.py",
        "uv.lock",
    }
)
"""What a repository-relative path starts with. Normalisation anchors here, not on the repo name.

**The first version anchored on the repository's own name and was wrong in a way that silently
corrupted the measurement.** Stripping through `/pinakes/` matches the *package* directory as
readily as the checkout, so `src/pinakes/sync.py` normalised to `sync.py` — which then collided
with every other `sync.py` on disk, including the ones inside a reviewer's throwaway scratch KB.
Overlap between passes read higher than it was, in the tool built to measure overlap.

Anchoring on the top-level directory instead is also the only form that survives where reviewers
actually work: `Pinakes-worktrees/<branch>/`, `pinakes-wt/<branch>/`, `Pinakes-i4/` and a detached
clone at `/tmp/s2rev-fpx/` all appear in one week of transcripts, and all four must reduce to the
same path or two passes reading one file look like two passes reading two.

A path matching nothing here is not a file in this repository — a scratch KB's `a.md`, a temporary
JSON dump — and is dropped. Those are real work and often repeated work, but they are not shared
ground, and counting them as such is what the bug above did.
"""


@dataclass
class Probe:
    """One command an earlier pass ran, and the first thing it printed."""

    command: str
    output: str
    pass_number: int


@dataclass
class Pass:
    """One review agent's run over one increment, as its own transcript records it."""

    agent_id: str
    started: str
    tokens: int = 0
    brief: str = ""
    files: list[str] = field(default_factory=list[str])
    probes: list[Probe] = field(default_factory=list[Probe])
    report: str = ""
    ended_cleanly: bool = False
    killed: str = ""
    """The harness's own reason, when the run ended in an API error rather than in the agent.

    **A killed agent's last message reads exactly like a report.** `"You've hit your session limit ·
    resets 11:40pm"` arrives as assistant text, and a first version of this tool quoted it under
    *what each pass reported* for four consecutive passes over one increment — presenting four
    deaths as four conclusions, which is the failure `tools/review_pass_gate.py` exists for wearing
    a different coat. The transcript is unambiguous where the text is not: the record carries
    `error` and `isApiErrorMessage`, so this is read structurally and never by matching the prose.
    """
    context: list[int] = field(default_factory=list[int])
    """Per assistant turn: the input plus cache-creation plus cache-read the API was handed.

    Measured, never estimated. This is the whole basis of `--measure`, and it is why a chars-per-
    token guess appears nowhere in this file: an earlier attempt at the same measurement modelled
    context from message lengths and reconstructed 12% of the real bill, because the system prompt
    and tool schemas are re-sent every turn and appear in no message.
    """
    turn_files: list[list[str]] = field(default_factory=list[list[str]])
    """Per assistant turn: the repository files that turn opened. Parallel to `context`."""

    @property
    def turns(self) -> int:
        return len(self.context)

    def cost_split(self, seen: set[str]) -> tuple[float, float, float]:
        """This pass's raw tokens, and how they divide between ground already walked and new.

        A turn's growth in context is what that turn added, and it is re-transmitted on every later
        turn — so its cost is the growth times the turns remaining, not the growth. That weighting
        is the reason the share rises with how expensive a pass is: a re-read early in a long pass
        is paid for by every turn after it.

        `raw` here is the same total the brief prints for the pass — context plus output, one
        denominator. It excluded output until this tool's own adversarial pass: 0.5% of the bill,
        and a second denominator in a report whose subject is ratios. That exact defect is the one
        the retrospective this tool came from rated HIGH.

        A turn counts as **repeat** only when *every* file it opened was already opened by an
        earlier pass. That is deliberately the generous reading — a turn that re-opens a known file
        to check something genuinely new is counted as repeat here — which makes the resulting share
        a ceiling on what a carry-forward could recover, never a floor.
        """
        raw = float(self.tokens)
        repeat = new = 0.0
        for index in range(self.turns):
            if index + 1 >= self.turns:
                break  # the final turn's growth is re-transmitted to nothing
            growth = max(self.context[index + 1] - self.context[index], 0)
            weight = float(growth * (self.turns - index - 1))
            opened = self.turn_files[index] if index < len(self.turn_files) else []
            if not opened:
                continue
            if all(path in seen for path in opened):
                repeat += weight
            else:
                new += weight
        return raw, repeat, new

    @property
    def incomplete(self) -> str | None:
        """Why this pass's contribution to the map is partial, or `None` if it is not.

        Two shapes, and they need saying apart. A pass that never reached a final message died —
        its files were opened and its probes did run, so the evidence is real and the *conclusion*
        is missing. A pass that finished and said nothing is the quieter one: it looks like a clean
        bill and re-running it from cache reproduces the silence.
        """
        if self.killed:
            return f"KILLED by the harness ({self.killed}) — its probes ran, it never concluded"
        if not self.ended_cleanly:
            return "died before a final message — its probes ran, its conclusion is missing"
        if not self.report.strip():
            return "completed and reported nothing — silence, not a clean bill"
        return None


def tracked_files() -> frozenset[str]:
    """Every path git tracks here, or an empty set when that cannot be answered.

    **A reviewer's throwaway KB has a `docs/` directory too.** Every pass over one increment built
    a scratch knowledge base and read `docs/a.md` out of it; anchoring on the top-level directory
    alone put that in the map as repository ground, seventeen passes deep, and counted seventeen
    *different* files as one. Asking git is the only authority that separates them.

    An empty answer — no git, a checkout without history, a test fixture — means the caller keeps
    every top-level-anchored path instead. Degrading to the looser rule is right: a map with some
    scratch paths in it is worth more than no map, and the brief says which mode it ran in.

    **Only `docs/` is checked against this, and the narrowness is the point.** `git ls-files` is
    today's tree, so screening every path through it would silently drop any file an old increment
    reviewed and a later one deleted — losing real history to fix a problem that has one shape.
    A scratch KB is a `docs/` directory of prose; it has no `src/pinakes/` and no `tests/`.
    """
    try:
        listed = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=False, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return frozenset()
    if listed.returncode != 0:
        return frozenset()
    return frozenset(line for line in listed.stdout.splitlines() if line)


def _is_repository_file(path: str, tracked: frozenset[str]) -> bool:
    """Whether a normalised path names a file of this repository rather than a reviewer's scratch.

    See `tracked_files` for why only `docs/` is screened.
    """
    if not path:
        return False
    if path.startswith("docs/") and tracked:
        return path in tracked
    return True


def changed_files(increment: str) -> list[str]:
    """What the increment changed, from its branch if it is live and its merge commit if it landed.

    Empty when git cannot answer — an increment named after a plan rather than a branch, a
    repository without the history, a landing whose merge message was written by hand. The section
    it feeds is then omitted rather than shown empty, because "no unopened files" and "nobody asked"
    are different claims and only one of them is true.
    """

    def git(*args: str) -> str:
        try:
            done = subprocess.run(
                ["git", *args], capture_output=True, text=True, check=False, timeout=30
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        return done.stdout.strip() if done.returncode == 0 else ""

    if git("rev-parse", "--verify", "--quiet", increment):
        listed = git("diff", "--name-only", f"origin/main...{increment}")
        if listed:
            return listed.splitlines()
    merge = git(
        "log", "--all", "--merges", "--format=%H", f"--grep=Merge branch '{increment}'", "-1"
    )
    if not merge:
        return []
    return [
        line for line in git("diff", "--name-only", f"{merge}^1...{merge}^2").splitlines() if line
    ]


def _normalise(path: str) -> str:
    """Reduce any spelling of a repository file to its repository-relative path, or `""`.

    The **earliest** occurrence of a top-level directory wins, because what is being removed is the
    checkout prefix and the repository-relative path begins at the first marker after it.

    **This was `rfind` — last wins — until a surviving mutant made the case for it.** The reasoning
    was that a branch directory could contain `docs`, so the later match must be the real one. It
    cannot: a branch is `20260807_2143-docs-audit-findings`, where `docs` is bounded by hyphens and
    never by slashes, so the marker `/docs/` does not match it at all. What last-wins *did* match
    was the committed corpora — `tests/demo-kb/docs/access-restrictions.md` reduced to
    `docs/access-restrictions.md`, which is not a file, and the `docs/` screen below then discarded
    it. **102 tracked paths nest a top-level name that way.**

    Measured rather than asserted, because the two are not the same size: over the 49,000 read
    targets in this corpus, **28 normalise differently and 27 of those are recovered** — the shares
    `--measure` prints do not move at all. The defect was silent, real, and small. It is written up
    at this length because the *class* is neither: a path rule that quietly discards a file
    produces a map that is wrong only about what nobody looked at, which is the one thing a later
    pass reads this tool to learn.
    """
    path = path.strip().strip("'\"`,;()[]")
    if not path:
        return ""
    best = -1
    for marker in TOP:
        if path.startswith(marker):
            best = 0
            break
        found = path.find("/" + marker)
        if found != -1 and (best == -1 or found < best):
            best = found
    if best > 0:
        return path[best + 1 :]
    if best == 0:
        return path
    return path.rsplit("/", 1)[-1] if path.rsplit("/", 1)[-1] in ROOT_FILES else ""


def _text(content: object) -> str:
    """The text of a message, whatever shape the transcript stored it in."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in cast(list[object], content):
            if isinstance(block, dict):
                value = cast(dict[str, object], block).get("text")
                if isinstance(value, str):
                    parts.append(value)
        return "".join(parts)
    return ""


def _lines(path: Path) -> list[dict[str, object]]:
    """Parse a JSONL transcript, skipping any line that will not.

    A truncated final line is the normal state of a transcript belonging to an agent that was
    killed — the case this tool most wants to read — so a parse error must never be fatal.
    """
    out: list[dict[str, object]] = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            loaded: object = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(loaded, dict):
            out.append(cast(dict[str, object], loaded))
    return out


def _paths_in(name: str, payload: dict[str, object], tracked: frozenset[str]) -> list[str]:
    """Every repository file a single tool call opened."""
    if name == "Read":
        target = payload.get("file_path")
        found = _normalise(target) if isinstance(target, str) else ""
        return [found] if _is_repository_file(found, tracked) else []
    if name != "Bash":
        return []
    command = payload.get("command")
    if not isinstance(command, str) or not READS.search(command):
        return []
    # A root file may have no extension at all — `Makefile`. `PATHISH` needs a `/` or a `.` to
    # match, so those are found by scanning words rather than path-shaped tokens.
    tokens = [t for t in cast(list[str], PATHISH.findall(command)) if t.endswith(SUFFIXES)]
    tokens += [
        w.strip("'\"`,;()[]") for w in command.split() if w.strip("'\"`,;()[]") in ROOT_FILES
    ]
    opened = [_normalise(token) for token in tokens]
    return [path for path in opened if _is_repository_file(path, tracked)]


def read_pass(transcript: Path, tracked: frozenset[str] = frozenset()) -> Pass | None:
    """Reconstruct one review pass from its transcript, or `None` if it was not one.

    Returns `None` for an implementer, for a run with no brief, and for a run too short to have
    done anything — five assistant turns is below the cost of starting up.
    """
    records = _lines(transcript)
    if not records:
        return None

    brief = ""
    for record in records:
        if record.get("type") != "user":
            continue
        message = record.get("message")
        if isinstance(message, dict):
            found = _text(cast(dict[str, object], message).get("content"))
            if found.strip():
                brief = found
                break
    opening = " ".join(brief.split())[:HEAD]
    if not opening or IMPLEMENTER.search(opening) or not REVIEWER.search(opening):
        return None

    agent_id = transcript.stem.removeprefix("agent-")
    started = ""
    for record in records:
        stamp = record.get("timestamp")
        if isinstance(stamp, str) and stamp:
            started = stamp
            break
    result = Pass(agent_id=agent_id, started=started, brief=brief)

    pending: dict[str, str] = {}  # tool_use id -> the command, awaiting its output
    order: list[str] = []  # every Bash id in call order, so an unanswered one is still recoverable
    for record in records:
        kind = record.get("type")
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        body = cast(dict[str, object], message)

        if kind == "assistant":
            handed = 0
            usage = body.get("usage")
            if isinstance(usage, dict):
                for field_name in (
                    "input_tokens",
                    "cache_creation_input_tokens",
                    "cache_read_input_tokens",
                ):
                    count = cast(dict[str, object], usage).get(field_name)
                    if isinstance(count, int):
                        handed += count
                produced = cast(dict[str, object], usage).get("output_tokens")
                if isinstance(produced, int):
                    result.tokens += produced
            result.context.append(handed)
            result.tokens += handed
            opened_this_turn: list[str] = []
            result.turn_files.append(opened_this_turn)
            content = body.get("content")
            if not isinstance(content, list):
                continue
            failure = record.get("error")
            if record.get("isApiErrorMessage") is True or (isinstance(failure, str) and failure):
                result.killed = failure if isinstance(failure, str) and failure else "api error"
                result.ended_cleanly = False
                continue
            spoken = _text(cast(list[object], content))
            if spoken.strip():
                result.report = spoken
                result.ended_cleanly = True
                result.killed = ""  # an error the harness retried past is not how the run ended
            for raw in cast(list[object], content):
                if not isinstance(raw, dict):
                    continue
                block = cast(dict[str, object], raw)
                if block.get("type") != "tool_use":
                    continue
                name, payload = block.get("name"), block.get("input")
                if not isinstance(name, str) or not isinstance(payload, dict):
                    continue
                fields = cast(dict[str, object], payload)
                found_paths = _paths_in(name, fields, tracked)
                result.files.extend(found_paths)
                opened_this_turn.extend(found_paths)
                command = fields.get("command")
                identifier = block.get("id")
                if name == "Bash" and isinstance(command, str) and isinstance(identifier, str):
                    pending[identifier] = " ".join(command.split())
                    order.append(identifier)

        elif kind == "user":
            content = body.get("content")
            if not isinstance(content, list):
                continue
            for raw in cast(list[object], content):
                if not isinstance(raw, dict):
                    continue
                block = cast(dict[str, object], raw)
                if block.get("type") != "tool_result":
                    continue
                identifier = block.get("tool_use_id")
                if isinstance(identifier, str) and identifier in pending:
                    output = " ".join(_text(block.get("content")).split())
                    result.probes.append(Probe(pending.pop(identifier), output, 0))

    # **A command whose result never came back is the most interesting one a killed pass ran.**
    # It is the call the agent was still inside when the harness stopped it, and pairing probes to
    # their results alone dropped it silently. Thirteen of twenty-four passes over one real
    # increment were killed, so this is the common case here rather than the edge.
    for identifier in order:
        if identifier in pending:
            result.probes.append(Probe(pending[identifier], "", 0))

    # **A killed run is kept however short it is.** The five-turn floor exists to drop runs that
    # did nothing — but a pass that died in its third turn *is* the population the incomplete
    # section reports, and dropping it makes "13 of 24 did not finish" read as a smaller number
    # against a smaller denominator. The filter must not be able to improve the statistic it feeds.
    return result if result.turns >= 5 or result.killed else None


def increment_of(brief: str) -> str:
    """The increment a brief is about — the first `YYYYMMDD_HHMM-name` it names."""
    found = INCREMENT.search(brief)
    if not found:
        return ""
    return found.group(0).rstrip(".").removesuffix(".md")


def _when(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=UTC)


def transcripts(projects: Path | None = None) -> list[Path]:
    """Every subagent transcript for this project, at either depth the harness writes.

    Direct subagents land in `<session>/subagents/`; a `Workflow` fan-out's agents land one
    directory deeper under `workflows/<run id>/`. **The deeper one is 80% of them here** (732 of
    910), and a glob written for the shallow layout alone finds a fifth of the corpus while looking
    entirely healthy — the same near-miss `tools/review_pass_gate.py` records against its own
    discovery.
    """
    if projects is not None:
        return sorted(projects.rglob("subagents/**/agent-*.jsonl")) if projects.is_dir() else []
    if not PROJECTS.is_dir():
        return []
    # The harness names a project directory after the *session's* working directory, so this
    # repository owns several: one for the primary checkout and one per worktree a session was
    # started in. All of them carry this repository's name, and none of any other project's do.
    name = _repository_name().lower()
    found: list[Path] = []
    for directory in PROJECTS.iterdir():
        if directory.is_dir() and name in directory.name.lower():
            found.extend(directory.rglob("subagents/**/agent-*.jsonl"))
    return sorted(found)


def _repository_name() -> str:
    """The *primary* checkout's directory name, from wherever this is run.

    A worktree is the normal place to run this — every change here is made in one — and a
    worktree's own directory is named for the branch, not the repository. Its `.git` is a file
    reading `gitdir: /path/to/Pinakes/.git/worktrees/<branch>`, so the primary checkout's name is
    recoverable without shelling out to git. Getting this wrong is silent: the glob matches no
    project directory and the tool reports that the next pass starts from zero, which is precisely
    the wrong answer to give confidently.
    """
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        marker = candidate / ".git"
        if marker.is_dir():
            return candidate.name
        if marker.is_file():
            pointer = marker.read_text(errors="replace").strip()
            if pointer.startswith("gitdir:"):
                target = pointer.split(":", 1)[1].strip()
                head, sep, _ = target.partition("/.git/")
                if sep:
                    return Path(head).name
            return candidate.name
    return here.name


def collect(
    projects: Path | None = None, tracked: frozenset[str] | None = None
) -> dict[str, list[Pass]]:
    """Every review pass on disk, grouped by increment and ordered oldest first."""
    known = tracked_files() if tracked is None else tracked
    grouped: dict[str, list[Pass]] = {}
    for transcript in transcripts(projects):
        found = read_pass(transcript, known)
        if found is None:
            continue
        name = increment_of(found.brief)
        if name:
            grouped.setdefault(name, []).append(found)
    for passes in grouped.values():
        passes.sort(key=lambda p: _when(p.started))
        for number, entry in enumerate(passes, start=1):
            for probe in entry.probes:
                probe.pass_number = number
    return grouped


SCRATCH: Final = re.compile(r"(/private)?/tmp/[\w.-]+|/Users/[^/\s]+/[\w./-]*?[Pp]inakes[\w.-]*")
"""A directory a pass worked in. Replaced by a placeholder before two commands are compared.

**Without this the deduplication does nothing.** Every reviewer builds its own isolated copy —
`/tmp/s2rev-fpx`, `/tmp/p2-skeptic-quokka`, `/tmp/p2-zircon-marmot-77` — so the same probe run by
six passes is six distinct strings. Measured on one increment before this existed: 891 probes, 880
of them "distinct", and the ranking that was supposed to surface the most-repeated work degenerated
into insertion order.
"""

RUNS: Final = re.compile(
    r"\bpytest\b|\bpython3?\b|\bpnk\b|\bpinakes\b|\bruff\b|\bpyright\b|\bmake\b|\buv\b"
)
SCRIPTS: Final = re.compile(r"check\.sh|mutate\.py|_gate\.py|tools/\w+\.py")
"""A command that *executes* the project rather than reading it.

These rank first, because they are what a later pass actually rebuilds. Reading the tool calls
rather than counting them is what showed it: across 62 review runs on three increments, 340 pytest
invocations, 304 throwaway probe scripts, 48 CLI runs and 14 mutation runs against ~150 file reads
— each pass standing up its own worktree and scratch KB, and tearing it down. The file map below
already carries the reading; this section is for the running.
"""

NOT_EVIDENCE: Final = re.compile(
    r"^(cd \S+$|ls\b|pwd$|echo\b|mkdir\b|rm\b|git (status|worktree (add|remove|list)|stash)\b|"
    r"date\b|cp\b|mv\b|which\b|export\b|source\b)"
)


def _interesting(command: str) -> bool:
    """Whether a command is worth carrying to the next pass.

    Housekeeping is not evidence. `cd`, `ls`, `git status` and worktree setup and teardown are what
    a pass does to get *to* the work, and a brief that leads with forty of them buries the six
    probes that are the reason for reading it at all.
    """
    bare = command.strip()
    if not bare or len(bare) < 12:
        return False
    return not NOT_EVIDENCE.match(bare)


def _shape(command: str) -> str:
    """A command with the pass's own scratch directories removed, for comparing two of them."""
    return SCRATCH.sub("<dir>", command).strip()


def _executes(command: str) -> bool:
    """Whether a command runs the project, as against reading a file out of it.

    **Paths are stripped before the verbs are matched, and the first version did not do it.**
    `pinakes` is the package directory as well as the command, so `sed -n '1,120p'
    src/pinakes/pairing.py` classified as *executing* — and with it 586 of 762 probes on one
    increment, which put the reading it was meant to demote at the top of the list instead.
    """
    return bool(RUNS.search(PATHISH.sub(" ", command)) or SCRIPTS.search(command))


def brief_for(name: str, passes: list[Pass], width: int = 100) -> tuple[list[str], int]:
    """Render the carry-forward brief, and the exit status that goes with it."""
    out: list[str] = []
    total = sum(p.tokens for p in passes)
    out.append(f"{len(passes)} earlier review pass(es) over {name}, {total:,} raw tokens spent.")
    out.append("")
    out.append("READ THIS FIRST — three things this brief is not:")
    out.append("  * A file listed as opened was OPENED, never reviewed. Coverage is not here.")
    out.append("  * A probe is shown with what it PRINTED. Exit status is not in the transcript.")
    out.append(
        "  * A finding is the CLAIM of the pass that made it. Nothing here says it survived."
    )
    out.append("")

    partial = [(n, p) for n, p in enumerate(passes, start=1) if p.incomplete]
    if partial:
        out.append(f"!! {len(partial)} of {len(passes)} pass(es) did NOT finish. The map below")
        out.append("!! therefore claims more ground than anyone actually covered:")
        for number, entry in partial:
            out.append(f"     pass {number} ({entry.agent_id[:12]}): {entry.incomplete}")
        out.append("")

    probes = [p for entry in passes for p in entry.probes if _interesting(p.command)]
    shapes = Counter(_shape(p.command) for p in probes)
    if probes:
        # Runs before reads, then most-repeated first. The count is passes that wrote this probe,
        # which is what it cost to have it; the file map below already carries the reading.
        first: dict[str, Probe] = {}
        for probe in probes:
            first.setdefault(_shape(probe.command), probe)
        ranked = sorted(
            first.items(),
            key=lambda kv: (0 if _executes(kv[0]) else 1, -shapes[kv[0]], kv[0]),
        )
        executing = sum(1 for shape in first if _executes(shape))
        out.append(f"PROBES ALREADY RUN — {len(probes)} calls, {len(shapes)} distinct, {executing}")
        out.append("of them executing the project rather than reading it. Re-run one rather than")
        out.append("rebuilding it; [n passes] is how many have already paid to write it.")
        out.append("<dir> is each pass's own scratch copy — substitute yours. A line ending [CUT]")
        out.append("is NOT runnable as shown; --json carries it whole:")
        for shape, sample in ranked[:25]:
            count = shapes[shape]
            marker = f" [{count} passes]" if count > 1 else f" [pass {sample.pass_number}]"
            cut = " [CUT]" if len(shape) > width else ""
            out.append(f"  $ {shape[:width]}{cut}{marker}")
            if sample.output:
                out.append(f"      -> {sample.output[:width]}")
            elif sample.pass_number:
                out.append("      -> (no result — the pass was stopped inside this command)")
        if len(ranked) > 25:
            out.append(
                f"  ... {len(ranked) - 25} more distinct probe(s) not shown (--json has all)"
            )
        out.append("")

    opened = Counter(f for entry in passes for f in set(entry.files) if f)
    if opened:
        out.append(
            f"FILES ALREADY OPENED ({len(opened)}) — the count is how many passes opened it,"
        )
        out.append("which is how much of this ground has been walked, not how well:")
        for path, count in opened.most_common(30):
            out.append(f"  {count:2d}x  {path}")
        out.append("")

    unopened = [path for path in changed_files(name) if path not in opened]
    if unopened:
        out.append(f"CHANGED BY THIS INCREMENT, OPENED BY NOBODY ({len(unopened)}) — the only")
        out.append("section here that is a gap rather than a summary:")
        for path in unopened:
            out.append(f"  {path}")
        out.append("")

    out.append("WHAT EACH PASS REPORTED — claims, not conclusions:")
    for number, entry in enumerate(passes, start=1):
        stamp = entry.started[:16].replace("T", " ")
        out.append(
            f"  --- pass {number}  {stamp}  {entry.turns} turns  {entry.tokens:,} tokens ---"
        )
        why = entry.incomplete
        if why:
            out.append(f"      INCOMPLETE: {why}")
        body = " ".join(entry.report.split())
        # For a pass that never concluded this is the last thing it said mid-run, not a report.
        # Worth keeping — it names what the pass was doing when it stopped — but not worth
        # presenting as a finding, which is the whole distinction this section exists to hold.
        label = "      LAST WORDS: " if why else "      "
        out.append(f"{label}{body[:600] if body else '(nothing)'}")
    return out, (1 if partial else 0)


def measure(projects: Path | None = None) -> dict[str, float]:
    """Re-derive the docstring's table from the transcripts, so the numbers can be checked.

    The cost model, stated so it can be attacked. For each turn `t` of a pass, `context[t]` is the
    input plus cache-creation plus cache-read the API was handed — measured, never estimated. The
    growth `context[t+1] - context[t]` is what turn `t` added, and it is re-transmitted on every
    later turn, so its cost is that growth times the turns remaining. A turn is **repeat** when
    every file it opened had already been opened by an earlier pass over the same increment, and it
    opened at least one; **new** when it opened something no earlier pass had.

    **The corpus is live, and the result carries its own provenance for that reason.** Other
    sessions write subagent transcripts into the same directory while this runs, so two invocations
    minutes apart legitimately differ — `files_already_opened_median_pct` moved 96.1 to 95.8 during
    one editing pass here, with no code change between them. `transcripts_read` and
    `newest_transcript` are the corpus's version stamp: **a figure from this command means nothing
    without them**, exactly as a figure measured against a working tree means nothing without a sha.

    Concurrent members of one fan-out are excluded from the headline: they start within minutes of
    each other and cannot carry anything forward, whatever this tool does. They are counted
    separately because they are the case a *shared* brief helps and a sequential carry does not.

    **Two of these keys have different populations, which is stated here because a reader will
    otherwise assume one.** `repeat_share_pct`, `new_share_pct` and the two `over_5m` keys are
    **sequential later passes only**. `files_already_opened_median_pct` is over **every** later
    pass, concurrent ones included — it asks what a pass found already opened, which is a fact about
    the increment whether or not anything could have carried it.
    """
    seen_transcripts = transcripts(projects)
    newest = 0.0
    for path in seen_transcripts:
        try:
            newest = max(newest, path.stat().st_mtime)
        except OSError:
            continue
    grouped = collect(projects)
    sequential_raw = sequential_repeat = sequential_new = 0.0
    concurrent_raw = concurrent_repeat = 0.0
    expensive_raw = expensive_repeat = 0.0
    per_pass: list[float] = []
    per_expensive_pass: list[float] = []
    overlaps: list[float] = []
    increments = later = 0

    for passes in grouped.values():
        if len(passes) < 2:
            continue
        increments += 1
        seen: set[str] = set()
        first = _when(passes[0].started)
        for number, entry in enumerate(passes):
            files = {f for f in entry.files if f}
            if number and files:
                overlaps.append(100.0 * len(files & seen) / len(files))
            if number:
                gap = (_when(entry.started) - first).total_seconds() / 60.0
                raw, repeat, fresh = entry.cost_split(seen)
                if gap > 5.0:
                    later += 1
                    sequential_raw += raw
                    sequential_repeat += repeat
                    sequential_new += fresh
                    if raw:
                        per_pass.append(100.0 * repeat / raw)
                    if raw >= 5_000_000:
                        expensive_raw += raw
                        expensive_repeat += repeat
                        per_expensive_pass.append(100.0 * repeat / raw)
                else:
                    concurrent_raw += raw
                    concurrent_repeat += repeat
            seen |= files

    def share(part: float, whole: float) -> float:
        return round(100.0 * part / whole, 1) if whole else 0.0

    return {
        "transcripts_read": float(len(seen_transcripts)),
        "newest_transcript": newest,
        "increments": float(increments),
        "later_passes": float(later),
        "files_already_opened_median_pct": round(statistics.median(overlaps), 1)
        if overlaps
        else 0.0,
        "repeat_share_pct": share(sequential_repeat, sequential_raw),
        "new_share_pct": share(sequential_new, sequential_raw),
        "repeat_share_median_per_pass_pct": (
            round(statistics.median(per_pass), 1) if per_pass else 0.0
        ),
        "repeat_share_over_5m_pct": share(expensive_repeat, expensive_raw),
        "repeat_share_median_over_5m_pct": (
            round(statistics.median(per_expensive_pass), 1) if per_expensive_pass else 0.0
        ),
        "passes_over_5m": float(len(per_expensive_pass)),
        "concurrent_repeat_share_pct": share(concurrent_repeat, concurrent_raw),
        "raw_tokens_measured": sequential_raw,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="What earlier review passes over an increment already did.",
        epilog="0 = every pass finished; 1 = one did not, so the map overstates coverage; "
        "2 = nothing on disk.",
    )
    parser.add_argument("increment", nargs="?", help="a YYYYMMDD_HHMM-name branch or plan")
    parser.add_argument("--list", action="store_true", help="increments with passes on disk")
    parser.add_argument("--measure", action="store_true", help="re-derive the docstring's table")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--projects", type=Path, help="transcript root (tests)")
    args = parser.parse_args(argv)

    if args.measure:
        numbers = measure(args.projects)
        if args.json:
            print(json.dumps(numbers, indent=2))
        else:
            for key, value in numbers.items():
                if key == "newest_transcript":
                    stamp = datetime.fromtimestamp(value, tz=UTC).strftime("%Y%m%d %H:%M UTC")
                    print(f"{key:38} {stamp}")
                else:
                    print(f"{key:38} {value:,.1f}")
        return 0

    grouped = collect(args.projects)

    if args.list or not args.increment:
        if not grouped:
            print("no review passes found on this machine", file=sys.stderr)
            return 2
        rows = sorted(grouped.items(), key=lambda kv: -sum(p.tokens for p in kv[1]))
        if args.json:
            print(json.dumps({k: len(v) for k, v in rows}, indent=2))
            return 0
        print(f"{'passes':>6} {'raw tokens':>13}  increment")
        for name, passes in rows:
            print(f"{len(passes):6d} {sum(p.tokens for p in passes):13,}  {name}")
        return 0

    passes = grouped.get(args.increment)
    if not passes:
        print(
            f"no review passes on disk for {args.increment} — the next pass does start from zero",
            file=sys.stderr,
        )
        return 2

    lines, status = brief_for(args.increment, passes)
    if args.json:
        print(
            json.dumps(
                {
                    "increment": args.increment,
                    "unopened": [
                        path
                        for path in changed_files(args.increment)
                        if path not in {f for p in passes for f in p.files}
                    ],
                    "passes": [
                        {
                            "agent": p.agent_id,
                            "started": p.started,
                            "turns": p.turns,
                            "tokens": p.tokens,
                            "incomplete": p.incomplete,
                            "files": sorted({f for f in p.files if f}),
                            "probes": [
                                {"command": x.command, "output": x.output[:400]}
                                for x in p.probes
                                if _interesting(x.command)
                            ],
                            "report": p.report[:2000],
                        }
                        for p in passes
                    ],
                },
                indent=2,
            )
        )
    else:
        print("\n".join(lines))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
