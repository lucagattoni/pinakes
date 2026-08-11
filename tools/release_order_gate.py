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
many releases there are, and it never needs raising.

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

    def __init__(self, path: str, what: str, pattern: str, ascending: bool) -> None:
        self.path = path
        self.what = what
        self.pattern = re.compile(pattern, re.MULTILINE)
        self.ascending = ascending

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

SEQUENCES = (
    Sequence("CHANGELOG.md", "the release headings", rf"^## \[{NUM}\] — ", ascending=False),
    Sequence("CHANGELOG.md", "the link definitions", rf"^\[{NUM}\]: ", ascending=False),
    Sequence("docs/ROADMAP.md", "the release table", rf"^\| \*\*\[{NUM}\]\(#", ascending=True),
    Sequence("docs/ROADMAP.md", "the per-release sections", rf"^## {NUM} — ", ascending=True),
    Sequence("docs/STATUS.md", "the release roadmap table", rf"^\| \*\*{NUM}\*\* ", ascending=True),
)


def _show(version: Version) -> str:
    return ".".join(str(part) for part in version)


def check(root: Path, *, report: list[str] | None = None) -> list[str]:
    failures: list[str] = []
    newest: dict[str, Version] = {}

    for sequence in SEQUENCES:
        where = f"{sequence.path} — {sequence.what}"
        versions = sequence.versions(root)
        if len(versions) < MINIMUM:
            failures.append(
                f"{where}: matched {len(versions)} release(s), fewer than the {MINIMUM} floor. "
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
        newest[where] = max(versions)
        if report is not None:
            # The count is printed on success, not only on failure: it is the one number that says
            # the pattern still matches what it names, and a gate that prints nothing on a green
            # run gives a reader no way to notice it has gone quiet.
            report.append(
                f"{where}: {len(versions)} releases, {direction}, newest {_show(max(versions))}"
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
    print(f"release-order: {len(SEQUENCES)} sequences in release order.")
    for line in report:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
