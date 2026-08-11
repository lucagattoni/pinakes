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


def _tree(root: Path, *, versions: list[str], status_versions: list[str] | None = None) -> Path:
    """A minimal repository whose three documents carry the sequences the gate reads."""
    status_versions = versions if status_versions is None else status_versions
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
        + "".join(f"## {v} — Something · 20260101 00:00\n\nbody.\n\n" for v in versions),
        encoding="utf-8",
    )
    (root / "docs" / "STATUS.md").write_text(
        "| Release | Adds |\n|---|---|\n"
        + "".join(f"| **{v}** ✅ | something |\n" for v in status_versions),
        encoding="utf-8",
    )
    return root


def _versions(count: int = COUNT) -> list[str]:
    return [f"0.{n}.0" for n in range(1, count + 1)]


def test_the_real_documents_are_in_release_order() -> None:
    """The invariant itself, with no arguments: on a correct tree the gate is green. This is the
    run `check.sh` performs."""
    result = run()
    assert result.returncode == 0, result.stderr
    assert "5 sequences in release order" in result.stdout


def test_every_pattern_still_matches_the_real_documents() -> None:
    """The vacuity check, and the reason this file exists as much as the ordering branch does.

    A gate whose patterns have rotted reports success over a document it can no longer read. The
    green run therefore prints what each pattern matched, and this asserts all five are named with
    a real count — reformat a table past recognition and it goes red in the commit that does it,
    rather than quietly measuring nothing.
    """
    result = run()
    assert result.returncode == 0, result.stderr
    for what in (
        "CHANGELOG.md — the release headings",
        "CHANGELOG.md — the link definitions",
        "docs/ROADMAP.md — the release table",
        "docs/ROADMAP.md — the per-release sections",
        "docs/STATUS.md — the release roadmap table",
    ):
        assert what in result.stdout, result.stdout
    counts = [int(m) for m in re.findall(r": (\d+) releases,", result.stdout)]
    assert len(counts) == 5, result.stdout
    assert all(count >= 25 for count in counts), result.stdout


def test_an_ordered_tree_passes(tmp_path: Path) -> None:
    result = run(str(_tree(tmp_path, versions=_versions())))
    assert result.returncode == 0, result.stderr
    assert "5 sequences in release order" in result.stdout


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


def test_a_sweep_that_updates_one_document_and_not_another_is_caught(tmp_path: Path) -> None:
    """Every sequence internally sorted, and the set of them disagreeing — which no per-file
    ordering check can see."""
    versions = _versions()
    result = run(str(_tree(tmp_path, versions=versions, status_versions=versions[:-1])))
    assert result.returncode == 1
    assert "the newest release differs between sequences" in result.stderr
    assert "0.30.0" in result.stderr and "0.29.0" in result.stderr
