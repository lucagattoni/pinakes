"""Compare a register's documented row counts against the files it names.

**Why this exists.** On 20260904 the process-review harvest's `README.md` stated three different row
counts for one dataset, and the one under its own *"the two questions this harvest was steered to
answer"* heading was a figure that had been withdrawn twice — 4.4x too high, fourteen lines below
the block withdrawing it. Nothing was wrong with the file on disk. The register describing it had
simply never been compared to it.

**Why this check is possible when the sibling one is not.** The same afternoon produced a defect
that is undetectable in principle: an unquoted heredoc eats inline code spans, and any detector must
ignore code spans to look for the gap, which performs the same deletion. This check has the opposite
shape. A documented row count and the file it names are **two artifacts of one act**, so they can
disagree, and a disagreement means something. That is the whole test for whether a gate is worth
writing: can it be made to fail on a known-bad input? Here it can, and
`tests/test_register_gate.py` constructs one and asserts the failure *before* asserting the pass.

**The pattern below admits a hyphen on purpose.** The first attempt at this comparison used
`[a-z_]+\\.tsv`, which cannot match `ci-runs.tsv`; it reported a clean fifteen of fifteen and said
nothing about the sixteenth row, because a selector that cannot fire does not fail — it succeeds
against the wrong population. The register's own file names are the population, so the pattern is
written to match every name the directory can hold.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

#: A register row: `| `name.tsv` | 1,234 | ... |`. The name class admits `-` and `.` deliberately.
ROW = re.compile(r"^\|\s*`([A-Za-z0-9_.\-]+\.tsv)`\s*\|\s*([\d,]+)\s*\|", re.MULTILINE)


def documented(register: Path) -> list[tuple[str, int]]:
    """Every `(filename, claimed row count)` the register's table states."""
    return [
        (name, int(count.replace(",", "")))
        for name, count in ROW.findall(register.read_text(encoding="utf-8"))
    ]


def data_rows(path: Path) -> int:
    """Rows in a TSV, excluding its header line."""
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def disagreements(register: Path, directory: Path) -> tuple[list[str], int]:
    """Every way the register and the directory disagree, and how many rows were compared.

    Returns the problems and the comparison count together so a caller can distinguish *clean* from
    *vacuous*: zero problems over zero rows is not a pass, and the count is what says so.
    """
    problems: list[str] = []
    rows = documented(register)
    for name, claimed in rows:
        target = directory / name
        if not target.is_file():
            problems.append(f"{name}: register claims {claimed:,} rows, but the file is missing")
            continue
        actual = data_rows(target)
        if actual != claimed:
            problems.append(f"{name}: register says {claimed:,} rows, file has {actual:,}")
    listed = {name for name, _ in rows}
    for found in sorted(p.name for p in directory.glob("*.tsv")):
        if found not in listed:
            problems.append(f"{found}: present in {directory}, absent from the register")
    return problems, len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "register", type=Path, help="the Markdown file whose table documents the datasets"
    )
    parser.add_argument(
        "directory", type=Path, help="the directory holding the .tsv files it describes"
    )
    args = parser.parse_args(argv)

    if not args.register.is_file():
        print(f"register-gate: no such register: {args.register}", file=sys.stderr)
        return 2
    problems, compared = disagreements(args.register, args.directory)
    for problem in problems:
        print(f"register-gate: {problem}", file=sys.stderr)
    # The count is printed on success too: "0 mismatched" over 0 rows is a vacuous pass, and the
    # only thing that distinguishes it from a real one is this number.
    print(f"register-gate: {compared} documented row(s) checked, {len(problems)} disagreeing")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
