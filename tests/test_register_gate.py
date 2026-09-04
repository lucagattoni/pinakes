"""The register gate must be shown able to fail before its passing means anything.

Run as a subprocess rather than imported: this exercises **the same artifact an operator runs by
hand**, argument parsing and exit status included, and needs no `sys.path` surgery the type checkers
cannot follow. The exit status is the point of a gate, so the exit status is what is asserted.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

GATE = Path(__file__).resolve().parents[1] / "tools" / "register_gate.py"

REGISTER = """# Datasets

| file | rows | one row is |
|---|---:|---|
| `alpha.tsv` | 2 | a thing |
| `beta-two.tsv` | 1 | another thing |
"""


def _fixture(tmp_path: Path, *, beta_rows: int = 1) -> Path:
    (tmp_path / "README.md").write_text(REGISTER, encoding="utf-8")
    (tmp_path / "alpha.tsv").write_text("h\na\nb\n", encoding="utf-8")
    (tmp_path / "beta-two.tsv").write_text("h\n" + "x\n" * beta_rows, encoding="utf-8")
    return tmp_path


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), str(root / "README.md"), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_it_fails_on_a_miscounted_register(tmp_path: Path) -> None:
    """The known-bad input. This assertion is what licenses the clean run in the next test."""
    result = _run(_fixture(tmp_path, beta_rows=9))
    assert result.returncode == 1
    assert "beta-two.tsv" in result.stderr
    assert "register says 1 rows, file has 9" in result.stderr


def test_it_passes_on_a_register_that_agrees(tmp_path: Path) -> None:
    result = _run(_fixture(tmp_path))
    assert result.returncode == 0
    assert "2 documented row(s) checked, 0 disagreeing" in result.stdout


def test_a_hyphenated_name_is_seen(tmp_path: Path) -> None:
    """`[a-z_]+\\.tsv` reported a clean fifteen of fifteen by never seeing `ci-runs.tsv`.

    A pattern that skipped `beta-two.tsv` would report *one* row checked and still exit 0, which is
    the failure this asserts against: the count, not the status, is what catches it.
    """
    result = _run(_fixture(tmp_path))
    assert "2 documented row(s) checked" in result.stdout


def test_an_undocumented_file_is_a_disagreement(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    (root / "gamma.tsv").write_text("h\nz\n", encoding="utf-8")
    result = _run(root)
    assert result.returncode == 1
    assert "gamma.tsv" in result.stderr and "absent from the register" in result.stderr


def test_a_missing_file_is_a_disagreement(tmp_path: Path) -> None:
    root = _fixture(tmp_path)
    (root / "alpha.tsv").unlink()
    result = _run(root)
    assert result.returncode == 1
    assert "alpha.tsv" in result.stderr and "missing" in result.stderr


def test_a_missing_register_is_an_error_not_a_pass(tmp_path: Path) -> None:
    """Exit 2, never 0: a gate that cannot find its input must not report success."""
    result = _run(tmp_path)
    assert result.returncode == 2
