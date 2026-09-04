"""Does each injected fake in the test suite actually decide anything?

    python3 tools/vacuous_injection_audit.py            # every pathlib/os/paths injection
    python3 tools/vacuous_injection_audit.py --runs 3   # more repeats per site

**The method, in one sentence: disable a test's `monkeypatch.setattr` line, re-run the test that
owns it, and see whether it still passes.** A test that passes with its own instrument neutralised
cannot tell you the instrument still works — so the day the production code stops calling the
faked name, the test goes on passing while covering nothing. That is not hypothetical here: a
`doctor` test asserted only that the diagnosis *finished*, and a `pnk link` test faked
`Path.is_file` to raise on an interpreter where the real call had stopped raising.

**CLEAR `__pycache__` AROUND EVERY WRITE, AND THIS TOOL DOES.** CPython invalidates bytecode on
(mtime-to-the-second, size), so an edit and its restore inside the same second run from stale
bytecode. The first three versions of this audit did not clear, and **two of fifteen sites returned
a different verdict on repeat**; with clearing, zero of fifteen. The rule was already written down
for mutation harnesses and was missed here because this was called an audit rather than a battery.

**`--runs` exists because a verdict that does not repeat is not a verdict.** Each site is probed at
least twice and only agreeing verdicts are reported.

**"Still passes" is three findings wearing one label, and only the first is a defect:**

* **asserts-nothing** — the assertions do not depend on the injected condition. The real thing.
* **the real environment does it anyway** — a 300-character filename raises `ENAMETOOLONG` for real
  where `NAME_MAX` is 255, so the fake is redundant *on that machine* and may be load-bearing on
  another. Not a defect, and **not rulable from one platform**.
* **mis-attributed** — the probe disabled a fake and ran a test that never used it. An injection
  inside a *helper* belongs to every test that calls the helper, which is why the enclosing
  definition is found by column-0 `def` and helpers are expanded to their callers.

Report the split, never the bare count: the count moved 5 → 3 → 2 across three broken instruments,
and every intermediate number was a true statement about a broken measurement.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = re.compile(r"monkeypatch\.setattr\(\s*(Path|os|paths)\s*,")


def clear_pycache(root: Path) -> None:
    """Every `__pycache__` under `root`. See the module docstring — this is not optional."""
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def enclosing(lines: list[str], index: int) -> str | None:
    """The column-0 `def` that owns `index` — never "the nearest test above", which blames a
    helper's injection on whatever test happens to precede it."""
    for j in range(index, -1, -1):
        match = re.match(r"def (\w+)", lines[j])
        if match:
            return match.group(1)
    return None


def sites(root: Path) -> list[tuple[Path, int, list[str], str]]:
    found: list[tuple[Path, int, list[str], str]] = []
    for path in sorted((root / "tests").glob("test_*.py")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if not TARGET.search(line) or not line.rstrip().endswith(")"):
                continue
            owner = enclosing(lines, i)
            if owner and owner.startswith("test_"):
                targets = [owner]
            else:
                targets = sorted(
                    {
                        m.group(1)
                        for k, text in enumerate(lines)
                        if owner
                        and f"{owner}(" in text
                        and (
                            m := re.match(
                                r"def (test_\w+)",
                                lines[
                                    max(
                                        (
                                            j
                                            for j in range(k, -1, -1)
                                            if re.match(r"def \w+", lines[j])
                                        ),
                                        default=0,
                                    )
                                ],
                            )
                        )
                    }
                )
            found.append((path, i, targets, line.strip()))
    return found


def probe(root: Path, path: Path, index: int, targets: list[str]) -> str:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    lines[index] = " " * (len(lines[index]) - len(lines[index].lstrip())) + "pass  # audit probe\n"
    path.write_text("".join(lines), encoding="utf-8")
    clear_pycache(root)
    try:
        run = subprocess.run(
            [
                "uv",
                "run",
                "--frozen",
                "pytest",
                *(f"tests/{path.name}::{t}" for t in targets),
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=900,
        )
    finally:
        path.write_text(original, encoding="utf-8")
        clear_pycache(root)
    # A skipped test also exits 0, and a skip is not a pass.
    if "no tests ran" in run.stdout or re.search(r"\b0 passed\b", run.stdout):
        return "INCONCLUSIVE"
    return "VACUOUS" if run.returncode == 0 else "sound"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Does each injected fake in the test suite actually decide anything?"
    )
    parser.add_argument("--runs", type=int, default=2, help="probes per site (minimum 2)")
    args = parser.parse_args(argv)
    runs = max(2, args.runs)

    collected = sites(ROOT)
    print(f"{len(collected)} site(s), {runs} probes each, __pycache__ cleared around every write\n")
    vacuous: list[str] = []
    unstable: list[str] = []
    for path, index, targets, text in collected:
        if not targets:
            unstable.append(f"{path.name}:{index + 1}  {text}  -> no caller found")
            continue
        verdicts = {probe(ROOT, path, index, targets) for _ in range(runs)}
        verdict = verdicts.pop() if len(verdicts) == 1 else "UNSTABLE"
        print(f"  [{verdict:12}] {path.name}:{index + 1}  {text[:56]}")
        if verdict == "VACUOUS":
            vacuous.append(f"{path.name}:{index + 1}  {text}  ({', '.join(targets)})")
        elif verdict in ("UNSTABLE", "INCONCLUSIVE"):
            unstable.append(f"{path.name}:{index + 1}  {text}  -> {verdict}")

    print(f"\n{len(collected)} sites · {len(vacuous)} vacuous · {len(unstable)} not ruled")
    for row in vacuous:
        print(f"  VACUOUS   {row}")
    for row in unstable:
        print(f"  NOT RULED {row}")
    print(
        "\nRead the module docstring before acting on a VACUOUS row: it is three findings wearing "
        "one label, and only asserts-nothing is a defect."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
