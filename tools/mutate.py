"""Run a per-increment mutation battery — the one step of `docs/BUILDING.md` with no guard.

**Why this exists.** Step 4 of [`docs/BUILDING.md`](../docs/BUILDING.md) says: break the code on
purpose, confirm the right test fails, restore. It is the procedure's one *silently-failing* step.
A broken harness prints SURVIVED and KILLED in exactly the same shape a working one does, so the
report reads as evidence either way. `plans/20260821_0745-mutation-harness.md` counts more than a
dozen invalid or destructive runs across ten increments; the `git checkout` trap alone is recorded
**six times** (`docs/RETROSPECTIVES.md` § *Start here*), still recurring after four write-ups. E5's
own words: *"knowing the trap was not enough to avoid it."*

The precedent is `tools/land.py`. When prose has failed repeatedly against a class of mistake that
fails *silently*, the rule stops being a rule and becomes a tool. Each of the written rules is a
refusal here:

* **the target must be tracked, and must match `HEAD`** — the six recorded incidents all end
  `git checkout <file>`, which restores to the last commit and takes any uncommitted fix in that
  file with it. This script never runs `git checkout`; it restores from a byte snapshot taken
  before the write. But a snapshot lives in memory and **`SIGKILL` cannot be handled**, so after a
  hard kill the only recovery *is* `git checkout <file>` — and that refusal is what makes the
  recovery correct rather than the seventh instance of the trap. Tracked, too: `git status` prints
  nothing for a **gitignored** file, so cleanliness alone would pass a file with no `HEAD` version
  at all, for which the printed recovery does not work;
* **the anchor must match exactly once**, checked across the whole battery before the first write —
  a `str.replace` that matches nothing returns the string unchanged and reports to no one. The
  mutant is never written, the tests pass, the row says SURVIVED;
* **`__pycache__` is cleared after the write and after the restore** — CPython validates a `.pyc`
  on `(mtime-to-the-second, size)`. A *same-length* mutant applied within the same wall-clock
  second as the previous compile changes neither, so the stale bytecode runs and the row says
  SURVIVED. Measured 6 times out of 6 before this script existed (T3);
* **pytest never sees `-x`** — refused in the battery's `pytest` command, refused in a selector,
  and `PYTEST_ADDOPTS` is dropped from the child environment, because it is inherited and
  `PYTEST_ADDOPTS="-x"` in the operator's shell turns a mutant that two tests catch into a row
  saying one did;
* **a mutant that does not compile is refused, not run.** A Python mutant whose result is a
  `SyntaxError` tests nothing, and `KILLED` will not say so: found 20260823, on this tool's own
  battery, where a repaired `old` had left its `new` behind and the resulting `keyword argument
  repeated` arrived as an ordinary assertion failure because the module is imported *inside* the
  test rather than at collection. `ast.parse` is not enough — it accepts `f(a=1, a=2)` and
  `compile()` does not, which is exactly the case that got through;
* **an invalid mutant is its own outcome** — pytest exits 2 with a collection `<error>`, not a
  `<failure>`. T4 misread that in both directions: once as a kill, once as a survival. The same
  `<error>` tag also covers a **setup or teardown** failure on a real node, which is the opposite
  event — the mutant ran and a fixture noticed it — so the two are told apart structurally (a
  collection failure carries no `line`) rather than folded together, which tallied a genuine
  assertion-kill beside one as `0 killed`. The *syntax* half of "invalid" is refused above, before
  anything is written, per this tool's own rule that a refusal available before the first write is
  made there; what remains here is every invalidity only a run can find;
* **the restore happens in a `finally`, and its bytes are verified** — a run killed mid-battery must
  not poison the mutants after it (L6). `SIGTERM`, `SIGHUP` and `SIGQUIT` are turned back into an
  unwind, because their default disposition ends the process *without* running `finally` and leaves
  the mutant on disk — measured;
* **a batch with no kills exits non-zero.** A run where nothing died is a broken harness, not a
  clean bill. `--allow-zero-kills` is for the rare deliberate probe of a backstop already documented
  as unpinned.

**Three ways a run can lie that the plan did not name**, all measured while building this, all of
them the harness reporting confidently on a question it never asked:

* **a test that skips exits 0 — byte for byte the SURVIVED signal.** This repo skips constantly
  (`pdf`, `paid`, `model`, a missing extra), so a battery aimed at one of those in a `[light]`
  checkout would report every mutant in it unpinned;
* **a selector that is already red reports KILLED for every mutant aimed at it**, including the
  ones nothing catches;
* **`PYTHONPYCACHEPREFIX` moves every `.pyc` into a mirrored tree**, where the clearing above cannot
  reach it — so it is refused rather than guessed at.

The first two are caught by one pre-flight run per selector, before any file is touched: it must
collect a test, actually *run* a test, and be green. That run also times the selector, and a
mutated run is given ten times as long before it is called non-terminating.

**What it deliberately does not do.** Cross-file mutants and generated mutation operators are not
supported, and a target under `tests/` is **refused**: a mutant in the file its own selector runs
can make that test vacuous, and no outcome printed here would say so. A row is a claim about *one
assertion*, never about a commit.

    python3 tools/mutate.py battery.toml
    python3 tools/mutate.py battery.toml --allow-zero-kills
    python3 tools/mutate.py battery.toml --repo ../pinakes-worktree
    python3 tools/mutate.py --check-anchors tools/batteries/*.toml

The battery is TOML — `tomllib` is stdlib, and `'''…'''` carries quotes, backslashes and
indentation without escaping, which is most of what source code is made of. This example is the
battery this tool was first run with, and it still resolves:

    # Optional. Default: ["uv", "run", "--frozen", "pytest"]
    pytest = ["uv", "run", "--frozen", "pytest"]

    [[mutant]]
    name = "the depth cap is a max(), so a deep walk is never clamped"
    file = "src/pinakes/graph/traverse.py"
    old  = '''min(depth, MAX_DEPTH)'''
    new  = '''max(depth, MAX_DEPTH)'''
    kills = "tests/test_traverse.py::test_depth_is_clamped_to_the_server_maximum"

`'''` trims exactly one newline after the opening delimiter and keeps a trailing one, so a
multi-line anchor either opens on the same line as its first character or accepts that. An anchor
that does not match is refused with its count, which is the safety net for getting it wrong.

`pytest` lives in the battery rather than on the command line: one home for the setting, and the
tests can point it at `sys.executable -m pytest` without a flag that would otherwise exist only for
them.

**Batteries are kept.** Until 20260823 the paragraph above went on to say a battery *is* a
per-increment working file, not a portable artifact. That was an assumption shipped as a fact, and
nothing had measured it. Measured: of 81 mutants written across six increments and left in session
scratchpads, **78 anchors still resolved exactly once** a day to a week later — and the three that
did not **refused**, naming the anchor and its count, because a stale anchor is the one thing this
tool has never been willing to guess at. The failure mode of keeping a battery is a maintenance
prompt, never a false KILLED or a false SURVIVED. So they live in
[`tools/batteries/`](batteries/README.md), one per target, and `--check-anchors` answers *do they
still hold?* in milliseconds instead of a pytest baseline per selector. A committed battery omits
`pytest` and takes the default, so there is one less thing in it that can rot.

What that keeps is not the proof — re-deriving 41 mutants against a gate takes an afternoon, not a
release. It is **the reasoning about which mutants were worth writing**: which breakages are
plausible, which are the shipped defect this increment closed, and which two exist only because a
first-draft guard-test turned out to be a tautology. None of that is in the code, and none of it is
re-derivable from it.

**And the axis that historically rots is the selector, not the anchor.**
`docs/RETROSPECTIVES.md` records it twice in one increment: *"a battery is source that goes stale
like any other, and a SURVIVED row is a claim about a pair — the mutant and the selector — either
half of which can be wrong."* The 78-of-81 measurement above is about anchors, which is the half
that held; `tests/test_batteries.py` resolves the selectors, which is the half that broke.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shlex
import signal
import subprocess
import sys
import time
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

#: The two pytest exit codes the baseline reads directly. Everything else is classified from the
#: JUnit report, because an exit code cannot tell a `<failure>` from an `<error>`: 0 is "all passed"
#: *or* "every test skipped", 1 is a failure, 2 is a collection error — an invalid mutant.
PYTEST_USAGE_ERROR = 4
PYTEST_NO_TESTS_COLLECTED = 5

#: Refused in a battery's `pytest` command and in its selectors. With `-x`, a run reports on test
#: ordering rather than on the mutant.
STOP_AT_FIRST_FAILURE = ("-x", "--exitfirst")

#: A target under here is refused; mutating a test stays manual.
TESTS_DIRNAME = "tests"

#: A mutated run gets this multiple of its selector's measured baseline before it is called
#: non-terminating, with a floor for selectors fast enough that the multiple is meaningless. A
#: mutant that removes a loop's exit condition would otherwise hang the battery with itself on disk.
TIMEOUT_FACTOR = 10
TIMEOUT_FLOOR_SECONDS = 60.0

#: Signals whose default disposition ends the process *without* unwinding, so `applied()`'s
#: `finally` never runs and the mutant stays on disk. Measured for SIGTERM, 1 of 1. SIGINT is
#: absent because Python already raises `KeyboardInterrupt` for it; SIGKILL cannot be handled at
#: all, which is what the `HEAD` refusal is the answer to.
UNWINDLESS_SIGNALS = ("SIGTERM", "SIGHUP", "SIGQUIT")


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
        """`old → new`, rendered so the two sides cannot look identical when they are not.

        `_oneline` strips each line so a multi-line anchor fits a row, which erases an
        indentation-only mutant entirely — both sides print the same string and the row says
        nothing. When that happens the raw `repr` is used instead: unreadable, but true.
        """
        before, after = _oneline(self.old), _oneline(self.new)
        if before == after:
            return f"{self.old!r} → {self.new!r}"
        return f"{before} → {after}"


@dataclass(frozen=True)
class Battery:
    pytest: tuple[str, ...]
    mutants: tuple[Mutant, ...]


@dataclass(frozen=True)
class PytestRun:
    """One pytest invocation, classified from its JUnit XML rather than from its stdout.

    The XML is a stable contract that distinguishes `<failure>` from `<error>`; the short summary
    on stdout is a rendering, and a test that printed the word FAILED would be part of it.
    """

    exit_code: int
    output: str
    collected: int
    failed: tuple[tuple[str, str], ...]
    collection_errors: tuple[tuple[str, str], ...]
    setup_errors: tuple[tuple[str, str], ...]
    skipped: tuple[str, ...]
    passed: tuple[str, ...]
    seconds: float = 0.0
    timed_out: bool = False

    @property
    def ran(self) -> int:
        """Tests that actually executed. A skipped test is collected but never run, and neither is
        a test whose *module* failed to import — but one whose fixture raised did run."""
        return len(self.failed) + len(self.setup_errors) + len(self.passed)


@dataclass(frozen=True)
class Result:
    mutant: Mutant
    outcome: Outcome
    run: PytestRun


def _oneline(text: str) -> str:
    """A source fragment as one readable line, so a multi-line anchor still fits in a report row."""
    collapsed = " ⏎ ".join(line.strip() for line in text.splitlines())
    return f"`{collapsed}`" if len(collapsed) <= 72 else f"`{collapsed[:69]}…`"


def _tail(output: str, lines: int = 15) -> str:
    kept = output.strip().splitlines()[-lines:]
    return "\n".join(f"  | {line}" for line in kept)


# --------------------------------------------------------------------------------------------
# git, and the two things a battery needs from it
# --------------------------------------------------------------------------------------------


def git(*args: str, cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise MutationError(f"could not run git in {cwd}: {exc}") from exc
    if result.returncode != 0:
        raise MutationError(
            f"`git {' '.join(args)}` failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def repo_root(start: Path) -> Path:
    """The working tree `start` sits in — a linked worktree's own root, not the primary checkout.

    The inverse of `tools/land.py`, deliberately: landing must happen in the primary checkout, and
    mutating must happen where the increment is being built.

    `.resolve()`, because on macOS `/tmp` is a symlink to `/private/tmp`: a root spelled differently
    from the resolved targets makes `relative_to` raise `ValueError` — a traceback where this file
    promises a refusal.
    """
    if not start.is_dir():
        raise MutationError(f"{start} is not a directory, so there is no working tree to mutate.")
    try:
        return Path(git("rev-parse", "--show-toplevel", cwd=start)).resolve()
    except MutationError as exc:
        raise MutationError(f"{start} is not inside a git working tree — {exc}") from exc


def refuse_unless_committed(root: Path, paths: Sequence[Path]) -> None:
    """Every target must be tracked by git and byte-identical to `HEAD` before anything is written.

    Checked for the whole battery up front rather than per mutant: a refusal on mutant 7 of 9 would
    already have run six mutations, and the point is to refuse *before* the first write.

    **Tracked** is a separate question from **clean**, and `git status --porcelain` answers only the
    second: it prints nothing at all for a gitignored file. Such a file has no `HEAD` version, so
    the `git checkout --` recovery this whole refusal exists to guarantee does not work for it.
    """
    untracked: list[str] = []
    dirty: list[str] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if not path.is_file():
            raise MutationError(f"{relative}: no such file in {root}")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.returncode != 0:
            untracked.append(relative)
            continue
        status = git("status", "--porcelain", "--", relative, cwd=root)
        if status:
            dirty.append(f"{relative} ({status.split()[0]})")

    if untracked:
        raise MutationError(
            "these targets are not tracked by git:\n  "
            + "\n  ".join(untracked)
            + "\nAn untracked or gitignored file has no HEAD version, so `git checkout --` cannot "
            "recover it after a hard kill — and that recovery is the only one left once the "
            "snapshot in memory is gone. Commit them, or do not mutate them."
        )
    if dirty:
        raise MutationError(
            "these targets differ from HEAD, and a mutation run can only be restored as precisely "
            "as the commit it can fall back to:\n  "
            + "\n  ".join(dirty)
            + "\nCommit them first — `git checkout <file>` after a hard kill would otherwise take "
            "the uncommitted work with it, which is the recorded failure this refusal exists for."
        )


def refuse_a_test_file(root: Path, mutants: Sequence[Mutant]) -> None:
    """Mutating a test file stays manual, and the tool says so rather than approximating it.

    A mutant inside the file its own selector runs can make that test vacuous — delete the
    assertion and the test still passes — and SURVIVED is then a statement about nothing. `tools/`
    scripts are *not* covered: the record holds three batteries against
    `tools/reachable_ceiling_probe.py`, which is ordinary code with ordinary tests.
    """
    refused = [m for m in mutants if m.path.relative_to(root).parts[:1] == (TESTS_DIRNAME,)]
    if refused:
        raise MutationError(
            "these targets are test files, and mutating a test stays manual:\n  "
            + "\n  ".join(m.path.relative_to(root).as_posix() for m in refused)
            + "\nA mutant in the file its own selector runs can make that test vacuous, and no "
            "outcome printed here would tell you it had. Do it by hand, and read the assertion."
        )


def refuse_a_mutant_that_cannot_compile(mutants: Sequence[Mutant]) -> None:
    """A Python mutant whose result does not compile is invalid, and `KILLED` will not say so.

    Found by this tool being used on itself, 20260823. Repairing a stale anchor had widened `old`
    to two lines and left `new` at the one line it used to replace, so applying it deleted a
    *neighbouring* keyword argument and duplicated another — `keyword argument repeated`, a
    `SyntaxError` at import.

    That should have been the ERRORED outcome, and it was not: `classify` reads a **collection**
    error as the invalid mutant, and this module is imported *inside* the test rather than at
    module scope, so the `SyntaxError` arrived as an ordinary assertion failure. The row read
    `KILLED`, the summary read `41 killed, 0 errored`, and the property the mutant names was never
    exercised. A confident row about a question nobody asked is the one thing this tool exists to
    refuse, so it is refused here — before the first write, with the anchor pre-flight, rather than
    inferred from what pytest happened to print.

    `ast.parse` is not enough: it accepts `f(a=1, a=2)` and `compile()` rejects it, which is
    precisely the case that got through. Only `.py` targets are checked — a battery may mutate a
    workflow, a Makefile or a `pyproject.toml`, and nothing here can judge those.
    """
    refused: list[str] = []
    for mutant in mutants:
        # A missing target and a stale anchor are each owned by a check that reports them better,
        # and both are reached before this one in a run. In `--check-anchors` this may run first,
        # so it declines rather than reading a file that is not there.
        if mutant.path.suffix != ".py" or not mutant.path.is_file():
            continue
        text = _decoded(mutant.path)
        if text.count(mutant.old) != 1:
            continue
        try:
            _ = compile(text.replace(mutant.old, mutant.new), str(mutant.path), "exec")
        except SyntaxError as exc:
            refused.append(
                f"{mutant.name}: applying this to {mutant.path.name} does not compile — "
                f"{exc.msg} (line {exc.lineno}).\n  edit: {mutant.edit}"
            )
    if refused:
        raise MutationError(
            "these mutants do not compile, so nothing they produce is a test of the property "
            "they name:\n  "
            + "\n  ".join(refused)
            + "\nThe usual cause is a repaired `old` whose `new` was left behind. Repair both, "
            "and re-read the edit rather than the anchor."
        )


def refuse_an_anchor_that_is_not_unique(mutants: Sequence[Mutant]) -> None:
    """Every anchor must occur exactly once, checked against the pristine files up front.

    `applied()` checks this too, and must: it may never write a mutant it cannot place. But
    checking *only* there means a battery whose ninth anchor is stale has already run eight
    mutations before it refuses, and the plan asks for a refusal **before writing**. Every mutant is
    restored before the next begins, so the pristine file is what each anchor will meet.
    """
    for mutant in mutants:
        text = _decoded(mutant.path)
        count = text.count(mutant.old)
        if count != 1:
            raise MutationError(_bad_anchor_message(mutant, count, text))


def _decoded(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MutationError(f"{path}: not UTF-8, so an anchor cannot be located — {exc}") from exc


def _bad_anchor_message(mutant: Mutant, occurrences: int, text: str) -> str:
    why = (
        "nothing would be written and the row would read SURVIVED."
        if occurrences == 0
        else "which of them is the mutant is not stated, so nothing is written."
    )
    # A CRLF file and an LF anchor never match, and the bare count gives no hint why: TOML's
    # `'''…'''` produces LF whatever the file it was copied from uses.
    crlf = (
        "\n  note: this file has CRLF line endings and the anchor does not — a multi-line anchor "
        "copied through TOML will never match it."
        if "\r\n" in text and "\r\n" not in mutant.old and "\n" in mutant.old
        else ""
    )
    return (
        f"{mutant.name}: the anchor occurs {occurrences} times in {mutant.path.name}, and it must "
        f"occur exactly once — {why}\n  anchor: {_oneline(mutant.old)}{crlf}"
    )


# --------------------------------------------------------------------------------------------
# the bytecode cache
# --------------------------------------------------------------------------------------------


def refuse_a_relocated_bytecode_cache() -> None:
    """`PYTHONPYCACHEPREFIX` puts every `.pyc` in a mirrored tree, out of the clearing's reach.

    Measured: with it set, `<package>/__pycache__` is never created at all and the cache lands
    under the prefix — so `clear_pycache` finds nothing, removes nothing, reports success, and a
    same-length mutant reads SURVIVED off bytecode this tool never saw. The prefix could be followed
    rather than refused, but the mirror is built from the *child* interpreter's view of an absolute
    path, and guessing it wrong fails in exactly the silent direction the tool exists to close.
    """
    prefix = os.environ.get("PYTHONPYCACHEPREFIX")
    if prefix:
        raise MutationError(
            f"PYTHONPYCACHEPREFIX is set to {prefix!r}, which moves every .pyc into a mirrored "
            f"tree this harness would have to guess at. It cannot clear what it cannot find, and "
            f"an uncleared .pyc is how a same-length mutant reads SURVIVED. Unset it and re-run."
        )


def pycache_entries(source: Path) -> list[Path]:
    """Every cached bytecode file that could shadow `source`, whatever interpreter wrote it.

    A glob rather than a computed name, for two reasons: `importlib.util.cache_from_source` answers
    for *this* interpreter's tag only, and this script may well run under a different one than the
    pytest it launches (`uv run` resolves its own); and pytest's assertion rewriting writes a second
    file under its own tag, `…cpython-313-pytest-9.1.1.pyc`, beside the ordinary one.
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
    source = snapshot.decode("utf-8")

    # Checked in the pre-flight too, and kept here on purpose: this is the last point before a
    # write, and placing a mutant whose anchor is not unique must be impossible.
    occurrences = source.count(mutant.old)
    if occurrences != 1:
        raise MutationError(_bad_anchor_message(mutant, occurrences, source))

    mutated = source.replace(mutant.old, mutant.new).encode("utf-8")
    try:
        mutant.path.write_bytes(mutated)
        _ = clear_pycache(mutant.path)
        yield
    finally:
        # The order is deliberate and the inner `try` is not decoration. Restoring comes first
        # because it is the only step whose failure is unrecoverable; the cache is cleared even when
        # the restore went wrong, since the *mutant's* bytecode beside the *original* source is the
        # poisoning L6 records; and a cache error must not mask a failed restore, so it is held and
        # re-raised second.
        found = mutant.path.read_bytes()
        mutant.path.write_bytes(snapshot)
        restored = mutant.path.read_bytes()
        cache_failure: MutationError | None = None
        try:
            _ = clear_pycache(mutant.path)
        except MutationError as exc:
            cache_failure = exc
        if restored != snapshot:
            raise MutationError(
                f"{mutant.path} was NOT restored: {len(restored)} bytes on disk against "
                f"{len(snapshot)} snapshotted. Recover it with "
                f"`git checkout -- {mutant.path}` — the pre-run refusal guarantees that is correct."
            )
        if found != mutated:
            # Not a refusal: the file is back and the batch can go on. But something other than
            # this process wrote to the target while the mutant was in place, and CLAUDE.md's
            # standing assumption is that other agents are running right now — so the edit that was
            # just overwritten was somebody's.
            print(
                f"mutate: WARNING — {mutant.path.name} changed on disk while the mutant was in "
                f"place, and the snapshot has just overwritten that change. The row below is about "
                f"a file two processes were writing to; re-run it alone.",
                file=sys.stderr,
            )
        if cache_failure is not None:
            raise cache_failure


# --------------------------------------------------------------------------------------------
# running pytest, and reading what it actually said
# --------------------------------------------------------------------------------------------


def child_environment() -> dict[str, str]:
    """The environment pytest runs in: this one, minus what would silently rewrite the run.

    `PYTEST_ADDOPTS` is inherited by any pytest, and it was measured here: `PYTEST_ADDOPTS="-x"` in
    the operator's shell turns a mutant that two tests catch into a row saying one test caught it —
    the `a107a05` under-selection defect, arriving through the environment rather than through the
    battery, and taking the "pytest never sees `-x`" promise with it. It is dropped rather than
    merged, because a mutation run has to mean the same thing on a machine whose shell nobody
    audited.
    """
    environment = dict(os.environ)
    _ = environment.pop("PYTEST_ADDOPTS", None)
    return environment


def _node_id(root: Path, classname: str, name: str, file: str | None) -> str:
    """`tests/test_x.py` + `tests.test_x.TestY` + `test_z` → `tests/test_x.py::TestY::test_z`.

    `junit_family=xunit1` reports the real path, so nothing has to be inferred. The dotted
    reconstruction is the fallback for a report that carries no `file`: the boundary between
    "module path" and "class" is not marked in a classname, so the longest dotted prefix that is a
    real file is found on disk — where splitting on the last dot would misname every test in a
    class.
    """
    if file:
        depth = len(Path(file).with_suffix("").parts)
        classes = classname.split(".")[depth:] if classname else []
        return "::".join([file, *classes, name])
    parts = classname.split(".") if classname else []
    for cut in range(len(parts), 0, -1):
        candidate = root.joinpath(*parts[:cut]).with_suffix(".py")
        if candidate.is_file():
            return "::".join([candidate.relative_to(root).as_posix(), *parts[cut:], name])
    return f"{classname}::{name}" if classname else name


def run_pytest(
    root: Path,
    command: Sequence[str],
    selectors: Sequence[str],
    timeout: float | None = None,
) -> PytestRun:
    """One pytest run over `selectors`, classified from its JUnit XML.

    Never `-x`: a run that stops at the first failure reports on test ordering, not on the mutant.
    `-p no:cacheprovider` keeps a mutation run from leaving `.pytest_cache` behind in a tree the
    caller is about to inspect. `junit_family=xunit1` is forced because it carries `file` and `line`
    where the default `xunit2` drops them, so the report's shape does not depend on the repo's own
    pytest configuration.
    """
    with TemporaryDirectory(prefix="pnk-mutate-") as tmp:
        report = Path(tmp) / "report.xml"
        argv = [
            *command,
            "-q",
            "-p",
            "no:cacheprovider",
            "-o",
            "junit_family=xunit1",
            f"--junit-xml={report}",
            *selectors,
        ]
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv,
                cwd=root,
                env=child_environment(),
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as expired:
            return PytestRun(
                -1,
                _decode_stream(expired.stdout) + _decode_stream(expired.stderr),
                0,
                (),
                (),
                (),
                (),
                (),
                seconds=time.monotonic() - started,
                timed_out=True,
            )
        except (OSError, ValueError) as exc:
            raise MutationError(
                f"could not run `{shlex.join(command)}` in {root}: {exc}. That command is the "
                f"battery's `pytest` key, or its default `{shlex.join(DEFAULT_PYTEST)}`."
            ) from exc
        seconds = time.monotonic() - started
        output = completed.stdout + completed.stderr
        if not report.is_file():
            return PytestRun(completed.returncode, output, 0, (), (), (), (), (), seconds=seconds)
        try:
            suites = ElementTree.parse(report).getroot()
        except ElementTree.ParseError as exc:
            raise MutationError(
                f"pytest's JUnit report did not parse ({exc}). The run is unreadable, so its "
                f"outcome is unknown rather than SURVIVED.\n{_tail(output)}"
            ) from exc

    failed: list[tuple[str, str]] = []
    collection_errors: list[tuple[str, str]] = []
    setup_errors: list[tuple[str, str]] = []
    skipped: list[str] = []
    passed: list[str] = []
    collected = 0
    for case in suites.iter("testcase"):
        collected += 1
        node = _node_id(root, case.get("classname", ""), case.get("name", ""), case.get("file"))
        failure = case.find("failure")
        error = case.find("error")
        if failure is not None:
            failed.append((node, _first_line(failure.get("message"))))
        elif error is not None:
            # Two different events wear the same tag. A **collection** failure is not a test at
            # all: pytest synthesises a testcase for the module, with an empty classname and no
            # `line`, and exits 2 — that is the invalid mutant. A **setup or teardown** error is a
            # real node that pytest reached and could not run to completion, and the mutant is
            # usually why. Measured on pytest 9.1.1: the `line` attribute is present for the second
            # and absent for the first, which is a structural test rather than a message match.
            if case.get("line") is None and not case.get("classname"):
                collection_errors.append((node, _first_line(error.get("message"))))
            else:
                setup_errors.append((node, _first_line(error.get("message"))))
        elif case.find("skipped") is not None:
            skipped.append(node)
        else:
            passed.append(node)

    return PytestRun(
        completed.returncode,
        output,
        collected,
        tuple(failed),
        tuple(collection_errors),
        tuple(setup_errors),
        tuple(skipped),
        tuple(passed),
        seconds=seconds,
    )


def _decode_stream(stream: bytes | str | None) -> str:
    if stream is None:
        return ""
    return stream if isinstance(stream, str) else stream.decode("utf-8", "replace")


def _first_line(message: str | None) -> str:
    stripped = (message or "").strip()
    return stripped.splitlines()[0] if stripped else "(no message)"


def check_baseline(root: Path, command: Sequence[str], selectors: Sequence[str]) -> PytestRun:
    """The selector, unmutated, must collect a test, run a test, and be green.

    Not in the plan; both halves were measured while building this. A selector whose tests all skip
    exits 0, which is byte for byte the SURVIVED signal — and this repo skips on a missing extra as
    a matter of course. A selector that is already red reports KILLED for every mutant aimed at it,
    including the ones nothing catches. Either way the battery reports confidently on a question it
    never asked.

    The run is also the timing reference for every mutated run of the same selector.
    """
    shown = " ".join(selectors)
    run = run_pytest(root, command, selectors)
    if run.exit_code == PYTEST_USAGE_ERROR:
        raise MutationError(f"pytest rejected the selector `{shown}`:\n{_tail(run.output)}")
    if run.exit_code == PYTEST_NO_TESTS_COLLECTED or run.collected == 0:
        raise MutationError(
            f"`{shown}` collected no tests. A battery cannot be killed by a test that does not "
            f"exist, and an empty selector reports SURVIVED for every mutant aimed at it."
            + (f"\n{_tail(run.output)}" if run.output.strip() else "")
        )
    if run.exit_code != 0:
        broken = [node for node, _ in (*run.failed, *run.collection_errors, *run.setup_errors)]
        raise MutationError(
            f"`{shown}` is not green before any mutation, so every mutant aimed at it would read "
            f"KILLED whatever the code does:\n  " + "\n  ".join(broken) + f"\n{_tail(run.output)}"
        )
    # After the exit-code check, not before it: a run that collected only skips exits 0, while one
    # that errored exits non-zero and belongs to the branch above.
    if run.ran == 0:
        raise MutationError(
            f"every test in `{shown}` skipped in this checkout, and a skipped test exits 0 exactly "
            f"like a passing one — every mutant aimed here would read SURVIVED.\n"
            f"  skipped: {', '.join(run.skipped)}\n"
            f"Install the extra the marker needs, or aim the battery at a test that runs here."
        )
    return run


def classify(run: PytestRun) -> Outcome:
    """KILLED, SURVIVED, or neither — and `neither` is never quietly folded into one of them.

    Two events wear pytest's `<error>` tag and they mean opposite things here.

    A **collection** error is the invalid mutant: the module did not import, nothing ran, and no
    assertion was tested. It wins over everything — that is T4's case.

    A **setup or teardown** error is a real node the mutant broke on the way in or out. It is not a
    kill: no assertion fired, so nobody may write "pinned by test X" for it. But it must not erase
    a genuine `<failure>` beside it either — the baseline proved this selector green, so a failing
    assertion in the same run is a real kill, and tallying it as `0 killed` was this classifier's
    own defect (found by review, reproduced, `git log`).
    """
    if run.timed_out or run.collection_errors:
        return Outcome.ERRORED
    if run.failed:
        return Outcome.KILLED
    if run.setup_errors:
        return Outcome.ERRORED
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


def _refuse_stopping_early(where: str, parts: Sequence[str]) -> None:
    stopping = [part for part in parts if part in STOP_AT_FIRST_FAILURE]
    if stopping:
        raise MutationError(
            f"{where} carries {', '.join(stopping)}. A run that stops at the first failure reports "
            f"on test ordering rather than on the mutant, so this harness never passes it and will "
            f"not accept it from a battery either."
        )


def load_battery(path: Path, root: Path) -> Battery:
    """Parse and validate the battery, resolving every target against the repository root.

    Every refusal here needs no subprocess, so a malformed battery costs nothing to reject.
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
        _refuse_stopping_early(f"{path}: `pytest`", command)

    entries = _array(data.get("mutant", []), f"{path}: `mutant`")
    if not entries:
        raise MutationError(
            f"{path}: no mutants. A battery needs at least one `[[mutant]]` table with "
            f"`file`, `old`, `new` and `kills`."
        )

    # Optional, and checked when present: a declared inventory. Nothing else in this tool or in
    # `tests/test_batteries.py` is a *count*, so a committed battery could shrink to a single
    # mutant with every check still green — and the sanctioned repair for a property that has
    # genuinely gone is to delete its mutant, which makes shrinking the cheapest path to green
    # during a refactor. Deleting a row then has to be a two-line edit that says so.
    if "mutants" in data:
        declared = data["mutants"]
        if not isinstance(declared, int) or isinstance(declared, bool):
            raise MutationError(f"{path}: `mutants` must be an integer count, not {declared!r}")
        if declared != len(entries):
            raise MutationError(
                f"{path}: declares `mutants = {declared}` and carries {len(entries)}. If a mutant "
                f"was deleted on purpose, say so in its section and change the count in the same "
                f"edit; a corpus that can shrink silently reports on a question nobody asked."
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
        _refuse_stopping_early(f"{where}: `kills`", selectors)

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
    """Every refusal that can be made before the first write is made before the first write."""
    targets = list(dict.fromkeys(mutant.path for mutant in battery.mutants))
    refuse_a_relocated_bytecode_cache()
    refuse_a_test_file(root, battery.mutants)
    refuse_unless_committed(root, targets)
    refuse_an_anchor_that_is_not_unique(battery.mutants)
    refuse_a_mutant_that_cannot_compile(battery.mutants)
    for target in targets:
        _ = clear_pycache(target)

    baselines: dict[tuple[str, ...], PytestRun] = {}
    for mutant in battery.mutants:
        if mutant.selectors not in baselines:
            baselines[mutant.selectors] = check_baseline(root, battery.pytest, mutant.selectors)
    for selectors, run in baselines.items():
        print(
            f"baseline: {run.ran} test(s) ran and passed in {run.seconds:.1f}s "
            f"— `{' '.join(selectors)}`" + (f" ({len(run.skipped)} skipped)" if run.skipped else "")
        )
    print()

    results: list[Result] = []
    for index, mutant in enumerate(battery.mutants, start=1):
        print(f"[{index}/{len(battery.mutants)}] {mutant.name}")
        print(f"        {mutant.path.name}: {mutant.edit}")
        baseline = baselines[mutant.selectors]
        timeout = max(TIMEOUT_FLOOR_SECONDS, TIMEOUT_FACTOR * baseline.seconds)
        with applied(mutant):
            run = run_pytest(root, battery.pytest, mutant.selectors, timeout=timeout)
        result = Result(mutant, classify(run), run)
        results.append(result)
        print(f"        {_render(result, baseline)}\n")

    still_dirty = [
        target.relative_to(root).as_posix()
        for target in targets
        if git("status", "--porcelain", "--", target.relative_to(root).as_posix(), cwd=root)
    ]
    if still_dirty:
        raise MutationError(
            "the battery finished but git still sees a change in: "
            + ", ".join(still_dirty)
            + ".\nEvery restore reported success, so this is the harness disagreeing with itself. "
            "Recover with `git checkout --` on those paths and treat the whole report as void."
        )
    return results


def _render(result: Result, baseline: PytestRun) -> str:
    run = result.run
    scale = f"{{}} of {baseline.ran} test(s) in the selector"
    if result.outcome is Outcome.KILLED:
        killers = "\n        ".join(f"{node} — {why}" for node, why in run.failed)
        caveat = ""
        if run.setup_errors:
            broke = ", ".join(node for node, _ in run.setup_errors)
            caveat = (
                f"\n        (and it broke setup or teardown for {broke}, which is not a kill — "
                f"no assertion there fired)"
            )
        return f"KILLED — {scale.format(len(run.failed))} failed:\n        {killers}{caveat}"
    if result.outcome is Outcome.SURVIVED:
        return (
            f"SURVIVED — all {baseline.ran} test(s) in the selector passed with the mutant in "
            f"place. Nothing here pins this assertion; before believing it, check the mutant "
            f"really does break the case it claims to."
        )
    if run.timed_out:
        return (
            f"ERRORED (not a kill) — the run did not finish within {run.seconds:.0f}s, "
            f"{TIMEOUT_FACTOR} times its baseline. The mutant probably removed something's exit "
            f"condition; nothing is known about the assertion."
        )
    if run.collection_errors:
        detail = "\n        ".join(f"{node} — {why}" for node, why in run.collection_errors)
        return f"ERRORED (not a kill) — the mutant did not run:\n        {detail}"
    if run.setup_errors:
        detail = "\n        ".join(f"{node} — {why}" for node, why in run.setup_errors)
        return (
            f"ERRORED (not a kill) — the mutant broke setup or teardown, so it was noticed but no "
            f"assertion fired. This does not pin anything; give the behaviour a test that asserts "
            f"it directly:\n        {detail}"
        )
    return (
        f"ERRORED (not a kill) — pytest exited {run.exit_code} with "
        f"{run.collected} test(s) collected and {run.ran} run:\n{_tail(run.output)}"
    )


#: What the probe below asks the launcher to run. One line, so a shell-quoted command stays short.
_INTERPRETER_PROBE = "import sys; print(sys.version.split()[0] + ' at ' + sys.executable)"


def probe_command(command: Sequence[str]) -> list[str] | None:
    """The `pytest` command, rewritten to print its interpreter instead of running tests.

    **The launcher is asked, never this process.** `mutate.py`'s own `sys.version` is the wrong
    answer and would be wrong in exactly the case worth reporting: the documented invocation is
    `python3 tools/mutate.py`, which is the *system* interpreter, while the tests run under
    `uv run --frozen pytest` — the project venv. Printing the launcher's own version would have
    read as an answer while naming a Python no test ever touched.

    Two shapes, because those are the two this tool documents: the default `[… , "pytest"]` and
    the `[sys.executable, "-m", "pytest"]` form the tests use. Anything else returns `None` and is
    reported as unknown rather than guessed at — the same stance `run_pytest` takes towards a
    JUnit report it cannot parse.
    """
    if len(command) >= 2 and tuple(command[-2:]) == ("-m", "pytest"):
        return [*command[:-2], "-c", _INTERPRETER_PROBE]
    if command and command[-1] == "pytest":
        return [*command[:-1], "python", "-c", _INTERPRETER_PROBE]
    return None


def interpreter_under_test(root: Path, command: Sequence[str]) -> str | None:
    """The Python the tests ran under, or `None` if this run could not establish it.

    One extra subprocess per battery, not per mutant. It exists because a battery's verdict can
    depend on the interpreter and the report could not say which one produced it: the row for
    `doctor`'s root guard is KILLED on 3.13 and SURVIVED on 3.14 — equivalent above the floor,
    since both spellings answer `False` there — and a reader handed `67 killed` had no way to tell
    which of the two numbers they were holding. A count whose meaning depends on an unstated
    variable is the shape this repository keeps being caught by.
    """
    probe = probe_command(command)
    if probe is None:
        return None
    try:
        completed = subprocess.run(
            probe,
            cwd=root,
            env=child_environment(),
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    answer = completed.stdout.strip().splitlines()
    return answer[-1] if completed.returncode == 0 and answer else None


def report(results: Sequence[Result], *, allow_zero_kills: bool, interpreter: str | None) -> int:
    """Print the summary and decide the exit status. Survivors are a finding, not a failure.

    The summary is a Markdown table on purpose. Every battery in this repository's record was
    hand-written into a commit message in one of four different shapes, and `RETROSPECTIVES`
    observes that *"a number for the battery is unverifiable afterwards — the runs leave no
    artefact"*. This is the artefact, in the shape the record already uses, ready to paste.
    """
    tally = {outcome: [r for r in results if r.outcome is outcome] for outcome in Outcome}
    print("| Mutant | Outcome | Killed by |")
    print("|---|---|---|")
    for outcome in Outcome:
        for result in tally[outcome]:
            killers = (
                ", ".join(f"`{node}`" for node, _ in result.run.failed)
                if outcome is Outcome.KILLED
                else "—"
            ) or "—"
            print(f"| {result.mutant.name} | {outcome.value} | {killers} |")
    print(
        f"\n{len(results)} mutant(s): {len(tally[Outcome.KILLED])} killed, "
        f"{len(tally[Outcome.SURVIVED])} survived, {len(tally[Outcome.ERRORED])} errored."
    )
    # **Beside the counts, not only in the header**, because the counts are what gets pasted into a
    # commit message and the header is what gets left behind in the terminal.
    print(
        f"tests ran under Python {interpreter}."
        if interpreter is not None
        else "tests ran under an interpreter this run could not identify — the `pytest` command is "
        "neither `… pytest` nor `… -m pytest`, so these counts do not say which Python produced "
        "them."
    )

    if tally[Outcome.ERRORED]:
        print(
            "\nmutate: an ERRORED mutant is neither killed nor survived. It never ran (an invalid "
            "mutant), never finished, or broke setup rather than an assertion — read the rows to "
            "see which. Nothing here pins the assertions those mutants aimed at.",
            file=sys.stderr,
        )
        return 1
    if not tally[Outcome.KILLED] and not allow_zero_kills:
        print(
            "\nmutate: nothing died. A batch with no kills is a broken harness, not a clean bill. "
            "The recorded causes, in the order they are worth checking: the tests are running a "
            "different copy of the code (a `.venv` carried into a copied tree ran the original "
            "worktree's source and reported all 29 mutants surviving), the package is installed "
            "non-editable, or the selector does not reach the mutated module at all. Add a mutant "
            "you know is caught and run again; pass --allow-zero-kills only for a backstop already "
            "documented as unpinned.",
            file=sys.stderr,
        )
        return 1
    if tally[Outcome.SURVIVED]:
        print(
            "\nA SURVIVED row is a real finding: that assertion is not pinned by the test named "
            "beside it. It is not a harness failure, so this exits 0 — read the rows."
        )
    return 0


EPILOG = """\
The battery is TOML. `pytest` is optional and defaults to `uv run --frozen pytest`:

    pytest = ["uv", "run", "--frozen", "pytest"]

    [[mutant]]
    name  = "the depth cap is a max(), so a deep walk is never clamped"
    file  = "src/pinakes/graph/traverse.py"
    old   = '''min(depth, MAX_DEPTH)'''
    new   = '''max(depth, MAX_DEPTH)'''
    kills = "tests/test_traverse.py::test_depth_is_clamped_to_the_server_maximum"

`old` must occur exactly once in `file`, and `kills` is one selector or an array of them. Targets
under tests/ are refused: mutating a test stays manual. See tools/mutate.py's own docstring.

Committed batteries live in tools/batteries/, one per target. `--check-anchors` reads any number of
them, resolves every anchor against the working tree and exits — it runs nothing and writes nothing,
so it is the cheap way to ask whether they still hold after a refactor.
"""


# --------------------------------------------------------------------------------------------
# checking a battery without running it
# --------------------------------------------------------------------------------------------


def check_anchors(root: Path, loaded: Sequence[tuple[Path, Battery]]) -> int:
    """Resolve every anchor against the working tree, write nothing, and report *every* failure.

    This is `run_battery`'s pre-flight minus the subprocesses. It exists because
    [`tools/batteries/`](batteries/README.md) made a battery something that outlives the increment
    that wrote it, and the question *do the committed batteries still say anything?* has to be
    answerable in milliseconds or nobody will ask it. A full run answers it too, and charges a
    pytest baseline per distinct selector for the privilege.

    Three deliberate differences from a run:

    * **the working tree, not `HEAD`.** A run refuses an uncommitted target, because after a
      `SIGKILL` the only recovery is `git checkout <file>` and that must be safe. Nothing is
      written here, so that refusal would buy nothing and would disarm the check in the one moment
      it is wanted — mid-refactor, before the commit;
    * **every failure, not the first.** A run refuses the batch on the first stale anchor, since it
      must not write a mutant it cannot place. A repair wants the whole list;
    * **no file may be claimed by two batteries**, which is only visible when several are read at
      once — the shape this check is for. Two batteries mutating one file is how two increments end
      up maintaining two sets of mutants for it that can disagree.

    **What it cannot see**, and it says so on success rather than leaving a green line to be
    misread: a `kills` selector naming a test that has been renamed away — caught by the baseline,
    which needs pytest — and an anchor that still matches while the code around it moved, so the
    mutant would be KILLED about a property nobody tests any more. Nothing detects the second; it
    is why a mutant's `name` states what the breakage *is* rather than what the edit does.
    """
    problems: list[str] = []
    claimed: dict[Path, set[Path]] = {}

    for path, battery in loaded:
        # Collected, never raised. `run_battery` raises here because it must not write a mutant it
        # cannot place; this mode promises *every* failure, and an exception on battery 1 of 4
        # would throw away the problems already found and never read batteries 2 to 4.
        try:
            refuse_a_test_file(root, battery.mutants)
            refuse_a_mutant_that_cannot_compile(battery.mutants)
        except MutationError as exc:
            problems.append(f"{path}: {exc}")
        stale = 0
        for mutant in battery.mutants:
            claimed.setdefault(mutant.path, set()).add(path.resolve())
            if not mutant.path.is_file():
                stale += 1
                problems.append(
                    f"{path}: {mutant.name}: {mutant.path.relative_to(root).as_posix()} does not "
                    f"exist — the target was renamed or deleted, and the anchor cannot be located."
                )
                continue
            text = _decoded(mutant.path)
            count = text.count(mutant.old)
            if count != 1:
                stale += 1
                problems.append(f"{path}: {_bad_anchor_message(mutant, count, text)}")
        targets = len({mutant.path for mutant in battery.mutants})
        verdict = f"{stale} stale" if stale else "all resolve"
        print(f"{path}: {len(battery.mutants)} anchor(s) over {targets} file(s) — {verdict}")

    for target, batteries in sorted(claimed.items()):
        # Resolved, so the same battery named twice under two spellings — `b.toml` and `./b.toml`,
        # or a path through a symlink — is one battery and not a double claim.
        if len(batteries) > 1:
            problems.append(
                f"{target.relative_to(root).as_posix()} is claimed by "
                + ", ".join(sorted(battery.as_posix() for battery in batteries))
                + " — a file belongs to exactly one battery, so that an increment touching it "
                "again has one place to add to and cannot leave two sets of mutants that disagree."
            )

    if problems:
        print()
        # stdout is block-buffered when this is piped and stderr is not, so without the flush the
        # per-battery summary lines land *below* the problems they summarise.
        sys.stdout.flush()
        for problem in problems:
            print(f"mutate: {problem}", file=sys.stderr)
        print(f"\n{len(problems)} problem(s). Nothing was written.", file=sys.stderr)
        return 1
    print(
        "\nEvery anchor resolves. That is not a green run: a `kills` selector renamed away is "
        "caught by the baseline, which needs pytest, and an anchor that still matches while the "
        "code around it moved is caught by nothing."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a mutation battery: apply each mutant, run the tests that should catch "
        "it, restore, and report which assertions are actually pinned.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _ = parser.add_argument(
        "battery",
        type=Path,
        nargs="+",
        help="the TOML battery file — several only with --check-anchors",
    )
    _ = parser.add_argument(
        "--check-anchors",
        action="store_true",
        help="resolve every anchor against the working tree and exit, running nothing and "
        "writing nothing — the cheap way to ask whether the committed batteries still hold",
    )
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
    battery_paths: list[Path] = args.battery
    check_only: bool = args.check_anchors
    allow_zero_kills: bool = args.allow_zero_kills
    start: Path = args.repo if args.repo is not None else Path.cwd()

    def _restore_and_die(signum: int, _frame: FrameType | None) -> None:
        """These signals end the process without unwinding, so `finally` never runs and the mutant
        stays on disk — measured for SIGTERM, 1 of 1. Raising turns it back into an unwind."""
        raise KeyboardInterrupt(f"signal {signal.Signals(signum).name}")

    for name in UNWINDLESS_SIGNALS:
        handled = getattr(signal, name, None)
        if handled is not None:  # pragma: no branch — all three exist on every POSIX target
            _ = signal.signal(handled, _restore_and_die)

    try:
        root = repo_root(start.resolve())
        if check_only:
            return check_anchors(root, [(p, load_battery(p, root)) for p in battery_paths])
        if len(battery_paths) > 1:
            raise MutationError(
                "run one battery at a time. The exit status is a claim about one batch, so a "
                "second battery's kills would be counted into the first's and `--allow-zero-kills` "
                "would excuse a batch that was never meant to need it. `--check-anchors` takes as "
                "many as you like."
            )
        battery = load_battery(battery_paths[0], root)
        print(
            f"mutate: {len(battery.mutants)} mutant(s) in {root}, "
            f"pytest = {shlex.join(battery.pytest)}\n"
        )
        results = run_battery(root, battery)
    except MutationError as exc:
        # stdout is block-buffered when piped and stderr is not, so without this the refusal
        # prints *above* the per-battery lines it applies to — the inverse of what happened.
        sys.stdout.flush()
        print(f"mutate: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt as exc:
        sys.stdout.flush()
        # `--check-anchors` writes nothing, so it has no restore to claim. Saying it did would be
        # the one kind of false reassurance this tool is built to avoid.
        restored = (
            " — nothing was written, so there was nothing to restore."
            if check_only
            else " — the target was restored on the way out."
        )
        print(f"\nmutate: interrupted ({exc}){restored}", file=sys.stderr)
        return 1
    return report(
        results,
        allow_zero_kills=allow_zero_kills,
        interpreter=interpreter_under_test(root, battery.pytest),
    )


if __name__ == "__main__":
    raise SystemExit(main())
