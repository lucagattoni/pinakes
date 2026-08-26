"""`docs/STATUS.md`'s header names the released version — a gate, not a checklist item.

**Why a gate at all.** The header — line 3, `**Latest release: x.y.z**` — drifted from
`pinakes.__version__` for four consecutive releases (0.5.0 → 0.7.1) while the same release sweeps
updated every table below it, in the file whose own preamble says it is the only place in the repo
that says what is built — and this repo is public. A written checklist missed it four times
running, which is this project's own threshold for turning the item into a gate: the same reason
`changelog.d/`, `retro.d/` and `nul-scan` exist (plans/20260731_1202-open-corrections.md, 20260803).

**Two layers, and they answer different questions.**

* **Layer 1 — `line3 == pinakes.__version__`.** The only machine-derived comparison here: Hatch
  reads that constant to build the wheel, it is bumped in the release commit, and both facts are
  inside the checkout. This is why `check.sh` can run this gate unconditionally in a script whose
  own comment demands it stay offline-capable.
* **Layer 2 — the hold marker, against `R`,** the newest entry of `docs/STATUS.md`'s
  *Published versions* row. `line3 > R` → the marker is **required**; `line3 == R` → it is
  **forbidden**; `line3 < R` → always red; **the row unreadable → hard fail, never skip.**

**`__version__` means *landed on `main`*, not *published* — decided by the user 20260825 12:37
(D-35), and this docstring said the opposite until 20260826.** It read *"The invariant holds with
no exception window… this gate never goes red on a correct tree"*. There **is** an exception
window: the interval between a release commit landing and its tag reaching PyPI, used deliberately
three times, and 0.30.2's lasted fourteen minutes. During it line 3 names a version `pip install`
cannot get, on a page that deploys on every push — so the line must *say so*, and layer 2 is what
makes it say so.

**Layer 2 exists because writing the marker is enforceable and removing it was not.** X7's network
rule can only require the marker when a version is absent from the index; a marker left behind
after a successful publish is green by construction, forever — green here too (`SHAPE` has no `$`,
a looseness that exists for the `last reviewed` date), and green in `release_order_gate.py`, none
of whose seven sequences reads line 3's tail. The marker is **0-for-2 on being produced by the
procedure**: it was absent for 0.30.2's fourteen minutes and again at 20260825 08:27. That record
is about *writing* it; nothing has ever tested *removing* it, which is exactly why the removal side
is the half that had to become a check rather than a habit.

**What layer 2 does not reach, stated so its green is not read as more than it is.**
`docs/RELEASING.md` explicitly permits the *Published versions* row to lag a release, because an
entry is held back until it is verified from the index. So after a successful publish `line3 > R`
still holds, and layer 2 stays green over a marker that has become false. **It enforces the
marker's removal at the moment the row is updated, not at the moment of publication** — the
publication window is layer 3's (the PyPI index query), which is soft and lives in its own CI job.
This limit was measured and written down before the build, not discovered after it.

**The marker's shape is a parsed shape, not free text.** `⏸` followed by a bold span, and **that
span must name `R`** — the version `pip install` actually gets. A qualifier is a claim about the
index, and a claim nobody checks is how line 3 got here. The `⏸` form was chosen over a bracketed
keyword for one reason worth recording: it is the form already on `main`, so this gate went green
on the tree it was written against without asking anyone to edit a document to satisfy it.

**Only the version is gated — never the `last reviewed` date beside it.** A wall-clock staleness
check fails on a quiet weekend with no code change; decided at `prices-toml-parses` (`check.sh`),
where staleness is a runtime concern rather than a build gate. The same reasoning, not re-decided.

**The shape and the position are gated as well as the value.** The header must sit on line 3 —
the line `docs/RELEASING.md`'s sweep table names, the first line a reader sees — and must start
with exactly `**Latest release: x.y.z**`. A gate that scanned the whole file for the pattern
would stay green while a stale header sat where every reader looks, and a gate that accepted any
shape could be silenced by reformatting the line. Not found, or not that shape → fail.

**Two couplings that move together or not at all.** Layer 1's failure string *"the header drifted
from the release"* is grepped verbatim by `ci.yml`'s negative check, which
`tests/test_check_script.py` pins as a command; rewording it without changing the workflow leaves
that check asserting only a non-zero exit, which its own comment says is insufficient. And layer 1
must stay **first**, because that negative check drives this gate with `--expect-version 99.99.99`
and reads the reason it prints.

`--status-file` and `--expect-version` exist for the unit tests and for CI's negative check
("the gate can still fail"); with neither, it checks the real file against the real version. Layer
2 reads `R` out of **the same file** `--status-file` names, so one flag moves both layers and a
fixture cannot satisfy one while dodging the other.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from release_order_gate import SEQUENCES, AmbiguousRegionError, Sequence, Version

from pinakes import __version__

REPO = Path(__file__).resolve().parent.parent
STATUS = REPO / "docs" / "STATUS.md"

HEADER_LINE = 3
"""1-based, matching what `docs/RELEASING.md`'s sweep table and every editor display."""

SHAPE = re.compile(r"^\*\*Latest release: (\d+\.\d+\.\d+)\*\*")
"""Anchored at the start of the line. What follows the closing `**` — the `last reviewed` date —
is deliberately unconstrained by *this* pattern, because it is deliberately ungated. Layer 2 reads
that tail for the hold marker and constrains nothing else in it."""

HOLD = re.compile(r"⏸\s*\*\*(?P<why>[^*]+)\*\*")
"""The hold marker, in line 3's tail: a pause glyph and a bold qualifier.

Bold-delimited rather than *"anything after the glyph"* so the qualifier has an end the gate can
find — `why` is what must name `R`. `[^*]+` and not `.+?` because the span is what is between the
fences, and a lazy dot would stop at the first `*` of the closing pair either way while accepting
a nested one."""

#: Which `release_order_gate` sequence carries `R`. Matched on both fields, because that module has
#: two sequences over `docs/STATUS.md` forty lines apart, and reading the wrong one is the exact
#: mistake that let the row drift four releases while the gate reported those releases present.
PUBLISHED_ROW = ("docs/STATUS.md", "the Published versions row")


def _show(version: Version) -> str:
    return ".".join(str(part) for part in version)


def _parse(version: str) -> Version:
    major, minor, patch = version.split(".")
    return (int(major), int(minor), int(patch))


def _fail(message: str) -> int:
    print(f"status-header: {message}", file=sys.stderr)
    return 1


def _published_row() -> Sequence | None:
    for sequence in SEQUENCES:
        if (sequence.path, sequence.what) == PUBLISHED_ROW:
            return sequence
    return None


def _check_hold_marker(status_file: Path, text: str, tail: str, stated: Version) -> int:
    """Layer 2. Returns 0 when line 3's tail is in the state `R` requires."""
    sequence = _published_row()
    if sequence is None:
        return _fail(
            f"tools/release_order_gate.py no longer has a sequence "
            f"({PUBLISHED_ROW[0]}, {PUBLISHED_ROW[1]}), so the hold-marker check has nothing to "
            f"compare line {HEADER_LINE} against. It is not skipped: a renamed sequence would "
            f"otherwise disable this layer silently. Repoint PUBLISHED_ROW"
        )
    try:
        published = sequence.versions_in(text)
    except AmbiguousRegionError as exc:
        return _fail(f"the Published versions row is no longer unique in {status_file}: {exc}")
    if not published:
        return _fail(
            f"{status_file} has no readable *Published versions* row, so there is nothing to say "
            f"whether line {HEADER_LINE} is ahead of PyPI. A row this gate cannot read is a hard "
            f"failure and never a skip — a check that quietly stops checking is what the hold "
            f"marker already was"
        )
    # The last entry, not `max()`: the row is declared ascending and `release_order_gate.py` is
    # what holds it to that. Taking the maximum here would paper over a mis-sorted row that the
    # other gate is red about, and this one would report a version the row does not end with.
    newest = published[-1]

    marker = HOLD.search(tail)
    if stated < newest:
        return _fail(
            f"{status_file} line {HEADER_LINE} says the latest release is {_show(stated)}, but "
            f"the *Published versions* row already ends at {_show(newest)} — the headline is "
            f"behind what is published. Line 3 names pinakes.__version__, so this means the "
            f"version bump is missing, not that the row is wrong"
        )
    if stated == newest:
        if marker is not None:
            return _fail(
                f"{status_file} line {HEADER_LINE} still carries the hold marker, but "
                f"{_show(stated)} is the newest entry in the *Published versions* row — it is "
                f"published, so the line claims a hold that is over. Remove the ⏸ and its "
                f"qualifier. Nothing else in this repository can see a stale marker: this gate's "
                f"SHAPE stops at the closing ** and no release-order sequence reads line 3's tail"
            )
        return 0
    if marker is None:
        return _fail(
            f"{status_file} line {HEADER_LINE} names {_show(stated)}, which is ahead of the "
            f"*Published versions* row's newest entry {_show(newest)} — so it is landed and not "
            f"published, and the line says nothing about that on a page that deploys on every "
            f"push. Add the hold marker: ** — ⏸ **landed on `main`, NOT tagged and NOT on PyPI; "
            f"`pip install pinakes` still gets {_show(newest)}.**"
        )
    if _show(newest) not in marker.group("why"):
        return _fail(
            f"{status_file} line {HEADER_LINE}'s hold marker does not name {_show(newest)}, the "
            f"version `pip install pinakes` actually gets: it reads {marker.group('why')!r}. A "
            f"qualifier is a claim about the index, and an unchecked claim about the index is how "
            f"this line came to need a gate at all"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="status_header_gate", description=__doc__)
    parser.add_argument(
        "--status-file",
        type=Path,
        default=STATUS,
        help="the file to check (default: the real docs/STATUS.md; tests point this at a copy)",
    )
    parser.add_argument(
        "--expect-version",
        default=__version__,
        help="the version the header must name (default: pinakes.__version__)",
    )
    args = parser.parse_args(argv)
    status_file: Path = args.status_file
    expected: str = args.expect_version

    text = status_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < HEADER_LINE:
        return _fail(
            f"{status_file} has fewer than {HEADER_LINE} lines — "
            f"the '**Latest release: x.y.z**' header is gone"
        )

    line = lines[HEADER_LINE - 1]
    match = SHAPE.match(line)
    if match is None:
        return _fail(
            f"{status_file} line {HEADER_LINE} does not start with "
            f"'**Latest release: x.y.z**' — found {line!r}. Deleting or reformatting "
            f"the header does not silence this gate; restore the line"
        )

    stated = match.group(1)
    # Layer 1 first, and it must stay first: `ci.yml`'s negative check drives this gate with
    # `--expect-version 99.99.99` and greps the reason below. A layer 2 failure reaching that
    # tree first would leave the workflow asserting only a non-zero exit.
    if stated != expected:
        return _fail(
            f"{status_file} line {HEADER_LINE} says the latest release is "
            f"{stated}, but pinakes.__version__ is {expected} — the header drifted from the "
            f"release. Bump it in the release commit (docs/RELEASING.md, sweep table)"
        )

    # The tail is everything after the closing `**` — the region SHAPE deliberately leaves
    # unconstrained, which is where the `last reviewed` date lives and where the marker goes.
    # Searching the whole line would work today only because SHAPE is anchored; passing the tail
    # says what the marker is part of.
    tail = line[match.end() :]
    layer_two = _check_hold_marker(status_file, text, tail, _parse(stated))
    if layer_two != 0:
        return layer_two

    held = HOLD.search(tail) is not None
    print(
        f"status-header: {status_file.name} line {HEADER_LINE} and "
        f"pinakes.__version__ agree on {stated}"
        + (
            ", and the hold marker is present as the *Published versions* row requires"
            if held
            else ", and the *Published versions* row agrees it is published — no hold marker"
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
