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

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL = Path(__file__).parent.parent / "tools" / "release_order_gate.py"

#: Enough releases to clear the gate's own floor, so a fixture exercises the ordering branch
#: rather than the count branch.
COUNT = 30


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False
    )


def failures_of(result: subprocess.CompletedProcess[str]) -> list[str]:
    """The gate's failure lines. Each is printed as `  {failure}` under one headline.

    Exists so a fixture can assert **exactly one failure, and which one** rather than
    `assert "reads ascending" not in stderr`. The negative form is satisfied by a reworded message
    and by a second failure appearing beside the one under test: it asserts the absence of a
    spelling, where what the test means is the presence of exactly one thing.
    """
    return [line[2:] for line in result.stderr.splitlines() if line.startswith("  ")]


def _row(versions: list[str]) -> str:
    """The **Published versions** row of STATUS's PyPI table — the seventh sequence's home.

    The trailing prose is not decoration. That cell carries ~20 version numbers *outside* the
    enumeration in the real document, and they are the reason the sequence needs a `within` anchor
    at all. So the fixture carries some too, **in descending order**: a gate whose scoping broke
    would read them as part of the sequence and report it unsorted. Without them a `within` that
    had stopped scoping would still pass every test here.
    """
    listed = ", ".join(versions[:-1]) + f" and {versions[-1]}" if len(versions) > 1 else versions[0]
    return (
        f"| Published versions | **{listed}** — {len(versions)}, counted from the index. "
        f"**{versions[-1]} changes no code path**; **{versions[0]} is the first published** |\n"
    )


def _tree(
    root: Path,
    *,
    versions: list[str],
    status_versions: list[str] | None = None,
    prose_versions: list[str] | None = None,
    row_versions: list[str] | None = None,
    extra_row: str = "",
) -> Path:
    """A minimal repository whose three documents carry the sequences the gate reads."""
    status_versions = versions if status_versions is None else status_versions
    prose_versions = versions if prose_versions is None else prose_versions
    row_versions = versions if row_versions is None else row_versions
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
        )
        + "\n| | |\n|---|---|\n"
        + _row(row_versions)
        + extra_row
        + "| First upload | 20260101 00:00 |\n",
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
    assert "7 sequences in release order" in result.stdout


def test_every_pattern_still_matches_the_real_documents() -> None:
    """The vacuity check, and the reason this file exists as much as the ordering branch does.

    A gate whose patterns have rotted reports success over a document it can no longer read. The
    green run therefore prints what each pattern matched, and this asserts all seven are named with
    a real count — reformat a table past recognition and it goes red in the commit that does it,
    rather than quietly measuring nothing.
    """
    result = run()
    assert result.returncode == 0, result.stderr
    # Each sequence against **its own** floor, not a single number: the prose list began at 0.16.0
    # and carries a lower one, so asserting the shared 25 here would either fail on a correct tree
    # or have to be weakened to 15 for all seven — which would stop noticing a rotted pattern in the
    # five that are long.
    floors = {
        "CHANGELOG.md — the release headings": 25,
        "CHANGELOG.md — the link definitions": 25,
        "docs/ROADMAP.md — the release table": 25,
        "docs/ROADMAP.md — the per-release sections": 25,
        "docs/STATUS.md — the release roadmap table": 25,
        "docs/STATUS.md — the Published on PyPI prose": 15,
        "docs/STATUS.md — the Published versions row": 25,
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
    assert "7 sequences in release order" in result.stdout


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
    The count is the observable — seven sequences, and the prose one names exactly its own
    entries.
    """
    versions = _versions()
    # Two behind, not ten: `MAX_VERIFICATION_LAG` makes a ten-behind fixture illegitimate, and a
    # fixture the gate would reject in production proves nothing about production.
    prose = versions[:-2]
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=prose)))

    assert result.returncode == 0, result.stderr
    match = re.search(r"the Published on PyPI prose: (\d+) releases,", result.stdout)
    assert match is not None, result.stdout
    assert int(match.group(1)) == len(prose), (
        f"the prose sequence must match its own {len(prose)} entries and nothing else — the "
        f"STATUS table beside it carries {len(versions)}, so a pattern reaching into the table "
        f"would report more: {result.stdout}"
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
    only = failures_of(result)
    assert len(only) == 1, (
        "the fixture must fail for placement ALONE — a second failure means it no longer "
        f"distinguishes placement from ordering, which is the whole point:\n{only}"
    )
    assert f"the section for {versions[-1]} sits under Part 5" in only[0]
    assert "Part 5 declares no release range" in only[0]


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
    only = failures_of(result)
    assert len(only) == 1, f"placement alone, or the fixture has stopped discriminating:\n{only}"
    assert "the section for 0.8.0 sits under Part 3, but belongs under Part 4" in only[0]
    assert "Part 3 declares 0.5.0 → 0.7.0" in only[0]


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
    every 0.1.z section nowhere while looking correct on the other thirty.

    Asserts **both** directions, because the red half alone is satisfied by absence: a mutant that
    breaks the prefix pattern altogether also produces this failure, so a test asserting only the
    failure passes whether the form is read correctly or not at all. A mutation run found exactly
    that — the same shape as a containment test satisfied by a path that does not exist.
    """
    root = _tree(tmp_path, versions=_versions())
    roadmap = root / "docs" / "ROADMAP.md"
    intact = roadmap.read_text(encoding="utf-8")

    baseline = run(str(root))
    assert baseline.returncode == 0, (
        "with `0.1.x` intact the 0.1.z section must be *accepted* — this is the half that fails "
        f"when the prefix form stops being read at all:\n{baseline.stderr}"
    )

    roadmap.write_text(
        intact.replace(
            "# Part 1 · The engine — `0.1.x`",
            "# Part 1 · The engine — `0.1.z`",  # not a form the gate knows
        ),
        encoding="utf-8",
    )
    result = run(str(root))

    assert result.returncode == 1
    assert "the section for 0.1.0 sits under Part 1" in result.stderr
    assert "Part 1 declares no release range" in result.stderr


def test_a_range_like_string_in_a_part_title_is_not_mistaken_for_the_range(tmp_path: Path) -> None:
    """The range is matched at the **end** of the heading, and this is what that buys.

    A title that mentions versions — "The 0.2.0 to 0.4.0 era", written with the arrow — contains
    the closed-range shape before the real range. An unanchored search takes the leftmost match,
    so the Part would
    silently claim the versions named in its *prose* and disown the ones it actually holds. Nothing
    in the real document does this today, which is exactly why the property needs a test rather
    than a docstring: a future Part title is where it would first appear.
    """
    versions = _versions()
    root = _tree(tmp_path, versions=versions)
    roadmap = root / "docs" / "ROADMAP.md"
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "# Part 3 · Links — `0.5.0` → `0.7.0`",
            "# Part 3 · The `0.2.0` → `0.4.0` era, revisited — `0.5.0` → `0.7.0`",
        ),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 0, (
        "Part 3 still declares 0.5.0 → 0.7.0; the range in its title must not be read instead:\n"
        + result.stderr
    )


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
    assert "`# Part` heading(s), fewer than the 5 floor" in result.stderr


def test_the_real_documents_are_complete_from_their_declared_starts() -> None:
    """The invariant itself. Also pins the arithmetic that makes the numbers reconcile: the
    per-release sections are 45 with 0.11.0 declared absent, and STATUS's table is 41 because it
    opens at 0.2.0 and the five 0.1.x engine releases predate it."""
    result = run()
    assert result.returncode == 0, result.stderr
    assert "complete from 0.1.0 to" in result.stdout
    assert "complete from 0.2.0 to" in result.stdout, "STATUS's table declares a later start"
    assert "complete from 0.16.0 to" in result.stdout, "the prose list declares a later start"
    assert "declared absent: 0.11.0" in result.stdout, (
        "an exception must be named on a green run — an allowance nobody can see is one nobody "
        "retires"
    )
    assert result.stdout.count("declared absent: 0.30.3") == 2, (
        "0.30.3 is declared absent from both PyPI lists and must be named on a green run, for the "
        "same reason 0.11.0 is"
    )


def test_a_deleted_first_row_is_caught_because_the_start_is_declared(tmp_path: Path) -> None:
    """The whole reason the start is a constant rather than an observation.

    Delete the *oldest* row of a sequence and a derived start simply moves up: the sequence is
    still sorted, still contiguous, still internally consistent, and the gate reports green on
    precisely the deletion it exists to catch. The fixture's STATUS table opens at 0.2.0 like the
    real one, so removing 0.2.0 would move a derived start to 0.3.0 and hide itself.
    """
    versions = _versions()
    opens_at_second = versions[1:]  # mirrors the real table, which starts at 0.2.0
    without_first = opens_at_second[1:]

    green = run(str(_tree(tmp_path / "a", versions=versions, status_versions=opens_at_second)))
    assert green.returncode == 0, green.stderr

    result = run(str(_tree(tmp_path / "b", versions=versions, status_versions=without_first)))

    assert result.returncode == 1
    assert "docs/STATUS.md — the release roadmap table: 1 release(s) missing — 0.2.0" in (
        result.stderr
    )
    assert "declares it starts at 0.2.0" in result.stderr


def test_a_release_missing_from_the_middle_is_caught(tmp_path: Path) -> None:
    """The ordinary case, and the one a sorted-sequence check is blindest to: every remaining pair
    is still in order, so nothing about the ordering changes."""
    versions = _versions()
    gapped = [v for v in versions if v != "0.20.0"]

    result = run(str(_tree(tmp_path, versions=versions, status_versions=gapped)))

    assert result.returncode == 1
    only = failures_of(result)
    assert len(only) == 1, (
        f"a gap leaves every surviving pair sorted, so membership must be the only failure:\n{only}"
    )
    assert "1 release(s) missing — 0.20.0" in only[0]


def test_a_release_before_a_sequences_declared_start_is_not_required(tmp_path: Path) -> None:
    """STATUS's table opens at 0.2.0 and must not be asked for the 0.1.x releases that predate it.
    Without this, the declared start would be decoration and every sequence would be required to
    carry the union."""
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, status_versions=versions[1:])))

    assert result.returncode == 0, result.stderr


def test_a_lagging_sequence_need_not_have_reached_the_newest_release(tmp_path: Path) -> None:
    """The hold-back window, from the membership side: an entry is written only once it has been
    verified from the index, so the newest release is legitimately absent for a while."""
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=versions[:-1])))

    assert result.returncode == 0, result.stderr


def test_a_lagging_sequence_may_not_have_a_hole_below_its_own_newest(tmp_path: Path) -> None:
    """The bound on that exemption, and the test that keeps it from becoming a hole.

    Lagging permits *not having got there yet* — a suffix that is missing. It does not permit a gap
    underneath, which is a lost entry rather than an unwritten one. Without this the exemption
    would excuse any absence in the whole sequence.
    """
    versions = _versions()
    lagging_with_hole = [v for v in versions[:-1] if v != "0.20.0"]

    result = run(str(_tree(tmp_path, versions=versions, prose_versions=lagging_with_hole)))

    assert result.returncode == 1
    assert "the Published on PyPI prose: 1 release(s) missing — 0.20.0" in result.stderr


def test_a_lag_within_the_declared_bound_stays_green(tmp_path: Path) -> None:
    """The half that gets skipped.

    `MAX_VERIFICATION_LAG` is 2, so a list two releases behind is still legitimate — one unverified
    cut plus one slip. A bound that also reddened the normal hold-back window would be turned off
    within a week, so the green case is as much the specification as the red one.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=versions[:-2])))

    assert result.returncode == 0, result.stderr


def test_a_lag_past_the_declared_bound_fails_and_names_both_causes(tmp_path: Path) -> None:
    """Three behind is not latency any more.

    The ceiling for a lagging sequence is that sequence's own maximum — an echo of the document
    being checked — so without this bound, deleting its newest entry drops the ceiling with it and
    the deletion hides itself. That is the defect refused at the *lower* bound surviving four lines
    away at the upper one.

    The message must name **both** causes and choose neither: an entry deleted and an entry not yet
    written are indistinguishable from the documents, and a gate that guessed would be wrong half
    the time and confident every time.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, prose_versions=versions[:-3])))

    assert result.returncode == 1
    only = failures_of(result)
    assert len(only) == 1, f"the lag bound alone should fire here:\n{only}"
    assert "3 releases behind" in only[0]
    assert "past the declared lag of 2" in only[0]
    assert "an entry was deleted" in only[0] and "verification has stopped" in only[0], (
        "naming one cause would be a guess the documents cannot support"
    )


def test_the_lag_bound_does_not_apply_to_a_sequence_that_may_not_lag(tmp_path: Path) -> None:
    """A strict sequence that is behind is caught by the newest-differs check, never by the lag
    bound — and it is the *ceiling* that scopes this, not a second condition.

    A strict sequence's ceiling is the newest release overall, so nothing can be above it and the
    lag branch cannot fire. That is why there is no `newest_may_lag` test beside the bound: a
    mutation run deleted one and survived, because the condition was unobservable. What this test
    pins is the observable consequence — a strict sequence three behind reports the newest-differs
    failure and no lag failure.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, status_versions=versions[:-3])))

    assert result.returncode == 1
    assert "releases behind" not in result.stderr, (
        "a strict sequence is caught by the newest-differs check, not by the lag bound"
    )
    assert "the newest release differs between sequences" in result.stderr


def _roadmap_of(root: Path) -> Path:
    return root / "docs" / "ROADMAP.md"


def test_a_range_appended_to_a_rangeless_part_cannot_silence_placement(tmp_path: Path) -> None:
    """The exploit an adversarial audit found in this check, reproduced.

    File a release section under the rangeless final Part — the 0.25.3 and 0.27.1 defect — and the
    gate says so. Then append that Part's *missing* range to its heading and the same tree passes:
    twenty characters, exit 0, and the only trace is a green line changing `holding no releases:
    Part 5` to `holding no releases: none`.

    The range cannot be declared in the tool (reading it from the heading is what stops the mapping
    drifting), so it is constrained instead — two Parts may not claim the same version. Part 4
    already declares `0.8.0` onward, which is exactly what stops Part 5 doing so.
    """
    versions = _versions()
    root = _tree(tmp_path, versions=versions)
    _roadmap_of(root).write_text(
        "| Release | Adds |\n|---|---|\n"
        + "".join(f"| **[{v}](#anchor-{v})** | 20260101 00:00 | something |\n" for v in versions)
        + "\n"
        + _parts(versions, misfile=versions[-1], into=4),
        encoding="utf-8",
    )
    caught = run(str(root))
    assert caught.returncode == 1, "the misfiling itself must be caught first"
    assert f"the section for {versions[-1]} sits under Part 5" in caught.stderr

    roadmap = _roadmap_of(root)
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "# Part 5 · What is not built",
            "# Part 5 · What is not built — `0.8.0` onward",  # the twenty characters
        ),
        encoding="utf-8",
    )
    result = run(str(root))

    assert result.returncode == 1, (
        "appending a range to the Part must not make the misfiled section legitimate:\n"
        + result.stdout
    )
    assert "Part 4 and Part 5 both claim releases in the same range" in result.stderr


def test_parts_must_ascend_with_the_document(tmp_path: Path) -> None:
    """A section's holder is the nearest Part above it, so position only means something if the
    Parts run in version order. Descending Parts would make 'the nearest heading above' and 'the
    Part whose range holds it' answer different questions without either being wrong."""
    versions = _versions()
    root = _tree(tmp_path, versions=versions)
    roadmap = _roadmap_of(root)
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "# Part 2 · The middle — `0.2.0` → `0.4.0`",
            "# Part 2 · The middle — `0.9.0` → `0.9.9`",  # now above Part 3's range
        ),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 1
    # Naming the pair, not just the sentence. A mutation run flipped the comparison and this test
    # still passed: with `>` a *different*, correctly-ordered pair fires and prints the same words.
    # Asserting the message is asserting that something went wrong, not that the right thing did.
    assert "Part 3 declares 0.5.0 but follows Part 2 which declares 0.9.0" in result.stderr, (
        result.stderr
    )
    assert "must ascend with the document" in result.stderr


def test_demoting_the_last_part_heading_fails_the_floor(tmp_path: Path) -> None:
    """The floor was one below the real count, which made it a floor with a bypass.

    Demote `# Part 5` to `## Part 5` and the document has four Parts — passing a floor of four
    exactly — while every section beneath the demoted heading is re-attributed to Part 4, whose
    range is `0.8.0` onward and therefore holds everything. Parts are never removed, so a floor at
    the real count only ever holds.
    """
    versions = _versions()
    root = _tree(tmp_path, versions=versions)
    roadmap = _roadmap_of(root)
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace(
            "# Part 5 · What is not built", "## Part 5 · What is not built"
        ),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 1
    assert "`# Part` heading(s), fewer than the 5 floor" in result.stderr


# --- The seventh sequence: the **Published versions** row -----------------------------------
#
# It is the only sequence that is not a run of lines. The whole enumeration is one table cell, and
# the rest of that cell carries version numbers in prose — so these tests are as much about the
# `within` anchor holding its scope as about order. The defect they descend from: the row sat four
# releases behind (0.27.0, 0.27.2, 0.28.0, 0.28.1) through green runs of every gate here, because
# the check next door read the *prose* forty lines above it and reported those releases present.
# They were — in the sequence next door.


def test_the_row_and_the_prose_are_two_sequences_not_one(tmp_path: Path) -> None:
    """On the real documents, both are named and they carry different counts.

    The failure this guards is not a wrong number, it is a pattern quietly reading the *other*
    list: the two sequences live in one file under one heading, forty lines apart, and if the row's
    anchor drifted onto the prose the gate would report seven green sequences while checking six
    lists and one duplicate. Different counts is what proves they are different lists.
    """
    result = run()
    assert result.returncode == 0, result.stderr
    row = re.search(r"the Published versions row: (\d+) releases,", result.stdout)
    prose = re.search(r"the Published on PyPI prose: (\d+) releases,", result.stdout)
    assert row is not None and prose is not None, result.stdout
    # 41 versions carried files on 20260823 02:22 UTC, counted from
    # https://pypi.org/simple/pinakes/. A literal, and a floor rather than an equality: the row
    # only grows. The prose begins at 0.16.0 and is shorter by construction.
    assert int(row.group(1)) >= 41, result.stdout
    assert int(row.group(1)) > int(prose.group(1)), (
        "the row starts at 0.2.2 and the prose at 0.16.0, so the row must be the longer list; "
        "equal counts would mean one anchor is reading the other's list"
    )


def test_a_release_missing_from_the_row_is_named_even_though_the_prose_has_it(
    tmp_path: Path,
) -> None:
    """The defect itself, in the arrangement that hid it.

    Every other sequence carries 0.20.0 — including the *Published on PyPI* prose in the same file
    under the same heading. Only the row has lost it, and every surviving pair in the row is still
    sorted. A gate checking order alone reports green here, and did.
    """
    versions = _versions()
    gapped = [v for v in versions if v != "0.20.0"]

    result = run(str(_tree(tmp_path, versions=versions, row_versions=gapped)))

    assert result.returncode == 1
    only = failures_of(result)
    assert len(only) == 1, (
        f"the row alone lost it, so membership on the row must be the only failure:\n{only}"
    )
    assert only[0].startswith("docs/STATUS.md — the Published versions row:"), only[0]
    assert "1 release(s) missing — 0.20.0" in only[0], only[0]


def test_the_row_drifting_behind_the_prose_beside_it_is_caught(tmp_path: Path) -> None:
    """The shape the real drift had: the row simply stops early while the prose carries on.

    The row is rewritten whole rather than appended to, so it does not fall behind by one the way
    the prose does — it is forgotten, and the gap is however many releases shipped since anyone
    last retyped the cell. Three is already past the declared lag, and by then the not-behind rule
    has been red for three releases: both fire, and the test asserts both.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, row_versions=versions[:-3])))

    assert result.returncode == 1
    only = failures_of(result)
    # Both bounds, and both are about the row: three behind is past the declared lag, and the
    # prose beside it carries all three. Asserting one would mean either bound could be deleted
    # while this stayed green — and the point of the pair is that they catch the drift at
    # different moments, the tight one at its first commit and the loose one at its third.
    assert len(only) == 2, f"the drift trips the not-behind rule and the lag bound:\n{only}"
    assert all(line.startswith("docs/STATUS.md — the Published versions row:") for line in only), (
        only
    )
    not_behind = [line for line in only if "the Published on PyPI prose at" in line]
    lag = [line for line in only if "releases behind" in line]
    assert len(not_behind) == 1 and len(lag) == 1, only
    assert f"newest {versions[-4]}" in not_behind[0], not_behind[0]
    assert f"at {versions[-1]}" in not_behind[0], not_behind[0]
    assert "3 releases behind" in lag[0], lag[0]
    assert f"newest here {versions[-4]}" in lag[0], lag[0]
    assert f"newest overall {versions[-1]}" in lag[0], lag[0]


def test_the_prose_beside_the_row_is_not_read_as_part_of_it(tmp_path: Path) -> None:
    """The scoping, proved by a tree that only passes if it holds.

    `_row` writes version numbers *after* the enumeration and in descending order, mirroring the
    real cell. If the `within` anchor stopped scoping — or were replaced by a bare pattern over the
    file — those trailing numbers would join the sequence and it would read as unsorted. So a green
    run here is the assertion, and the count is what says which list was read.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions)))

    assert result.returncode == 0, result.stderr
    match = re.search(r"the Published versions row: (\d+) releases,", result.stdout)
    assert match is not None, result.stdout
    assert int(match.group(1)) == len(versions), (
        "the row must contain exactly the enumeration — more means the trailing prose was read "
        f"into it, fewer means the anchor is clipping it:\n{result.stdout}"
    )


def test_a_renamed_row_matches_nothing_rather_than_passing_vacuously(tmp_path: Path) -> None:
    """The anchor's own vacuity check.

    A `within` that matches nothing yields an empty sequence, and an empty sequence is sorted by
    definition — the one way a check like this dies quietly. Reformat or rename the row and the
    floor fires in the commit that does it.
    """
    versions = _versions()
    root = _tree(tmp_path, versions=versions)
    status = root / "docs" / "STATUS.md"
    status.write_text(
        status.read_text(encoding="utf-8").replace(
            "| Published versions |", "| Versions published |"
        ),
        encoding="utf-8",
    )

    result = run(str(root))

    assert result.returncode == 1
    only = failures_of(result)
    assert len(only) == 1, f"the floor on the row alone should fire here:\n{only}"
    assert only[0].startswith("docs/STATUS.md — the Published versions row:"), only[0]
    assert "matched 0 release(s)" in only[0], only[0]
    assert "stopped matching what it names" in only[0], only[0]


def test_a_second_row_is_refused_rather_than_read_first(tmp_path: Path) -> None:
    """Two regions is a different fault from none, and is not folded into it.

    Taking the first of several matches would splice two lists into one sequence and call it
    sorted — the "derived, never declared" mistake this module refuses everywhere else, one layer
    down, with the anchor deciding for itself which region it meant.
    """
    versions = _versions()
    root = _tree(tmp_path, versions=versions, extra_row=_row(list(reversed(versions))))

    result = run(str(root))

    assert result.returncode == 1
    assert "a region this gate reads is no longer unique" in result.stderr, result.stderr
    assert "matched 2 regions" in result.stderr, result.stderr
    assert "the Published versions row" in result.stderr, result.stderr
    assert failures_of(result) == [], (
        "this stops the gate before any sequence is checked, so it must not also be reported as "
        f"an ordering failure:\n{result.stderr}"
    )


def test_a_within_anchor_with_the_wrong_number_of_groups_is_refused_at_import(
    tmp_path: Path,
) -> None:
    """The region is what the group captures, so a mis-specified anchor is a programming error in a
    constant and fails when the module is built rather than when a document is read.

    Zero groups would capture the whole match — the row including its label — and two would make
    which one is meant a matter of position.
    """
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('rog', {str(TOOL)!r})\n"
        "assert spec and spec.loader\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "for anchor in (r'^\\| Published versions \\| \\*\\*.+?\\*\\*', r'^(a)(b)'):\n"
        "    try:\n"
        "        mod.Sequence('docs/X.md', 'a row', mod.NUM, ascending=True,\n"
        "                     starts_at=(0, 0, 0), within=anchor)\n"
        "    except ValueError as exc:\n"
        "        print('refused:', exc)\n"
        "    else:\n"
        "        sys.exit('accepted an anchor with the wrong group count: ' + anchor)\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(probe)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("refused:") == 2, result.stdout
    assert "has 0." in result.stdout and "has 2." in result.stdout, result.stdout


def test_the_row_may_not_lag_the_prose_recording_the_same_verification(tmp_path: Path) -> None:
    """The tight bound the lag constant is only a loose backstop for.

    Both lists record one event — a release verified from the index — so the prose naming a release
    the row omits is not latency. It is the row having been forgotten by a sweep that remembered
    the prose, which is how both recorded drifts began. One behind is inside `MAX_VERIFICATION_LAG`
    and invisible to every other check here, and one behind is where both drifts started.
    """
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, row_versions=versions[:-1])))

    assert result.returncode == 1
    only = failures_of(result)
    assert len(only) == 1, (
        f"one behind is within the lag bound and leaves no hole, so this must be the only "
        f"failure — if the lag bound also fired, this test is not about what it says:\n{only}"
    )
    assert only[0].startswith("docs/STATUS.md — the Published versions row:"), only[0]
    assert f"newest {versions[-2]}" in only[0], only[0]
    assert "the Published on PyPI prose" in only[0], only[0]
    assert f"at {versions[-1]}" in only[0], only[0]


def test_the_row_may_still_lag_the_release_documents_alongside_the_prose(tmp_path: Path) -> None:
    """And the rule must not over-fire, which is the half that makes it usable.

    Between cutting a release and verifying it on the index, *both* lists are legitimately a
    release behind CHANGELOG — measured as the ordinary state in 53 of the 67 commits carrying
    both. A rule that went red there would be turned off within a week.
    """
    versions = _versions()
    behind = versions[:-1]
    result = run(
        str(_tree(tmp_path, versions=versions, row_versions=behind, prose_versions=behind))
    )

    assert result.returncode == 0, result.stderr


def test_a_not_behind_naming_no_sequence_is_refused_when_the_module_is_built(
    tmp_path: Path,
) -> None:
    """A `not_behind` pointing at a label that does not exist would disable itself in silence —
    the failure mode this whole module is written against, one layer up in the constants.

    It feeds the validator a **bad** sequence, not only the real constants. Handing a guard the
    input it already validates asserts nothing about the guard: that test passes whether or not
    the refusal exists, which is how E7's tautological guard-test got written.
    """
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('rog', {str(TOOL)!r})\n"
        "assert spec and spec.loader\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "declared = [s for s in mod.SEQUENCES if s.not_behind is not None]\n"
        "assert declared, 'no sequence declares not_behind, so the guard guards nothing'\n"
        "mod._validate_not_behind(mod.SEQUENCES)\n"
        "bogus = mod.Sequence('docs/STATUS.md', 'a row', mod.NUM, ascending=True,\n"
        "                     starts_at=(0, 0, 0), not_behind=('docs/STATUS.md', 'no such list'))\n"
        "try:\n"
        "    mod._validate_not_behind((bogus,))\n"
        "except ValueError as exc:\n"
        "    print('refused:', exc)\n"
        "else:\n"
        "    sys.exit('accepted a not_behind naming a sequence that does not exist')\n"
        "print('declared:', len(declared))\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(probe)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "declared: 1" in result.stdout, result.stdout


# --- 0.30.3: prepared, never published (20260830) ---------------------------------------------


def _gate_module() -> Any:
    """The tool as an importable module, so a test can read the declarations it ships with.

    Same idiom as `tests/test_graph_channel.py`'s loader, `sys.modules` registration included: a
    module executed outside it raises on `dataclass`, which resolves `sys.modules[cls.__module__]`
    while the module is still executing.
    """
    spec = importlib.util.spec_from_file_location("release_order_gate", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["release_order_gate"] = module
    try:
        spec.loader.exec_module(module)
    finally:
        del sys.modules["release_order_gate"]
    return module


def test_0303_is_declared_absent_from_the_published_lists_and_from_nothing_else() -> None:
    """**The scope is the whole claim.** 0.30.3 was prepared 20260825, never tagged, and reached no
    index — so it is absent from what PyPI serves and present everywhere a release *document* is
    recorded. A blanket exclusion would make the gate green by erasing that distinction, which is
    the false claim the declaration exists to refuse, so this pins the two sequences that carry it
    and the five that must not.
    """
    carried = {
        (sequence.path, sequence.what)
        for sequence in _gate_module().SEQUENCES
        if (0, 30, 3) in sequence.absent
    }
    assert carried == {
        ("docs/STATUS.md", "the Published on PyPI prose"),
        ("docs/STATUS.md", "the Published versions row"),
    }, "0.30.3 is absent from what an index serves, and from nothing else"


def _published_but_for_0303(tmp_path: Path) -> Path:
    """A tree in the shape `main` takes **after** the post-publish sweep: 0.31.0 present in both
    PyPI lists, so 0.30.3 is an interior hole rather than the tail.

    That shape is the whole point. Both sequences declare `newest_may_lag`, so before the sweep
    0.30.3 is merely the newest thing missing and the gate is legitimately green — which is why
    this control cannot be run against the real documents until the sweep lands, and is built here
    instead.
    """
    versions = [f"0.{n}.0" for n in range(1, 31)] + ["0.30.3", "0.31.0"]
    published = [v for v in versions if v != "0.30.3"]
    return _tree(tmp_path, versions=versions, prose_versions=published, row_versions=published)


def test_a_release_that_reached_no_index_is_declared_absent_rather_than_tolerated(
    tmp_path: Path,
) -> None:
    """The green half: with the declaration, an interior hole in both PyPI lists passes **and is
    named in the output**. A tolerated gap and a declared one look identical from an exit status."""
    result = run(str(_published_but_for_0303(tmp_path)))

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("declared absent: 0.30.3") == 2


def test_removing_that_declaration_turns_both_published_lists_red_and_nothing_else(
    tmp_path: Path,
) -> None:
    """**The control, and the reason the test above is not self-satisfying.** A declared absence
    that nothing depends on is indistinguishable from a gate that never looked: both are green.

    So the same tree is run with `(0, 30, 3)` removed from every sequence that declares it, and the
    gate must go red on exactly the two PyPI lists — never on CHANGELOG's headings or link
    definitions, ROADMAP's table or sections, or STATUS's release roadmap, where 0.30.3 is a real
    release document and stays expected.
    """
    root = _published_but_for_0303(tmp_path)
    script = (
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('rog', {str(TOOL)!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules['rog'] = module\n"
        "assert spec.loader is not None\n"
        "spec.loader.exec_module(module)\n"
        "stripped = [s.what for s in module.SEQUENCES if s.absent.pop((0, 30, 3), None)]\n"
        "assert len(stripped) == 2, stripped\n"
        f"sys.exit(module.main([{str(root)!r}]))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )

    assert result.returncode == 1, result.stdout
    missing = [line for line in failures_of(result) if "missing — 0.30.3" in line]
    assert len(missing) == 2, failures_of(result)
    assert any("the Published on PyPI prose" in line for line in missing)
    assert any("the Published versions row" in line for line in missing)
    assert failures_of(result) == missing, "only the two PyPI lists may go red"
