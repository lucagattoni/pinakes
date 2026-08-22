"""`tools/release_order_gate.py`, driven as a subprocess — one test per branch.

A subprocess rather than an import, for the reason `tests/test_status_header_gate.py` gives: it
exercises the same artifact `check.sh` and CI run, argument parsing included, with no `sys.path`
surgery. The gate takes a repository root as its one argument, so every mutated tree is written to
`tmp_path` and the real documents are never touched.

The defect this gate exists to catch is a *sequence* defect, so the tests that matter are the ones
proving the gate can still see it: a misordering must be named with the offending pair, and a
pattern that has stopped matching must fail rather than pass vacuously — an empty sequence is
sorted by definition, which is the one way a check like this dies quietly.
"""

import re
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).parent.parent / "tools" / "release_order_gate.py"

#: Enough releases to clear the gate's own floor, so a fixture exercises the ordering branch
#: rather than the count branch.
COUNT = 30


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False
    )


def _tree(
    root: Path,
    *,
    versions: list[str],
    status_versions: list[str] | None = None,
    prose_versions: list[str] | None = None,
) -> Path:
    """A minimal repository whose three documents carry the sequences the gate reads."""
    status_versions = versions if status_versions is None else status_versions
    prose_versions = versions if prose_versions is None else prose_versions
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "CHANGELOG.md").write_text(
        "".join(f"## [{v}] — 20260101 00:00\n\nsomething.\n\n" for v in reversed(versions))
        + "".join(f"[{v}]: https://example.invalid/{v}\n" for v in reversed(versions)),
        encoding="utf-8",
    )
    (root / "docs" / "ROADMAP.md").write_text(
        "| Release | Adds |\n|---|---|\n"
        + "".join(f"| **[{v}](#anchor-{v})** | 20260101 00:00 | something |\n" for v in versions)
        + "\n"
        + _parts(versions),
        encoding="utf-8",
    )
    (root / "docs" / "STATUS.md").write_text(
        "| Release | Adds |\n|---|---|\n"
        + "".join(f"| **{v}** ✅ | something |\n" for v in status_versions)
        + "\n## Published on PyPI\n\n"
        + "".join(
            f"**{v}, same standard, 20260101 00:00:** verified from the index.\n\n"
            for v in prose_versions
        ),
        encoding="utf-8",
    )
    return root


#: The real document's Part structure, in miniature: the three range forms it actually uses, plus a
#: rangeless Part at the end. Fixtures carry it because the placement check reads a section's Part
#: from the document, so a fixture with no Parts tests nothing about placement.
PARTS: tuple[tuple[str, str], ...] = (
    ("# Part 1 · The engine — `0.1.x`", "prefix"),
    ("# Part 2 · The middle — `0.2.0` → `0.4.0`", "closed"),
    ("# Part 3 · Links — `0.5.0` → `0.7.0`", "closed"),
    ("# Part 4 · Everything since — `0.8.0` onward", "open"),
    ("# Part 5 · What is not built", "none"),
)


def _part_of(version: str) -> int:
    """Which Part index the fixture's own ranges put a version in. Mirrors PARTS above."""
    minor = int(version.split(".")[1])
    if minor == 1:
        return 0
    if 2 <= minor <= 4:
        return 1
    if 5 <= minor <= 7:
        return 2
    return 3


def _parts(versions: list[str], *, misfile: str | None = None, into: int = 4) -> str:
    """The Part headings with each version's section under the Part its own range claims.

    `misfile` moves one section under `into` instead — the defect that shipped twice, and the only
    way to build a tree where every sequence is sorted and a section is still in the wrong place.
    """
    held: list[list[str]] = [[] for _ in PARTS]
    for v in versions:
        index = into if v == misfile else _part_of(v)
        held[index].append(f"## {v} — Something · 20260101 00:00\n\nbody.\n")
    out: list[str] = []
    for (heading, _kind), sections in zip(PARTS, held, strict=True):
        out.append(heading + "\n\n" + "".join(f"{s}\n" for s in sections))
    return "\n".join(out)


def _versions(count: int = COUNT) -> list[str]:
    return [f"0.{n}.0" for n in range(1, count + 1)]


def test_the_real_documents_are_in_release_order() -> None:
    """The invariant itself, with no arguments: on a correct tree the gate is green. This is the
    run `check.sh` performs."""
    result = run()
    assert result.returncode == 0, result.stderr
    assert "6 sequences in release order" in result.stdout


def test_every_pattern_still_matches_the_real_documents() -> None:
    """The vacuity check, and the reason this file exists as much as the ordering branch does.

    A gate whose patterns have rotted reports success over a document it can no longer read. The
    green run therefore prints what each pattern matched, and this asserts all five are named with
    a real count — reformat a table past recognition and it goes red in the commit that does it,
    rather than quietly measuring nothing.
    """
    result = run()
    assert result.returncode == 0, result.stderr
    # Each sequence against **its own** floor, not a single number: the prose list began at 0.16.0
    # and carries a lower one, so asserting the shared 25 here would either fail on a correct tree
    # or have to be weakened to 15 for all six — which would stop noticing a rotted pattern in the
    # five that are long.
    floors = {
        "CHANGELOG.md — the release headings": 25,
        "CHANGELOG.md — the link definitions": 25,
        "docs/ROADMAP.md — the release table": 25,
        "docs/ROADMAP.md — the per-release sections": 25,
        "docs/STATUS.md — the release roadmap table": 25,
        "docs/STATUS.md — the Published on PyPI prose": 15,
    }
    for what, floor in floors.items():
        match = re.search(rf"{re.escape(what)}: (\d+) releases,", result.stdout)
        assert match is not None, f"{what} is not named in the report:\n{result.stdout}"
        assert int(match.group(1)) >= floor, result.stdout
    counts = [int(m) for m in re.findall(r": (\d+) releases,", result.stdout)]
    assert len(counts) == len(floors), result.stdout


def test_an_ordered_tree_passes(tmp_path: Path) -> None:
    result = run(str(_tree(tmp_path, versions=_versions())))
    assert result.returncode == 0, result.stderr
    assert "6 sequences in release order" in result.stdout


def test_a_row_out_of_order_is_named_with_its_neighbour(tmp_path: Path) -> None:
    """The message must name the pair. A gate reporting only "out of order" leaves the reader to
    re-derive what this gate was written to find for them."""
    versions = _versions()
    swapped = [*versions[:5], versions[6], versions[5], *versions[7:]]
    result = run(str(_tree(tmp_path, versions=swapped)))
    assert result.returncode == 1
    assert "reads ascending, but 0.7.0 is followed by 0.6.0" in result.stderr
    assert "docs/ROADMAP.md — the release table" in result.stderr


def test_a_descending_sequence_is_checked_in_its_own_direction(tmp_path: Path) -> None:
    """`CHANGELOG.md` reads newest-first while the other two read oldest-first. A gate that
    inferred direction per file would call one of them correct whichever way it was scrambled."""
    root = _tree(tmp_path, versions=_versions())
    changelog = root / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    changelog.write_text(
        text.replace("## [0.30.0] — ", "## [TMP] — ")
        .replace("## [0.29.0] — ", "## [0.30.0] — ")
        .replace("## [TMP] — ", "## [0.29.0] — "),
        encoding="utf-8",
    )
    result = run(str(root))
    assert result.returncode == 1
    assert "reads descending, but 0.29.0 is followed by 0.30.0" in result.stderr


def test_a_pattern_that_stops_matching_fails_rather_than_passing(tmp_path: Path) -> None:
    """The failure mode that would otherwise kill this gate silently: an empty sequence is sorted,
    so a rotted pattern reports success over a document it can no longer read."""
    root = _tree(tmp_path, versions=_versions())
    status = root / "docs" / "STATUS.md"
    status.write_text(
        status.read_text(encoding="utf-8").replace("| **0.", "| 0."), encoding="utf-8"
    )
    result = run(str(root))
    assert result.returncode == 1
    assert "fewer than the 25 floor" in result.stderr
    assert "docs/STATUS.md — the release roadmap table" in result.stderr


def test_a_document_the_gate_cannot_read_fails_as_a_gate(tmp_path: Path) -> None:
    """Not as a traceback. A check that cannot find what it guards has stopped guarding it, and
    must say so in the same voice as every other failure here."""
    root = _tree(tmp_path, versions=_versions())
    (root / "docs" / "STATUS.md").unlink()
    result = run(str(root))
    assert result.returncode == 1
    assert "a document this gate reads is unreadable" in result.stderr
    assert "docs/STATUS.md" in result.stderr
    assert "Traceback" not in result.stderr


def test_a_sweep_that_updates_one_document_and_not_another_is_caught(tmp_path: Path) -> None:
    """Every sequence internally sorted, and the set of them disagreeing — which no per-file
    ordering check can see."""
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, status_versions=versions[:-1])))
    assert result.returncode == 1
    assert "the newest release differs between sequences" in result.stderr
    assert "0.30.0" in result.stderr and "0.29.0" in result.stderr


def test_a_prose_entry_out_of_order_is_named_with_its_neighbour(tmp_path: Path) -> None:
    """The sixth sequence, and the defect that produced it: `docs/RELEASING.md` names this list as
    a place a release stales and says this gate decides where the entry goes, while no pattern here
    matched it. It had drifted through every green run since 20260821."""
    versions = _versions()
    swapped = [*versions[:5], versions[6], versions[5], *versions[7:]]
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=swapped)))

    assert result.returncode == 1
    assert "docs/STATUS.md — the Published on PyPI prose" in result.stderr
    assert "reads ascending, but 0.7.0 is followed by 0.6.0" in result.stderr


def test_the_prose_list_may_lag_the_release_sequences(tmp_path: Path) -> None:
    """An entry here is written from evidence: the claim is held back until it is verified *from*
    the index, so between a release landing and its verification this list is one entry short by
    design. A gate that demanded agreement would turn that intended window red, and a gate people
    turn off during a documented window is not a gate."""
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=versions[:-1])))

    assert result.returncode == 0, result.stderr
    assert "may lag" in result.stdout, "the report must say which sequence is exempt, and why"


def test_the_prose_list_may_not_lead_the_release_sequences(tmp_path: Path) -> None:
    """Lagging is permitted, leading is not. A verification paragraph for a release the CHANGELOG
    and ROADMAP have never heard of is a claim about the index that nothing else records — the
    exemption is a direction, not a hole.

    Without this the exemption would let the list drift arbitrarily far in either direction, which
    is the failure mode of every "tolerate it" flag written without one.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=[*versions, "0.31.0"])))

    assert result.returncode == 1
    assert "docs/STATUS.md — the Published on PyPI prose" in result.stderr
    assert "names 0.31.0, newer than 0.30.0" in result.stderr
    assert "may not lead" in result.stderr


def test_a_sequence_carries_its_own_floor(tmp_path: Path) -> None:
    """The prose list begins at 0.16.0, so the shared 25 floor would fail it for being short
    rather than for being unread. Its own floor is 15 — still a floor, since releases are never
    deleted, and still the thing that catches a pattern that has stopped matching.

    Discriminating: the five long sequences stay at 30 here, so only the per-sequence floor can
    produce this failure. A gate still reading the shared `MINIMUM` would report 25 in the message.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=versions[:14])))

    assert result.returncode == 1
    assert "docs/STATUS.md — the Published on PyPI prose" in result.stderr
    assert "matched 14 release(s), fewer than the 15 floor" in result.stderr


def test_the_prose_pattern_does_not_match_the_roadmap_table(tmp_path: Path) -> None:
    """A pattern matching too much is as bad as one matching nothing, and harder to notice: it
    would silently fold another document's rows into this sequence and check a concatenation.
    The count is the observable — six sequences, and the prose one names exactly its own entries.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=versions[:20])))

    assert result.returncode == 0, result.stderr
    match = re.search(r"the Published on PyPI prose: (\d+) releases,", result.stdout)
    assert match is not None, result.stdout
    assert int(match.group(1)) == 20, (
        f"the prose sequence must match its own 20 entries and nothing else: {result.stdout}"
    )


def test_the_real_document_places_every_section_under_its_part() -> None:
    """The invariant itself, with no arguments — the run `check.sh` performs."""
    result = run()
    assert result.returncode == 0, result.stderr
    assert "every section placed" in result.stdout
    match = re.search(r"placement: (\d+) release section\(s\)", result.stdout)
    assert match is not None, result.stdout
    assert int(match.group(1)) >= 40, result.stdout


def test_a_section_under_a_rangeless_part_fails_while_every_sequence_stays_sorted(
    tmp_path: Path,
) -> None:
    """The defect that shipped twice, in the only form that matters.

    `0.27.1`'s section landed inside `# Part 5 · What is not built`, and **all six sequences were
    green**: it was still the newest section in document order, and sorting says nothing about
    location. So the fixture moves the newest section into the rangeless Part, where it remains last
    and every ordering check still passes. If this test ever fails for an *ordering* reason it has
    stopped testing placement.
    """
    versions = _versions()
    root = _tree(tmp_path, versions=versions)
    (root / "docs" / "ROADMAP.md").write_text(
        "| Release | Adds |\n|---|---|\n"
        + "".join(f"| **[{v}](#anchor-{v})** | 20260101 00:00 | something |\n" for v in versions)
        + "\n"
        + _parts(versions, misfile=versions[-1], into=4),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 1
    assert f"the section for {versions[-1]} sits under Part 5" in result.stderr
    assert "Part 5 declares no release range" in result.stderr
    assert "reads ascending" not in result.stderr, (
        "the fixture must fail for placement alone — an ordering failure here means the test no "
        "longer distinguishes the two, which is the whole point of the check:\n" + result.stderr
    )


def test_a_section_one_part_early_is_caught_and_names_both_parts(tmp_path: Path) -> None:
    """The realistic shape: an off-by-one at a Part boundary.

    `0.8.0` appended to the end of Part 3 (`0.5.0` → `0.7.0`) instead of opening Part 4 (`0.8.0`
    onward) leaves the document in ascending order — it still sits between `0.7.0` and `0.9.0` — so
    only its Part is wrong. The message must name the Part it is under *and* the Part it belongs to,
    or the reader has to re-derive what the gate already knows.
    """
    versions = _versions()
    root = _tree(tmp_path, versions=versions)
    (root / "docs" / "ROADMAP.md").write_text(
        "| Release | Adds |\n|---|---|\n"
        + "".join(f"| **[{v}](#anchor-{v})** | 20260101 00:00 | something |\n" for v in versions)
        + "\n"
        + _parts(versions, misfile="0.8.0", into=2),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 1
    assert "the section for 0.8.0 sits under Part 3, but belongs under Part 4" in result.stderr
    assert "Part 3 declares 0.5.0 → 0.7.0" in result.stderr
    assert "reads ascending" not in result.stderr, result.stderr


def test_a_part_whose_range_stops_parsing_holds_nothing_rather_than_everything(
    tmp_path: Path,
) -> None:
    """A heading whose range is reformatted past recognition must fail, not silently accept.

    The dangerous reading is "no declared range, so nothing to check" — that would make every
    section under it pass, and a Part is exactly where thirty sections live. `declares_range` is
    false in both cases and `holds()` returns False for both, so a rangeless Part holding sections
    is always a failure whether the range was removed or was never there.
    """
    root = _tree(tmp_path, versions=_versions())
    roadmap = root / "docs" / "ROADMAP.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "# Part 4 · Everything since — `0.8.0` onward",
            "# Part 4 · Everything since — 0.8.0 onward",  # backticks gone; range no longer parses
        ),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 1
    assert "Part 4 declares no release range" in result.stderr
    assert "falls in no Part's declared range" in result.stderr, (
        "with Part 4 unparsed nothing claims 0.8.0 onward, and the message must say so rather "
        "than point at a Part that could take it"
    )


def test_the_prefix_range_form_is_actually_read(tmp_path: Path) -> None:
    """`0.1.x` is a form of its own, and a gate understanding only `a → b` and `onward` would place
    every 0.1.z section nowhere while looking correct on the other thirty."""
    root = _tree(tmp_path, versions=_versions())
    roadmap = root / "docs" / "ROADMAP.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "# Part 1 · The engine — `0.1.x`",
            "# Part 1 · The engine — `0.1.z`",  # not a form the gate knows
        ),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 1
    assert "the section for 0.1.0 sits under Part 1" in result.stderr
    assert "Part 1 declares no release range" in result.stderr


def test_a_part_pattern_that_stops_matching_fails_rather_than_passing(tmp_path: Path) -> None:
    """The vacuity branch, for the reason the sequence floor exists: a document the gate can no
    longer find Parts in must say so, not report every section correctly placed."""
    root = _tree(tmp_path, versions=_versions())
    roadmap = root / "docs" / "ROADMAP.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace("\n# Part ", "\n# Section "), encoding="utf-8"
    )

    result = run(str(root))

    assert result.returncode == 1
    assert "`# Part` heading(s), fewer than the 4 floor" in result.stderr
