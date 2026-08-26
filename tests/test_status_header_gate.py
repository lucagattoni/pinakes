"""`tools/status_header_gate.py`, driven as a subprocess — one test per branch.

A subprocess rather than an import, for the reason `tests/test_fragments.py` gives: it exercises
the same artifact `check.sh` and CI run, argument parsing included, with no `sys.path` surgery.
`--status-file` exists so a mutated header is only ever written to a temp copy, never to the real
`docs/STATUS.md`; `--expect-version` exists so the disagreeing branch needs no fake package.

The recurring defect these tests exist to catch is a gate that reads the file and never compares
— which would pass any test that only checks exit 0. So every failing branch asserts the *stated
reason*, and the disagreeing branch asserts **both** values appear in it: a message naming only
one version is compatible with comparing that version to itself.

**Layer 2 (D-35, 20260826) reads `R` out of the same file**, so every fixture below is a miniature
`docs/STATUS.md` carrying a *Published versions* row rather than three lines. That is deliberate:
a fixture able to satisfy layer 1 while having no row at all would let layer 2 be deleted with
every test here still green.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

from pinakes import __version__

TOOL = Path(__file__).parent.parent / "tools" / "status_header_gate.py"

HELD = "**Latest release: 1.2.3** — ⏸ **landed on `main`, NOT tagged; `pip install` gets 1.2.2.**"
"""The qualified form, in the shape the real line 3 uses.

D-35's plan records that it passed `SHAPE` **by accident** — the pattern has no `$`, a looseness
its own docstring attributes to the `last reviewed` date — and that **nothing pinned it as legal**.
Anyone tightening that regex would have silently outlawed the state the user sanctioned, with every
test in this file still green. It is pinned now."""


def status(line3: str, *, row: str = "0.2.2, 1.2.1 and 1.2.2", rows: int = 1) -> str:
    """A miniature `docs/STATUS.md`: the header on line 3, and a *Published versions* row whose
    leading bold span is the enumeration `release_order_gate.py`'s `within` anchor carves out."""
    table = "".join(
        f"| Published versions | **{row}** — counted from the index |\n" for _ in range(rows)
    )
    return f"# Status\n\n{line3}\n\n| Thing | Value |\n|---|---|\n{table}"


def write(
    tmp_path: Path, line3: str, *, row: str = "0.2.2, 1.2.1 and 1.2.2", rows: int = 1
) -> Path:
    copy = tmp_path / "STATUS.md"
    copy.write_text(status(line3, row=row, rows=rows))
    return copy


def gate_module() -> Any:
    """The tool imported in-process, for the one branch no fixture can reach: the sequence layer 2
    reads being renamed out of `release_order_gate.SEQUENCES`."""
    spec = importlib.util.spec_from_file_location("status_header_gate_under_test", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False
    )


def test_the_real_status_file_agrees_with_the_real_version() -> None:
    """The invariant itself, with no flags: on a correct tree the gate is green. This is the run
    `check.sh` performs, and it holds between releases because a release bumps `__version__` and
    the header in the same commit (docs/RELEASING.md step 2 + sweep table)."""
    result = run()
    assert result.returncode == 0, result.stderr
    assert f"agree on {__version__}" in result.stdout
    # Layer 2 ran on the real file too, and said which of its two states the tree is in. Without
    # this, a layer 2 that returned 0 unconditionally would be invisible here.
    assert "hold marker" in result.stdout


def test_agreeing_versions_pass(tmp_path: Path) -> None:
    """Published and unmarked: line 3 names 1.2.3, the row's newest entry is 1.2.3, no hold."""
    copy = write(
        tmp_path,
        "**Latest release: 1.2.3** · last reviewed 20260803 22:23",
        row="0.2.2, 1.2.2 and 1.2.3",
    )
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 0, result.stderr
    assert "agree on 1.2.3" in result.stdout
    assert "no hold marker" in result.stdout


def test_disagreeing_versions_fail_naming_both(tmp_path: Path) -> None:
    copy = write(tmp_path, "**Latest release: 1.2.3** · last reviewed 20260803 22:23")
    result = run("--status-file", str(copy), "--expect-version", "9.9.9")
    assert result.returncode == 1
    assert "1.2.3" in result.stderr, "the failure must name the version the header states"
    assert "9.9.9" in result.stderr, "the failure must name the version the package states"
    assert "STATUS.md" in result.stderr, "the failure must name the file to fix"


def test_a_missing_line_fails(tmp_path: Path) -> None:
    """A file too short to have a line 3 at all — the header was deleted, not reworded."""
    copy = tmp_path / "STATUS.md"
    copy.write_text("# Status\n")
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "header is gone" in result.stderr


def test_a_reformatted_line_fails(tmp_path: Path) -> None:
    """The right version in the wrong shape — bold stripped, wording changed — must fail too:
    the parse is anchored to the exact shape precisely so reformatting cannot silence the gate."""
    copy = tmp_path / "STATUS.md"
    copy.write_text("# Status\n\nLatest release: 1.2.3 · last reviewed 20260803 22:23\n")
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "does not start with" in result.stderr


def test_the_header_on_the_wrong_line_fails(tmp_path: Path) -> None:
    """The exact header, one line lower than docs/RELEASING.md's sweep table names. A gate that
    scanned the whole file would pass this file — and would equally pass a stale line 3 with the
    current version buried further down, which is the drift this gate exists to stop."""
    copy = tmp_path / "STATUS.md"
    copy.write_text("# Status\n\n\n**Latest release: 1.2.3** · last reviewed 20260803 22:23\n")
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "does not start with" in result.stderr


# ── Layer 2 — the hold marker against `R`, the newest entry of the *Published versions* row ──
#
# D-35, taken by the user 20260825 12:37. `__version__` means *landed on `main`*, so there is a
# legitimate window in which line 3 names a version `pip install` cannot get — and the marker that
# says so was 0-for-2 on being produced by the release procedure. X7's network rule can require the
# marker when a version is absent from the index; it can never require its *removal*, which is the
# half that is green by construction in every other check here.


def test_a_landed_but_unpublished_version_requires_the_hold_marker(tmp_path: Path) -> None:
    """The sanctioned hold, unannounced. Line 3 names 1.2.3, the row ends at 1.2.2, and `docs/` is
    published on every push — so an unqualified line is publicly false for as long as the hold
    lasts. Both recorded occurrences look exactly like this."""
    copy = write(tmp_path, "**Latest release: 1.2.3** · last reviewed 20260803 22:23")
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "ahead of the" in result.stderr
    assert "1.2.2" in result.stderr, "the failure must name what pip install actually gets"
    assert "⏸" in result.stderr, "…and show the marker to add, or the remedy is a paraphrase"


def test_the_hold_marker_satisfies_layer_two_when_it_names_the_published_version(
    tmp_path: Path,
) -> None:
    """The state `main` was in when this gate was written: landed, untagged, and saying so."""
    copy = write(tmp_path, HELD)
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 0, result.stderr
    assert "hold marker is present" in result.stdout


def test_the_qualified_form_is_legal_and_that_is_now_pinned(tmp_path: Path) -> None:
    """**`SHAPE` has no `$`**, so the qualified form passed it by accident — a looseness its
    docstring attributes to the `last reviewed` date, with nothing anywhere asserting that a
    marker after the closing `**` is allowed. Anyone tightening that regex to `…\\*\\*$` would have
    outlawed the exact state the user sanctioned, and every test in this file would have stayed
    green. Named separately from the test above because it is a claim about `SHAPE`, not about
    layer 2: it must keep passing even if the marker's meaning changes."""
    copy = write(tmp_path, HELD)
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 0, result.stderr
    assert "does not start with" not in result.stderr, (
        "SHAPE has been tightened and the qualified form is no longer legal"
    )


def test_a_hold_marker_naming_the_wrong_published_version_fails(tmp_path: Path) -> None:
    """The marker is a claim about the index — *what `pip install` gets right now* — and an
    unchecked claim about the index is how line 3 came to need a gate. Here the qualifier is a
    release behind the row it sits above, which is a false statement on a published page and is
    invisible to a check that only asks whether a marker is present."""
    copy = write(
        tmp_path,
        "**Latest release: 1.2.3** — ⏸ **landed on `main`; `pip install` gets 1.2.1.**",
    )
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "does not name 1.2.2" in result.stderr
    assert "1.2.1" in result.stderr, "the failure must quote what the marker actually claims"


def test_a_published_version_may_not_keep_the_hold_marker(tmp_path: Path) -> None:
    """**The half nothing else in this repository can see, and the reason layer 2 exists.** The
    row has caught up, so the hold is over and the line still announces it. `SHAPE` stops at the
    closing `**`; none of `release_order_gate.py`'s seven sequences reads line 3's tail; X7's rule
    is *unqualified + absent from the index → red*, which is green here by construction. A stale
    marker would otherwise stand forever."""
    copy = write(
        tmp_path,
        "**Latest release: 1.2.2** — ⏸ **landed on `main`; `pip install` gets 1.2.2.**",
        row="0.2.2, 1.2.1 and 1.2.2",
    )
    result = run("--status-file", str(copy), "--expect-version", "1.2.2")
    assert result.returncode == 1
    assert "claims a hold that is over" in result.stderr
    assert "1.2.2" in result.stderr


def test_a_headline_behind_the_published_row_is_always_red(tmp_path: Path) -> None:
    """`line3 < R`, with or without a marker: the row says a version is published that the headline
    has never heard of. Since line 3 is pinned to `__version__` by layer 1, this means the version
    bump is missing — and the failure says so rather than blaming the row."""
    copy = write(tmp_path, "**Latest release: 1.2.1** · last reviewed 20260803 22:23")
    result = run("--status-file", str(copy), "--expect-version", "1.2.1")
    assert result.returncode == 1
    assert "behind what is published" in result.stderr
    assert "1.2.1" in result.stderr and "1.2.2" in result.stderr


def test_a_row_the_gate_cannot_read_is_a_hard_failure_never_a_skip(tmp_path: Path) -> None:
    """**Decided explicitly: row unreadable → hard fail, never skip.** A layer that quietly stops
    checking when its input goes missing is the shape of everything this increment replaced — the
    file would still pass layer 1, so a reformatted or deleted row would disarm the marker rule
    with every other gate green."""
    copy = tmp_path / "STATUS.md"
    copy.write_text("# Status\n\n**Latest release: 1.2.3** · last reviewed 20260803 22:23\n")
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "no readable *Published versions* row" in result.stderr
    assert "never a skip" in result.stderr


def test_a_second_published_versions_row_fails_rather_than_reading_the_first(
    tmp_path: Path,
) -> None:
    """`release_order_gate.py` refuses a `within` anchor that matches twice rather than resolving
    to the first, because taking the first would let the anchor decide which region it meant. That
    refusal has to reach *this* gate as a failure too — swallowed here, layer 2 would compare line
    3 against whichever list happened to sort first."""
    copy = write(tmp_path, HELD, rows=2)
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "no longer unique" in result.stderr
    assert "2 regions" in result.stderr, "the failure must come from the anchor, not from a guess"


def test_layer_one_runs_first_so_the_ci_negative_check_still_reads_its_reason(
    tmp_path: Path,
) -> None:
    """**A coupling, pinned as one.** `ci.yml`'s *The gate can still fail* step drives this tool
    with `--expect-version 99.99.99` and greps `the header drifted from the release`; its own
    comment says a bare non-zero exit is insufficient, since a crash satisfies that too. This
    fixture would fail *both* layers — the marker is missing as well — so it is exactly the tree on
    which a reordering would silently change which reason comes out."""
    copy = write(tmp_path, "**Latest release: 1.2.3** · last reviewed 20260803 22:23")
    result = run("--status-file", str(copy), "--expect-version", "99.99.99")
    assert result.returncode == 1
    assert "the header drifted from the release" in result.stderr
    assert "hold marker" not in result.stderr, (
        "layer 2 answered first — ci.yml's negative check now greps for a string this gate no "
        "longer prints on that tree"
    )


def test_the_published_row_sequence_still_resolves() -> None:
    """`PUBLISHED_ROW` names a sequence by `(path, what)`, and `release_order_gate.py` has **two**
    sequences over `docs/STATUS.md` forty lines apart. Reading the wrong one is the recorded
    mistake that let the row drift four releases while the gate reported those releases present,
    so the match is on both fields — and a rename over there must not quietly unhook it."""
    module = gate_module()
    assert module._published_row() is not None, (
        f"no sequence in release_order_gate.SEQUENCES matches {module.PUBLISHED_ROW} — layer 2 "
        f"has nothing to read R from"
    )


def test_a_renamed_sequence_fails_rather_than_disabling_layer_two(tmp_path: Path) -> None:
    """The branch no fixture can reach, because it is about the *other* module's constants. With
    the sequence gone, the honest options are to skip layer 2 or to refuse; skipping would delete
    the marker rule in a commit that touches neither this file nor `docs/STATUS.md`."""
    module = gate_module()
    module.SEQUENCES = ()
    copy = write(tmp_path, HELD)
    outcome = module._check_hold_marker(copy, copy.read_text(), " — ⏸ **x**", (1, 2, 3))
    assert outcome == 1


def test_the_marker_must_be_a_parsed_shape_not_a_loose_glyph(tmp_path: Path) -> None:
    """A bare `⏸` with no bold qualifier does not count. The marker's job is to carry a claim —
    which version `pip install` gets — and a glyph alone carries none, while still *looking* like
    a hold to a reader and to any check that greps for the character."""
    copy = write(tmp_path, "**Latest release: 1.2.3** — ⏸ landed on main, not tagged yet")
    result = run("--status-file", str(copy), "--expect-version", "1.2.3")
    assert result.returncode == 1
    assert "ahead of the" in result.stderr, (
        "a bare glyph was accepted as a marker, so the qualifier — the only part that says "
        "anything checkable — became optional"
    )
