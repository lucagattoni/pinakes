"""Run a per-increment mutation battery — the one step of `docs/BUILDING.md` with no guard.

**Why this exists.** Step 4 of [`docs/BUILDING.md`](../docs/BUILDING.md) says: break the code on
purpose, confirm the right test fails, restore. It is the procedure's one *silently-failing* step.
A broken harness prints SURVIVED and KILLED in exactly the same shape a working one does, so the
report reads as evidence either way — and this repository has produced more than a dozen invalid or
destructive runs across ten increments, six of them the identical `git checkout` trap, still
recurring after four write-ups. E5's own words: *"knowing the trap was not enough to avoid it."*

The precedent is `tools/land.py`. When prose has failed repeatedly against a class of mistake that
fails *silently*, the rule stops being a rule and becomes a tool. Everything below is one of those
rules, turned into a refusal:

* **the target must match `HEAD`** — the six recorded incidents all end `git checkout <file>`, which
  restores to the last commit and takes any uncommitted fix in that file with it. This script never
  runs `git checkout`; it restores from a byte snapshot taken before the write. But a snapshot lives
  in memory, and **`SIGKILL` cannot be handled** — measured below — so after a hard kill the only
  recovery *is* `git checkout <file>`, and the refusal is what makes that recovery correct rather
  than destructive. It is the last line of defence, not a formality;
* **the anchor must match exactly once** — `str.replace` that matches nothing returns the string
  unchanged and reports to no one. The mutant is never written, the tests pass, the row says
  SURVIVED;
* **`__pycache__` is cleared after the write and after the restore** — CPython validates a `.pyc` on
  `(mtime-to-the-second, size)`. A *same-length* mutant applied within the same wall-clock second as
  the previous run changes neither, so the stale bytecode runs and the row says SURVIVED. Measured
  here 6 times out of 6 before this script existed (T3);
* **pytest never sees `-x`** — with it, the report is about test ordering rather than about the
  mutant;
* **an invalid mutant is its own outcome** — pytest exits 2 with a collection `<error>`, not a
  `<failure>`. T4 misread that in both directions: once as a kill, once as a survival;
* **the restore happens in a `finally`, and its bytes are verified** — a run killed mid-battery must
  not poison the mutants after it (L6);
* **a batch with no kills exits non-zero.** A run where nothing died is a broken harness, not a
  clean bill. `--allow-zero-kills` is for the rare deliberate probe of a backstop already documented
  as unpinned.

**Two failure modes measured while building this, that the plan did not name.** Both are the harness
lying in the direction it exists to prevent, and both are caught by one pre-flight run per selector:

* **a test that skips reads exactly like a test that passes** — pytest exits 0 either way. This repo
  skips constantly (`pdf`, `paid`, `model`, a missing extra), so a battery aimed at a selector that
  skips in this checkout would report SURVIVED for every mutant in it;
* **a selector that is already red reports KILLED for every mutant** — including the ones nothing
  catches.

So before any file is touched, every selector in the battery is run unmutated and must collect at
least one test, actually *run* at least one, and pass. A battery cannot report on a selector whose
baseline it has not seen.

**What it deliberately does not do.** Cross-file mutants, generated mutation operators and mutating
test files: those stay manual, and the tool refuses loudly rather than approximating them. A row
here is still a claim about *one assertion*, never about a commit.

    python3 tools/mutate.py battery.toml
    python3 tools/mutate.py battery.toml --allow-zero-kills

The battery is TOML — `tomllib` is stdlib, and `'''…'''` survives quotes, backslashes and newlines
in an anchor without escaping, which is most of what source code is made of:

    # Optional. Default: ["uv", "run", "--frozen", "pytest"]
    pytest = ["uv", "run", "--frozen", "pytest"]

    [[mutant]]
    name = "the depth cap is a min(), not a pass-through"
    file = "src/pinakes/graph/traverse.py"
    old  = '''depth = min(depth, self.max_depth)'''
    new  = '''depth = depth'''
    kills = "tests/test_traverse.py::test_a_walk_deeper_than_the_cap_is_clamped"

`pytest` lives in the battery rather than on the command line because a battery is a per-increment
working file, not a portable artifact — one home for the setting, and the tests can point it at
`sys.executable -m pytest` without a flag that would otherwise exist only for them.
"""

from __future__ import annotations

import argparse
import importlib.util
import shlex
import signal
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ElementTree
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from types import FrameType
from typing import cast

DEFAULT_PYTEST: tuple[str, ...] = ("uv", "run", "--frozen", "pytest")

#: pytest's own exit codes, named. 1 and 0 are the two a mutation run is *allowed* to end on; the
#: rest all mean the report would be about something other than the mutant.
PYTEST_TESTS_FAILED = 1
PYTEST_INTERRUPTED = 2
PYTEST_USAGE_ERROR = 4
PYTEST_NO_TESTS_COLLECTED = 5


class MutationError(Exception):
    """A refusal with a remedy. Never raised for a condition the script could fix itself."""


class Outcome(Enum):
    """What one mutant did. `ERRORED` is deliberately neither of the other two (T4)."""

    KILLED = "KILLED"
    SURVIVED = "SURVIVED"
    ERRORED = "ERRORED"


@dataclass(frozen=True)
class Mutant:
    """One edit, and the tests that are supposed to notice it."""

    name: str
    path: Path
    old: str
    new: str
    selectors: tuple[str, ...]

    @property
    def edit(self) -> str:
        return f"{_oneline(self.old)} → {_oneline(self.new)}"


@dataclass(frozen=True)
class Battery:
    pytest: tuple[str, ...]
    mutants: tuple[Mutant, ...]


@dataclass(frozen=True)
class PytestRun:
    """One pytest invocation, classified from its JUnit XML rather than from its stdout.

    The XML is a stable contract that distinguishes `<failure>` from `<error>`; the short summary
    on stdout is a rendering, and a test that prints the word FAILED would be part of it.
    """

    exit_code: int
    output: str
    collected: int
    failed: tuple[tuple[str, str], ...]
    errored: tuple[tuple[str, str], ...]
    skipped: tuple[str, ...]
    passed: tuple[str, ...]

    @property
    def ran(self) -> int:
        """Tests that actually executed. A skipped test is collected but never run."""
        return len(self.failed) + len(self.errored) + len(self.passed)


@dataclass(frozen=True)
class Result:
    mutant: Mutant
    outcome: Outcome
    run: PytestRun


def _oneline(text: str) -> str:
    """A source fragment as one readable line, so a multi-line anchor still fits in a report row."""
    collapsed = " ⏎ ".join(line.strip() for line in text.splitlines())
    return f"`{collapsed}`" if len(collapsed) <= 72 else f"`{collapsed[:69]}…`"


# --------------------------------------------------------------------------------------------
# git, and the two things the battery needs from it
# --------------------------------------------------------------------------------------------


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise MutationError(
            f"`git {' '.join(args)}` failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def repo_root(start: Path) -> Path:
    """The working tree `start` sits in — a linked worktree's own root, not the primary checkout.

    The opposite of `tools/land.py`, deliberately: landing must happen in the primary checkout, and
    mutating must happen where the increment is being built.
    """
    try:
        return Path(git("rev-parse", "--show-toplevel", cwd=start))
    except MutationError as exc:
        raise MutationError(f"{start} is not inside a git working tree — {exc}") from exc


def refuse_unless_committed(root: Path, paths: Sequence[Path]) -> None:
    """Every target must be byte-identical to `HEAD` before anything is written.

    Checked for the whole battery up front rather than per mutant: a refusal on mutant 7 of 9 would
    already have run six mutations, and the point is to refuse *before* the first write.
    """
    dirty: list[str] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if not path.is_file():
            raise MutationError(f"{relative}: no such file in {root}")
        status = git("status", "--porcelain", "--", relative, cwd=root)
        if status:
            dirty.append(f"{relative} ({status.split()[0]})")
    if dirty:
        raise MutationError(
            "these targets differ from HEAD, and a mutation run can only be restored as precisely "
            "as the commit it can fall back to:\n  "
            + "\n  ".join(dirty)
            + "\nCommit them first — `git checkout <file>` after a hard kill would otherwise take "
            "the uncommitted work with it, which is the recorded failure this refusal exists for."
        )


# --------------------------------------------------------------------------------------------
# the bytecode cache
# --------------------------------------------------------------------------------------------


def pycache_entries(source: Path) -> list[Path]:
    """Every cached bytecode file that could shadow `source`, whatever interpreter wrote it.

    `importlib.util.cache_from_source` answers for *this* interpreter's tag only, and this script
    may well run under a different one than the pytest it launches (`uv run` resolves its own).
    So the glob is the real answer and the computed path is a belt-and-braces addition to it.
    """
    found: list[Path] = sorted((source.parent / "__pycache__").glob(f"{source.stem}.*.py[co]"))
    try:
        computed = Path(importlib.util.cache_from_source(str(source)))
    except (NotImplementedError, ValueError):  # pragma: no cover — no cache scheme for this path
        return found
    if computed.exists() and computed not in found:
        found.append(computed)
    return found


def clear_pycache(source: Path) -> int:
    """Remove them, and verify none survived. Returns how many were removed."""
    entries = pycache_entries(source)
    for entry in entries:
        entry.unlink(missing_ok=True)
    remaining = pycache_entries(source)
    if remaining:
        raise MutationError(
            f"could not clear the bytecode cache for {source}: "
            f"{', '.join(str(p) for p in remaining)} survived deletion. Every result after this "
            "point could be the previous source running."
        )
    return len(entries)


# --------------------------------------------------------------------------------------------
# applying one mutant, and taking it back
# --------------------------------------------------------------------------------------------


@contextmanager
def applied(mutant: Mutant) -> Generator[None]:
    """Write the mutant, yield, and restore the exact bytes — whatever happens in between.

    The snapshot is bytes, never `git checkout`: an increment's own uncommitted work is not this
    script's to discard, and the six recorded incidents are all the other spelling. The restore is
    verified rather than assumed, because a restore that silently did not happen poisons every
    mutant after it (L6) and looks like nothing at all.
    """
    snapshot = mutant.path.read_bytes()
    try:
        source = snapshot.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MutationError(
            f"{mutant.path}: not UTF-8, so an anchor cannot be located — {exc}"
        ) from exc

    occurrences = source.count(mutant.old)
    if occurrences != 1:
        raise MutationError(
            f"{mutant.name}: the anchor occurs {occurrences} times in "
            f"{mutant.path.name}, and it must occur exactly once — "
            + (
                "nothing would be written and the row would read SURVIVED."
                if occurrences == 0
                else "which of them is the mutant is not stated, so nothing is written."
            )
            + f"\n  anchor: {_oneline(mutant.old)}"
        )

    try:
        mutant.path.write_bytes(source.replace(mutant.old, mutant.new).encode("utf-8"))
        clear_pycache(mutant.path)
        yield
    finally:
        mutant.path.write_bytes(snapshot)
        clear_pycache(mutant.path)
        restored = mutant.path.read_bytes()
        if restored != snapshot:
            raise MutationError(
                f"{mutant.path} was NOT restored: {len(restored)} bytes on disk against "
                f"{len(snapshot)} snapshotted. Recover it with "
                f"`git checkout -- {mutant.path}` — the pre-run refusal guarantees that is correct."
            )


# --------------------------------------------------------------------------------------------
# running pytest, and reading what it actually said
# --------------------------------------------------------------------------------------------


def _node_id(root: Path, classname: str, name: str) -> str:
    """`tests.test_x.TestY` + `test_z` → `tests/test_x.py::TestY::test_z`, checked against disk.

    JUnit XML carries a dotted classname, and the boundary between "module path" and "class" is not
    marked in it. Finding the longest dotted prefix that is a real file is exact, where splitting on
    the last dot would silently misname every test that lives in a class.
    """
    parts = classname.split(".") if classname else []
    for cut in range(len(parts), 0, -1):
        candidate = root.joinpath(*parts[:cut]).with_suffix(".py")
        if candidate.is_file():
            return "::".join([candidate.relative_to(root).as_posix(), *parts[cut:], name])
    return f"{classname}::{name}" if classname else name


def run_pytest(root: Path, command: Sequence[str], selectors: Sequence[str]) -> PytestRun:
    """One pytest run over `selectors`, classified from its JUnit XML.

    Never `-x`: a run that stops at the first failure reports on test ordering, not on the mutant.
    `-p no:cacheprovider` keeps a mutation run from leaving `.pytest_cache` behind in a tree the
    caller is about to inspect.
    """
    with TemporaryDirectory(prefix="pnk-mutate-") as tmp:
        report = Path(tmp) / "report.xml"
        completed = subprocess.run(
            [*command, "-q", "-p", "no:cacheprovider", f"--junit-xml={report}", *selectors],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        output = completed.stdout + completed.stderr
        if not report.is_file():
            return PytestRun(completed.returncode, output, 0, (), (), (), ())
        try:
            suites = ElementTree.parse(report).getroot()
        except ElementTree.ParseError as exc:
            raise MutationError(
                f"pytest's JUnit report did not parse ({exc}). The run is unreadable, so its "
                f"outcome is unknown rather than SURVIVED.\n{_tail(output)}"
            ) from exc

    failed: list[tuple[str, str]] = []
    errored: list[tuple[str, str]] = []
    skipped: list[str] = []
    passed: list[str] = []
    collected = 0
    for case in suites.iter("testcase"):
        collected += 1
        node = _node_id(root, case.get("classname", ""), case.get("name", ""))
        failure = case.find("failure")
        error = case.find("error")
        if failure is not None:
            failed.append((node, (failure.get("message") or "").strip().splitlines()[0]))
        elif error is not None:
            errored.append((node, (error.get("message") or "").strip().splitlines()[0]))
        elif case.find("skipped") is not None:
            skipped.append(node)
        else:
            passed.append(node)

    return PytestRun(
        completed.returncode,
        output,
        collected,
        tuple(failed),
        tuple(errored),
        tuple(skipped),
        tuple(passed),
    )


def _tail(output: str, lines: int = 15) -> str:
    kept = output.strip().splitlines()[-lines:]
    return "\n".join(f"  | {line}" for line in kept)


def check_baseline(root: Path, command: Sequence[str], selectors: Sequence[str]) -> None:
    """The selector, unmutated, must collect a test, run a test, and be green.

    Not in the plan; both halves were measured while building this. A selector whose tests all skip
    exits 0, which is byte-for-byte the SURVIVED signal — and this repo skips on a missing extra as
    a matter of course. A selector that is already red reports KILLED for every mutant aimed at it,
    including the ones nothing catches. Either way the battery reports confidently on a question it
    never asked.
    """
    shown = " ".join(selectors)
    run = run_pytest(root, command, selectors)
    if run.exit_code == PYTEST_USAGE_ERROR:
        raise MutationError(f"pytest rejected the selector `{shown}`:\n{_tail(run.output)}")
    if run.exit_code == PYTEST_NO_TESTS_COLLECTED or run.collected == 0:
        raise MutationError(
            f"`{shown}` collected no tests. A battery cannot be killed by a test that does not "
            f"exist, and an empty selector reports SURVIVED for every mutant aimed at it."
        )
    if run.ran == 0:
        raise MutationError(
            f"every test in `{shown}` skipped in this checkout, and a skipped test exits 0 exactly "
            f"like a passing one — every mutant aimed here would read SURVIVED.\n"
            f"  skipped: {', '.join(run.skipped)}\n"
            f"Install the extra the marker needs, or aim the battery at a test that runs here."
        )
    if run.exit_code != 0:
        broken = [node for node, _ in (*run.failed, *run.errored)]
        raise MutationError(
            f"`{shown}` is not green before any mutation, so every mutant aimed at it would read "
            f"KILLED whatever the code does:\n  " + "\n  ".join(broken) + f"\n{_tail(run.output)}"
        )


def classify(run: PytestRun) -> Outcome:
    """KILLED, SURVIVED, or neither — and `neither` is never quietly folded into one of them."""
    if run.errored:
        return Outcome.ERRORED
    if run.failed:
        return Outcome.KILLED
    if run.exit_code == 0 and run.ran > 0:
        return Outcome.SURVIVED
    return Outcome.ERRORED


# --------------------------------------------------------------------------------------------
# the battery file
# --------------------------------------------------------------------------------------------


def _string(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise MutationError(f"{where} must be a string, not {type(value).__name__}")
    return value


def _array(value: object, where: str) -> list[object]:
    if not isinstance(value, list):
        raise MutationError(f"{where} must be an array, not {type(value).__name__}")
    return cast(list[object], value)


def _table(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise MutationError(f"{where} must be a table, not {type(value).__name__}")
    return cast(dict[str, object], value)


def load_battery(path: Path, root: Path) -> Battery:
    """Parse and validate the battery, resolving every target against the repository root.

    Every refusal here happens before the first byte is written, which is the point: a battery that
    is wrong in its ninth mutant has already mutated eight files by the time anything notices.
    """
    try:
        data: dict[str, object] = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise MutationError(f"{path}: {exc}") from exc

    command: tuple[str, ...] = DEFAULT_PYTEST
    if "pytest" in data:
        given = _array(data["pytest"], f"{path}: `pytest`")
        if not given:
            raise MutationError(f"{path}: `pytest` is empty — it must name a command to run")
        command = tuple(_string(part, f"{path}: pytest[{i}]") for i, part in enumerate(given))

    entries = _array(data.get("mutant", []), f"{path}: `mutant`")
    if not entries:
        raise MutationError(
            f"{path}: no mutants. A battery needs at least one `[[mutant]]` table with "
            f"`file`, `old`, `new` and `kills`."
        )

    mutants: list[Mutant] = []
    for index, entry in enumerate(entries, start=1):
        where = f"{path}: mutant {index}"
        table = _table(entry, where)
        missing = [key for key in ("file", "old", "new", "kills") if key not in table]
        if missing:
            raise MutationError(f"{where} is missing {', '.join(missing)}")

        old = _string(table["old"], f"{where}: old")
        new = _string(table["new"], f"{where}: new")
        if old == new:
            raise MutationError(
                f"{where}: `old` and `new` are identical, so the file would not change and the "
                f"row would read SURVIVED whatever the tests do."
            )

        kills = table["kills"]
        selectors = (
            (_string(kills, f"{where}: kills"),)
            if isinstance(kills, str)
            else tuple(
                _string(part, f"{where}: kills[{i}]")
                for i, part in enumerate(_array(kills, f"{where}: `kills`"))
            )
        )
        if not selectors:
            raise MutationError(f"{where}: `kills` names no test")

        target = (root / _string(table["file"], f"{where}: file")).resolve()
        if root not in target.parents:
            raise MutationError(
                f"{where}: {target} is outside the repository at {root}. A battery may only "
                f"mutate the tree it is being run against."
            )

        mutants.append(
            Mutant(
                name=_string(table.get("name", old), f"{where}: name"),
                path=target,
                old=old,
                new=new,
                selectors=selectors,
            )
        )
    return Battery(pytest=command, mutants=tuple(mutants))


# --------------------------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------------------------


def run_battery(root: Path, battery: Battery) -> list[Result]:
    refuse_unless_committed(root, [mutant.path for mutant in battery.mutants])

    seen: set[tuple[str, ...]] = set()
    for mutant in battery.mutants:
        if mutant.selectors not in seen:
            seen.add(mutant.selectors)
            clear_pycache(mutant.path)
            check_baseline(root, battery.pytest, mutant.selectors)
    print(f"baseline: {len(seen)} selector(s) green, with at least one test running in each.\n")

    results: list[Result] = []
    for index, mutant in enumerate(battery.mutants, start=1):
        print(f"[{index}/{len(battery.mutants)}] {mutant.name}")
        print(f"        {mutant.path.name}: {mutant.edit}")
        with applied(mutant):
            run = run_pytest(root, battery.pytest, mutant.selectors)
        result = Result(mutant, classify(run), run)
        results.append(result)
        print(f"        {_render(result)}\n")
    return results


def _render(result: Result) -> str:
    run = result.run
    if result.outcome is Outcome.KILLED:
        killers = "\n        ".join(f"{node} — {why}" for node, why in run.failed)
        survivors = len(run.passed)
        tail = f"  ({survivors} test(s) in the selector still passed)" if survivors else ""
        return f"KILLED by\n        {killers}{tail}"
    if result.outcome is Outcome.SURVIVED:
        return (
            f"SURVIVED — {len(run.passed)} test(s) passed with the mutant in place. "
            f"Nothing here pins this assertion."
        )
    if run.errored:
        detail = "\n        ".join(f"{node} — {why}" for node, why in run.errored)
        return f"ERRORED (not a kill) — the mutant did not run:\n        {detail}"
    return (
        f"ERRORED (not a kill) — pytest exited {run.exit_code} with "
        f"{run.collected} test(s) collected and {run.ran} run:\n{_tail(run.output)}"
    )


def report(results: Sequence[Result], *, allow_zero_kills: bool) -> int:
    """Print the summary and decide the exit status. Survivors are a finding, not a failure."""
    tally = {outcome: [r for r in results if r.outcome is outcome] for outcome in Outcome}
    print("=" * 96)
    for outcome in Outcome:
        for result in tally[outcome]:
            print(f"{outcome.value:<9} {result.mutant.name}")
    print(
        f"\n{len(results)} mutant(s): {len(tally[Outcome.KILLED])} killed, "
        f"{len(tally[Outcome.SURVIVED])} survived, {len(tally[Outcome.ERRORED])} errored."
    )

    if tally[Outcome.ERRORED]:
        print(
            "\nmutate: an ERRORED mutant is neither killed nor survived — it never ran. Fix the "
            "battery; this report says nothing about those assertions.",
            file=sys.stderr,
        )
        return 1
    if not tally[Outcome.KILLED] and not allow_zero_kills:
        print(
            "\nmutate: nothing died. A batch with no kills is a broken harness, not a clean bill — "
            "the tests may not be running the code you mutated at all. Add a mutant you know is "
            "caught and run again; pass --allow-zero-kills only for a backstop already documented "
            "as unpinned.",
            file=sys.stderr,
        )
        return 1
    if tally[Outcome.SURVIVED]:
        print(
            "\nA SURVIVED row is a real finding: that assertion is not pinned by the test named "
            "beside it. It is not a harness failure, so this exits 0 — read the rows."
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a mutation battery: apply each mutant, run the tests that should catch "
        "it, restore, and report which assertions are actually pinned.",
    )
    _ = parser.add_argument("battery", type=Path, help="the TOML battery file")
    _ = parser.add_argument(
        "--allow-zero-kills",
        action="store_true",
        help="accept a batch where nothing died — only for a deliberate probe of a backstop "
        "already documented as unpinned",
    )
    _ = parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="the working tree to mutate in (default: the one the current directory is in)",
    )
    args = parser.parse_args(argv)
    battery_path: Path = args.battery
    allow_zero_kills: bool = args.allow_zero_kills
    start: Path = args.repo if args.repo is not None else Path.cwd()

    def _restore_and_die(signum: int, _frame: FrameType | None) -> None:
        """SIGTERM's default disposition skips `finally` and leaves the mutant on disk — measured.
        Raising turns it back into an unwind, so the restore happens. SIGINT already raises."""
        raise KeyboardInterrupt(f"signal {signal.Signals(signum).name}")

    _ = signal.signal(signal.SIGTERM, _restore_and_die)

    try:
        root = repo_root(start.resolve())
        battery = load_battery(battery_path, root)
        print(
            f"mutate: {len(battery.mutants)} mutant(s) in {root}, pytest = "
            f"{shlex.join(battery.pytest)}\n"
        )
        results = run_battery(root, battery)
    except MutationError as exc:
        print(f"mutate: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt as exc:
        print(
            f"\nmutate: interrupted ({exc}) — the target was restored on the way out.",
            file=sys.stderr,
        )
        return 1
    return report(results, allow_zero_kills=allow_zero_kills)


if __name__ == "__main__":
    raise SystemExit(main())
