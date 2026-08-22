"""The release history reads in release order — checked, because it fails silently.

`CHANGELOG.md`, `docs/ROADMAP.md` and `docs/STATUS.md` each carry an ordered sequence of releases.
A release sweep adds one row to each, and **a row added in the wrong position is invisible to every
check that reads rows**: the table is complete, every link resolves, `mkdocs build --strict` is
green, and a reader checking any single row finds it correct. Ordering is a property of the
sequence, not of any row in it.

It drifted anyway. On 20260811 five rows were out of place across three sequences — `0.15.1` after
`0.16.0` in STATUS, and `0.20.1`/`0.21.0`/`0.21.1` scrambled after `0.22.1` in both of ROADMAP's.
Every one was wrong on **both** readings, SemVer and release time, so no ordering of the table made
them right. The `0.15.1` instance had already been found by the 20260807 documentation audit and
sat unworked for four days, which is this project's threshold for replacing a convention with a
gate (the same reasoning `check.sh` records above `status_header_gate.py`).

**The direction is declared per sequence, never inferred.** Inferring it from whichever direction
the majority of adjacent pairs agree on would let a badly scrambled file elect its own answer and
pass — the failure mode of a gate that reads a file and never compares.

**Every sequence must also be long.** A pattern that silently stops matching — because a table was
reformatted, or a heading style changed — leaves an empty sequence, and an empty sequence is sorted
by definition. `MINIMUM` is a floor on the count for that reason alone; it is not a claim about how
many releases there are, and it never needs raising. A sequence that *began* later carries its own
floor: STATUS's prose list starts at 0.16.0, so the shared floor would fail it for being short
rather than for being unread.

**A sequence may be allowed to lag, never to lead.** STATUS's *Published on PyPI* prose is written
from evidence: a claim about the index is held back until it has been verified *from* the index,
so between a release landing and its verification that list is legitimately one entry short. A
sequence marked `newest_may_lag` is therefore exempt from the agreement check below — but only
downwards. If it names a release *newer* than every other sequence, that is a claim about the index
for a release the release documents have never heard of, and it fails. Removing the exemption would
turn an intended, documented window red; removing the direction with it would let the list drift
behind forever with nothing watching.

**What `newest_may_lag` costs, said plainly.** A missing newest entry is legal for that sequence,
so an entry written in a shape the pattern does not match is indistinguishable from one that has
not been written yet — it is silently unchecked rather than reported. The floor still catches
wholesale pattern rot; a single mis-shaped newest entry it cannot catch. That is the price of not
turning the hold-back window red, and it is stated here rather than left for a reader to discover,
because a gate whose limits are undocumented gets trusted past them.

**Order is not the only way a release row goes wrong: it can be in the wrong *place*.** On
20260822 `0.27.1`'s per-release section landed inside `# Part 5 · What is not built` rather than at
the end of Part 4, because the script that inserted it looked for the next `## ` heading and
stepped over the `# ` that bounds the Part. All six sequences were green on a document filing a
shipped release under "what is not built" — the sequence was still sorted, because sorting says
nothing about location.
0.25.3 did the same thing and 0.25.4 fixed it once already, so this is the second instance and the
gate is the third attempt at the rule.

`check_placement` therefore requires every per-release section to sit under the Part whose declared
range contains its version. **The ranges are read out of the `# Part N` headings themselves** —
``— `0.1.x` ``, ``— `0.2.0` → `0.4.1` ``, ``— `0.8.0` onward`` — never from a mapping kept beside
them, because a hand-written mapping is a second copy of a fact the document already states and
would drift from it exactly as everything else here has. A Part that declares no range (Part 5) may
hold no release section at all, which is the case that fires on the defect above.

**Nothing here depends on timing, a network, or a dependency's behaviour.** Every check is a text
read over committed files, so there is no teardown to race and no run that can pass for a reason
other than the document's contents. Stated because a check whose passing depends on a dependency's
teardown timing has already been found in this repository, answering correctly 10 times out of 10
under one version and 2 out of 10 under the next.

**What this gate cannot see: a count.** It reads an *order*. A sentence saying "thirty-six" beside
a list of thirty-seven is invisible here, and one landed one line from its own correction through a
green run of every gate in this repo (20260822). Counts are checked by reading the neighbourhood,
which is why `docs/README.md` makes that a documentation rule rather than a gate.

Stdlib only, and no import of `pinakes`: like `paid_path_gate.py`, this must run before the package
is installed.
"""

from __future__ import annotations

import re
import sys
from itertools import pairwise
from pathlib import Path

#: A sequence shorter than this means the pattern stopped matching, not that the project un-released
#: something. Releases are never deleted, so this floor only ever holds.
MINIMUM = 25

Version = tuple[int, int, int]


class UnreadableError(Exception):
    """A document the gate reads is missing or unreadable. Carries the operator line, not a
    traceback."""


class Sequence:
    """One ordered run of releases in one file."""

    def __init__(
        self,
        path: str,
        what: str,
        pattern: str,
        ascending: bool,
        *,
        minimum: int = MINIMUM,
        newest_may_lag: bool = False,
    ) -> None:
        self.path = path
        self.what = what
        self.pattern = re.compile(pattern, re.MULTILINE)
        self.ascending = ascending
        self.minimum = minimum
        self.newest_may_lag = newest_may_lag

    def versions(self, root: Path) -> list[Version]:
        try:
            text = (root / self.path).read_text(encoding="utf-8")
        except OSError as exc:
            # A renamed or unreadable document must fail as a gate, with the operator line every
            # other failure here gets — never as a traceback. `paid_path_gate.py`'s gate 1 exists
            # for the same reason: a check that cannot find what it guards has stopped guarding it.
            raise UnreadableError(f"{self.path}: {exc}") from exc
        return [
            (int(a), int(b), int(c))
            for a, b, c in (m.group(1, 2, 3) for m in self.pattern.finditer(text))
        ]


NUM = r"(\d+)\.(\d+)\.(\d+)"
NUM_PREFIX = r"(\d+)\.(\d+)"

#: A per-release section in `docs/ROADMAP.md`. One home, because the ordering sequence and the
#: placement check must agree on what counts as one — if they disagree, each polices a set the
#: other does not and neither says so.
ROADMAP = "docs/ROADMAP.md"
ROADMAP_SECTION = rf"^## {NUM} — "

SEQUENCES = (
    Sequence("CHANGELOG.md", "the release headings", rf"^## \[{NUM}\] — ", ascending=False),
    Sequence("CHANGELOG.md", "the link definitions", rf"^\[{NUM}\]: ", ascending=False),
    Sequence("docs/ROADMAP.md", "the release table", rf"^\| \*\*\[{NUM}\]\(#", ascending=True),
    Sequence("docs/ROADMAP.md", "the per-release sections", ROADMAP_SECTION, ascending=True),
    Sequence("docs/STATUS.md", "the release roadmap table", rf"^\| \*\*{NUM}\*\* ", ascending=True),
    # The sixth, added 20260822. `docs/RELEASING.md`'s sweep table names this list as one of the
    # five places a release stales and says this gate decides where the new entry goes — while no
    # pattern here matched it, so the procedure delegated the decision to a check that could not
    # read the document. It had drifted: 0.25.1 → 0.25.3 → 0.25.2 → 0.25.4, wrong on SemVer and on
    # verification time, through every green run since 20260821.
    #
    # Its own floor because the list begins at 0.16.0, and `newest_may_lag` because an entry here
    # is held back until it has been verified from the index — see the module docstring for both.
    Sequence(
        "docs/STATUS.md",
        "the Published on PyPI prose",
        rf"^\*\*{NUM}, ",
        ascending=True,
        minimum=15,
        newest_may_lag=True,
    ),
)


#: `# Part 4 · Hardening, publishing, and every release since — `0.8.0` onward`. The number and the
#: title are not used; only the position and the trailing range are.
PART = re.compile(r"^# Part (\d+)\b.*$", re.MULTILINE)

#: The three range forms the Part headings actually use, matched at the **end** of the heading so a
#: title containing its own em dash cannot be mistaken for a range. A heading matching none of them
#: declares no range and may hold no release section.
_RANGE_PREFIX = re.compile(rf"`{NUM_PREFIX}\.x`\s*$")
_RANGE_CLOSED = re.compile(rf"`{NUM}`\s*→\s*`{NUM}`\s*$")
_RANGE_OPEN = re.compile(rf"`{NUM}`\s+onward\s*$")

#: A floor on the number of Parts, for the reason `MINIMUM` exists: a pattern that stopped matching
#: leaves no Parts, and a document with no Parts trivially satisfies "every section is under the
#: right Part" if the check is written the wrong way round. It is written the right way round — a
#: section under no Part fails — but the floor makes a rotted pattern say so directly.
PARTS_MINIMUM = 4


class Part:
    """One `# Part N` heading, and the release versions it declares itself to hold."""

    def __init__(self, number: str, heading: str, start: int) -> None:
        self.number = number
        self.heading = heading
        self.start = start
        self.low: Version | None = None
        self.high: Version | None = None
        self.declares_range = False

        if m := _RANGE_PREFIX.search(heading):
            major, minor = int(m.group(1)), int(m.group(2))
            self.low, self.high = (major, minor, 0), (major, minor, 10**9)
            self.declares_range = True
        elif m := _RANGE_CLOSED.search(heading):
            a = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            b = (int(m.group(4)), int(m.group(5)), int(m.group(6)))
            self.low, self.high = a, b
            self.declares_range = True
        elif m := _RANGE_OPEN.search(heading):
            self.low, self.high = (int(m.group(1)), int(m.group(2)), int(m.group(3))), None
            self.declares_range = True

    def holds(self, version: Version) -> bool:
        if not self.declares_range or self.low is None:
            return False
        if version < self.low:
            return False
        return self.high is None or version <= self.high

    def label(self) -> str:
        return f"Part {self.number}"

    def describe(self) -> str:
        """What this Part claims to hold, in its own words.

        Lives here rather than at the call site so the `low`/`high` narrowing is local to the
        object that owns them — a conditional expression at the call site reads as correct and does
        not type-check, because `declares_range` is not something a checker can tie to `low`.
        """
        if not self.declares_range or self.low is None:
            return f"{self.label()} declares no release range"
        if self.high is None:
            return f"{self.label()} declares {_show(self.low)} onward"
        return f"{self.label()} declares {_show(self.low)} → {_show(self.high)}"


def _show(version: Version) -> str:
    return ".".join(str(part) for part in version)


def check_placement(root: Path, *, report: list[str] | None = None) -> list[str]:
    """Every per-release section sits under the Part whose declared range contains its version.

    Positional, not textual: a section belongs to the nearest `# Part N` heading above it, which is
    what a reader sees and what `0.27.1` got wrong. The Part's *claim* about which versions it holds
    is then read from its own heading, so the two halves come from the document rather than from a
    table beside it.
    """
    failures: list[str] = []
    try:
        text = (root / ROADMAP).read_text(encoding="utf-8")
    except OSError as exc:
        raise UnreadableError(f"{ROADMAP}: {exc}") from exc

    parts = [Part(m.group(1), m.group(0), m.start()) for m in PART.finditer(text)]
    if len(parts) < PARTS_MINIMUM:
        failures.append(
            f"{ROADMAP}: matched {len(parts)} `# Part` heading(s), fewer than the "
            f"{PARTS_MINIMUM} floor. The pattern has stopped matching what it names, and a "
            "document with no Parts cannot be checked for placement at all."
        )
        return failures

    unranged = [p for p in parts if not p.declares_range]
    sections = list(re.compile(ROADMAP_SECTION, re.MULTILINE).finditer(text))
    placed = 0
    for match in sections:
        version = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        above = [p for p in parts if p.start < match.start()]
        if not above:
            failures.append(
                f"{ROADMAP}: the section for {_show(version)} sits above every `# Part` heading."
            )
            continue
        holder = above[-1]
        if holder.holds(version):
            placed += 1
            continue
        wanted = [p for p in parts if p.holds(version)]
        where = (
            f"belongs under {wanted[0].label()}"
            if wanted
            else "falls in no Part's declared range — either the section or a Part heading is wrong"
        )
        failures.append(
            f"{ROADMAP}: the section for {_show(version)} sits under {holder.label()}, but "
            f"{where}. {holder.describe()}. A sorted sequence says nothing about location, "
            "which is how 0.25.3 and 0.27.1 filed a shipped release under a Part that does not "
            "hold it."
        )

    if report is not None and not failures:
        names = ", ".join(p.label() for p in unranged) or "none"
        report.append(
            f"{ROADMAP} — placement: {placed} release section(s) under the Part their version "
            f"belongs to, across {len(parts)} Parts (holding no releases: {names})"
        )
    return failures


def check(root: Path, *, report: list[str] | None = None) -> list[str]:
    failures: list[str] = []
    newest: dict[str, Version] = {}
    lagging: dict[str, Version] = {}

    for sequence in SEQUENCES:
        where = f"{sequence.path} — {sequence.what}"
        versions = sequence.versions(root)
        if len(versions) < sequence.minimum:
            failures.append(
                f"{where}: matched {len(versions)} release(s), fewer than the "
                f"{sequence.minimum} floor. "
                "The pattern has stopped matching what it names; an empty sequence is sorted by "
                "definition, so this is a gate failure and not a short table."
            )
            continue

        direction = "ascending" if sequence.ascending else "descending"
        for first, second in pairwise(versions):
            if (first < second) != sequence.ascending:
                failures.append(
                    f"{where}: reads {direction}, but {_show(first)} is followed by "
                    f"{_show(second)}."
                )
        if sequence.newest_may_lag:
            lagging[where] = max(versions)
        else:
            newest[where] = max(versions)
        if report is not None:
            # The count is printed on success, not only on failure: it is the one number that says
            # the pattern still matches what it names, and a gate that prints nothing on a green
            # run gives a reader no way to notice it has gone quiet.
            lag = ", may lag" if sequence.newest_may_lag else ""
            report.append(
                f"{where}: {len(versions)} releases, {direction}, newest "
                f"{_show(max(versions))}{lag}"
            )

    # A sweep that updates one document and not another leaves every sequence internally sorted and
    # the set of them disagreeing — which no per-file check can see.
    if len(set(newest.values())) > 1:
        listed = ", ".join(f"{where} → {_show(v)}" for where, v in sorted(newest.items()))
        failures.append(
            f"the newest release differs between sequences: {listed}. A release adds a row to "
            "every one of them in the same commit (docs/RELEASING.md), so the sequence naming an "
            "older version is the one that was not swept."
        )

    # A lagging sequence is exempt from agreement, never from direction: naming a release newer
    # than every other sequence is a claim about the index for a release nothing else records.
    if newest and lagging:
        highest = max(newest.values())
        for where, version in sorted(lagging.items()):
            if version > highest:
                failures.append(
                    f"{where}: names {_show(version)}, newer than {_show(highest)} — the newest "
                    "release every other sequence carries. This list may lag them, because an "
                    "entry is held back until it is verified from the index; it may not lead "
                    "them, because that claims the index has a release the release documents do "
                    "not."
                )

    failures.extend(check_placement(root, report=report))

    return failures


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    report: list[str] = []
    try:
        failures = check(root, report=report)
    except UnreadableError as exc:
        print(f"release-order: a document this gate reads is unreadable — {exc}", file=sys.stderr)
        return 1
    if failures:
        print("release-order: the release history is out of order.", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"release-order: {len(SEQUENCES)} sequences in release order, and every section placed.")
    for line in report:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
