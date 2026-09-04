"""Does each injected fake in the test suite actually decide anything?

    python3 tools/vacuous_injection_audit.py            # every pathlib/os/paths injection
    python3 tools/vacuous_injection_audit.py --runs 3   # more repeats per site

`.github/workflows/injection-audit.yml` runs it on Linux, which is the one thing a macOS
checkout cannot do for itself — see *not rulable from one platform* below.

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
  another. Not a defect, and **not rulable from one platform**. This is why the report names
  the interpreter, the platform and `NAME_MAX` beside its counts: a verdict of this kind is a
  claim about an environment, and a report that cannot name its environment cannot state its
  own limit.
* **mis-attributed** — the probe disabled a fake and ran a test that never used it. An injection
  inside a *helper* belongs to every test that calls the helper, which is why the enclosing
  definition is found by column-0 `def` and helpers are expanded to their callers.

Report the split, never the bare count: the count moved 5 → 3 → 2 across three broken instruments,
and every intermediate number was a true statement about a broken measurement.

**Exit status: the *unruled* set, never the vacuous one.** `UNSTABLE`, `INCONCLUSIVE` and a
site with no caller found mean the **instrument** failed to rule, and an audit that cannot
rule a site while exiting 0 reports success for a measurement that did not happen. A
`VACUOUS` row is the opposite — a finding for a person to read and split three ways — so it
prints and exits 0, for the same reason `mutate.py` exits 0 on a survivor.
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

#: The launcher every probe runs its tests through, named once. `environment` rewrites *this*
#: tuple rather than repeating the words, so the line the report prints can never describe a
#: command the probes did not use.
PYTEST = ("uv", "run", "--frozen", "pytest")

#: What `environment` asks the launcher to run. **`NAME_MAX` is in here for a reason specific to
#: this tool**: `mutate.py` needs only the interpreter, while a verdict here can turn on the
#: filesystem — a 300-character filename raises `ENAMETOOLONG` where `NAME_MAX` is 255 and merely
#: fails to be a document where it is not, which is the difference between a redundant fake and a
#: load-bearing one. Printing the number removes the step where a reader has to know it.
_ENVIRONMENT_PROBE = """\
import os, platform, sys
try:
    name_max = os.pathconf(".", "PC_NAME_MAX")
except (OSError, ValueError, AttributeError):  # not every platform answers; say so rather than 0
    name_max = "unknown"
print(
    f"Python {sys.version.split()[0]} on {platform.system()} {platform.release()} "
    f"({platform.machine()}), NAME_MAX={name_max}"
)
"""


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
                *PYTEST,
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


def environment(root: Path) -> str | None:
    """The interpreter and filesystem the *probes* ran on, or `None` if this run could not say.

    **The launcher is asked, never this process** — the same reason `tools/mutate.py` states for
    the same question. The documented invocation is `python3 tools/vacuous_injection_audit.py`,
    which is whatever system Python is on `PATH`, while every probe runs under
    `uv run --frozen pytest` in the project venv. On this machine those are 3.14.7 and 3.13.15 at
    the same moment, so printing the launcher's own `sys.version` would name a Python that decided
    nothing here — worse than saying nothing, because it reads as measured.

    **Why this tool needs the platform and `mutate.py` does not.** This module's own docstring says
    a `VACUOUS` verdict can mean *the real environment does it anyway*, and that such a site is
    **not rulable from one platform**. A report that cannot name the platform it ran on therefore
    cannot state its own most important limit. One extra subprocess for the whole run.

    `None` is returned rather than a guess, and the caller prints that it could not tell.
    """
    try:
        completed = subprocess.run(
            [*PYTEST[:-1], "python", "-c", _ENVIRONMENT_PROBE],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    answer = completed.stdout.strip().splitlines()
    return answer[-1] if completed.returncode == 0 and answer else None


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
    where = environment(ROOT)
    print(
        f"probed under {where}."
        if where is not None
        else "probed under an environment this run could not identify — these verdicts do not "
        "say which interpreter or filesystem produced them, and a VACUOUS row cannot be read "
        "without both."
    )
    for row in vacuous:
        print(f"  VACUOUS   {row}")
    for row in unstable:
        print(f"  NOT RULED {row}")
    print(
        "\nRead the module docstring before acting on a VACUOUS row: it is three findings wearing "
        "one label, and only asserts-nothing is a defect."
    )
    # **The unruled set is the failure; a `VACUOUS` row is a finding to read.** An `UNSTABLE`,
    # `INCONCLUSIVE` or caller-less site means the *instrument* did not rule, and an audit that
    # cannot rule a site while exiting 0 is the "review harness reported success because every
    # agent died" shape this repository has already been caught by. A `VACUOUS` row, by
    # contrast, is three findings wearing one label and only one of them is a defect — so it
    # is printed and judged by a person, for the same reason `mutate.py` exits 0 on a survivor.
    return 1 if unstable else 0


if __name__ == "__main__":
    sys.exit(main())
