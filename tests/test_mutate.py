"""`tools/mutate.py` — the CLI as a subprocess, the guards a subprocess cannot see in-process.

A subprocess for the reason `tests/test_land.py` gives: it exercises the same artifact a human
runs, argument parsing included, with no `sys.path` surgery. The in-process half exists for the
properties a subprocess cannot observe — whether a `.pyc` existed *during* a mutation, and what
happens when a restore does not take — in the sense `tests/test_deep_reservation.py` uses.

**The assertion that matters is not "it ran a battery".** It is that the harness refuses, or reports
its own brokenness, in each of the ways a mutation run has silently lied here before. A suite that
only drove the happy path would pass with every guard deleted, and the guards *are* the tool.

Three rules hold throughout:

* **every refusal asserts the stated reason**, never merely a non-zero exit;
* **a refusal that claims to happen "before the first write" asserts that nothing ran** — not just
  that the file came back unchanged, which is equally true of a mutation that was applied and then
  restored. That distinction is the one this file got wrong first;
* **every guard has a control that proves it is not ceremony.** The bytecode-invalidation pin is
  followed by `test_a_stale_pyc_really_does_report_a_same_length_mutant_as_survived`, which forges
  the exact condition by hand and watches the mutant vanish. If the control ever stops reproducing,
  the pin is guarding nothing.

**The fixture sources are `textwrap.dedent`ed on purpose.** `tests/test_verification.py` resolves a
named test by scanning a file for `^def (\\w+)` with `re.MULTILINE`, so a `def test_…` at column 0
*inside a string literal here* would make that gate resolve a test this module does not define — a
false positive in the one gate built so the table "can go stale exactly once, in the commit that
breaks it". Indenting the literals keeps them out of its way.

The scratch repository runs `sys.executable -m pytest` rather than the battery's default
`uv run --frozen pytest`: `-m` puts the working directory on `sys.path`, which is how a package
that was never installed becomes importable. That is the battery's `pytest` key doing its job, and
it keeps the nested run to a few hundred milliseconds.
"""

import importlib.util
import os
import signal
import struct
import subprocess
import sys
import textwrap
import time
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest

TOOL = Path(__file__).parent.parent / "tools" / "mutate.py"

ORIGINAL_MODULE = textwrap.dedent(
    '''\
    """A scratch module: one pinned assertion, one unpinned function, and two markers."""

    MAX = 3
    MARKER = "original"
    RUNNABLE = True


    def clamp(value: int) -> int:
        return min(value, MAX)


    def describe() -> str:
        return "nothing asserts this"
    '''
)

PINNING_TESTS = textwrap.dedent(
    """\
    from pkg.mod import clamp


    def test_clamp_caps_at_the_maximum() -> None:
        assert clamp(10) == 3
    """
)

SLOW_TEST = textwrap.dedent(
    """\
    import time

    import pkg.mod
    from pkg.mod import clamp


    def test_clamp_caps_at_the_maximum_slowly() -> None:
        # Fast at baseline, thirty seconds once the marker mutant is in place: that is what gives
        # the kill-it-mid-run and the timeout tests a window they do not have to race for.
        if pkg.mod.MARKER != "original":
            time.sleep(30)
        assert clamp(10) == 3
    """
)

SKIPPABLE_TEST = textwrap.dedent(
    """\
    import pytest

    import pkg.mod


    @pytest.mark.skipif(not pkg.mod.RUNNABLE, reason="the extra is absent")
    def test_clamp_caps_when_it_can_run() -> None:
        assert pkg.mod.clamp(10) == 3
    """
)


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def mutate(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed scratch repository: a package, tests that pin one line of it, and a config.

    `pytest.ini` is not decoration — without it the nested pytest walks up out of `tmp_path`
    looking for a rootdir, and on a machine where that search reaches a real project it would
    collect somebody else's tests.
    """
    root = tmp_path / "scratch"
    (root / "pkg").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "mod.py").write_text(ORIGINAL_MODULE, encoding="utf-8")
    (root / "tests" / "test_pkg.py").write_text(PINNING_TESTS, encoding="utf-8")
    (root / "tests" / "test_slow.py").write_text(SLOW_TEST, encoding="utf-8")
    (root / "tests" / "test_skippable.py").write_text(SKIPPABLE_TEST, encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")

    _ = git("init", "-q", "--initial-branch=main", ".", cwd=root)
    _ = git("config", "user.email", "test@example.invalid", cwd=root)
    _ = git("config", "user.name", "Test", cwd=root)
    _ = git("add", "-A", cwd=root)
    _ = git("commit", "-q", "-m", "scratch", cwd=root)
    return root


def battery(
    root: Path,
    *mutants: dict[str, str | list[str]],
    command: Sequence[str] | None = None,
) -> Path:
    """Write a battery file. `'''` quoting is what lets an anchor carry quotes and backslashes."""
    parts = [
        "pytest = ["
        + ", ".join(f'"{part}"' for part in (command or [sys.executable, "-m", "pytest"]))
        + "]\n"
    ]
    for mutant in mutants:
        parts.append("[[mutant]]")
        for key, value in mutant.items():
            if isinstance(value, list):
                parts.append(f"{key} = [" + ", ".join(f'"{item}"' for item in value) + "]")
            elif key in ("old", "new"):
                parts.append(f"{key} = '''{value}'''")
            else:
                parts.append(f'{key} = "{value}"')
        parts.append("")
    path = root / "battery.toml"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def clamp_mutant(**overrides: str | list[str]) -> dict[str, str | list[str]]:
    """The battery's workhorse: a same-length mutant of the one line the scratch test pins."""
    mutant: dict[str, str | list[str]] = {
        "name": "the cap is a max(), so nothing is ever clamped",
        "file": "pkg/mod.py",
        "old": "min(value, MAX)",
        "new": "max(value, MAX)",
        "kills": "tests/test_pkg.py::test_clamp_caps_at_the_maximum",
    }
    mutant.update(overrides)
    return mutant


def warm(root: Path, selector: str = "tests/test_pkg.py") -> None:
    """Run the scratch suite once, so a `.pyc` for `pkg/mod.py` exists."""
    _ = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", selector],
        cwd=root,
        capture_output=True,
        check=False,
    )


def tool_module() -> ModuleType:
    """`tools/` is not a package, so the tool is loaded by path — `test_deep_reservation.py`'s
    idiom, `sys.modules` registration included."""
    spec = importlib.util.spec_from_file_location("pnk_mutate", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["pnk_mutate"] = module
    spec.loader.exec_module(module)
    return module


def assert_nothing_ran(result: subprocess.CompletedProcess[str]) -> None:
    """A refusal that claims to precede the first write must precede the first *run* too.

    Asserting only that the target's bytes are unchanged is satisfied by a mutation that was
    applied and then restored, which is exactly what the guard is supposed to prevent. The absence
    of any `[n/N]` header and of any baseline line is what says no work began.
    """
    assert "[1/" not in result.stdout, f"a mutant was attempted:\n{result.stdout}"
    assert "baseline:" not in result.stdout, f"a baseline run happened:\n{result.stdout}"


# ---------------------------------------------------------------------------------------------
# The three outcomes, and only three
# ---------------------------------------------------------------------------------------------


def test_a_mutant_the_tests_catch_is_killed_and_names_the_test_that_caught_it(repo: Path) -> None:
    """KILLED is not "a test failed" — it is *which* test failed, on what assertion, and how many
    of the selector's tests that was. The count is what makes a silently narrowed selection
    visible: the record holds a battery where a `-k` filter selected four of six tests and a mutant
    read as caught by one test when three catch it."""
    result = mutate(str(battery(repo, clamp_mutant())), cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "KILLED — 1 of 1 test(s) in the selector failed" in result.stdout
    assert "tests/test_pkg.py::test_clamp_caps_at_the_maximum" in result.stdout
    assert "assert 10 == 3" in result.stdout


def test_a_mutant_nothing_catches_survives_and_the_run_still_exits_zero(repo: Path) -> None:
    """A survivor is a finding about the *tests*, not a failure of the harness — so it must not be
    reported by an exit code that reads as "the tool broke". It needs a kill beside it, because a
    batch of nothing but survivors is the broken-harness case tested further down."""
    path = battery(
        repo,
        clamp_mutant(),
        clamp_mutant(
            name="nothing asserts the description",
            old="nothing asserts this",
            new="something else entirely",
        ),
    )
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "SURVIVED" in result.stdout
    assert "Nothing here pins this assertion" in result.stdout
    assert "1 killed, 1 survived, 0 errored" in result.stdout


def test_an_invalid_mutant_is_its_own_outcome_never_killed_and_never_survived(repo: Path) -> None:
    """T4 misread a collection `ERROR` in both directions: once as a kill, once as a survival.
    pytest exits 2 for it, and the JUnit report carries `<error>` where a real failure carries
    `<failure>` — which is why the classification reads the report and not the exit code."""
    path = battery(repo, clamp_mutant(name="a mutant that does not parse", new="min(value, MAX"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "ERRORED" in result.stdout
    assert "KILLED" not in result.stdout
    assert "SURVIVED" not in result.stdout
    assert "0 killed, 0 survived, 1 errored" in result.stdout
    assert "neither killed nor survived" in result.stderr


def test_a_mutant_that_makes_every_test_skip_is_not_a_survivor(repo: Path) -> None:
    """The mutant-time half of the skip problem, and the one `check_baseline` cannot reach.

    A mutant that flips a `skipif` predicate leaves pytest exiting 0 with nothing having run — the
    SURVIVED signal, produced by the mutant switching off its own judge. `classify` requires
    `ran > 0` for SURVIVED; deleting that clause is invisible to every other test here.
    """
    path = battery(
        repo,
        clamp_mutant(
            name="the mutant switches its own test off",
            old="RUNNABLE = True",
            new="RUNNABLE = False",
            kills="tests/test_skippable.py::test_clamp_caps_when_it_can_run",
        ),
    )
    result = mutate(str(path), cwd=repo)

    assert "SURVIVED" not in result.stdout, result.stdout
    assert "ERRORED" in result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------------------------
# The anchor
# ---------------------------------------------------------------------------------------------


def test_an_anchor_that_matches_nothing_refuses_before_writing_anything(repo: Path) -> None:
    """`str.replace` that matches nothing returns the string unchanged and reports to no one: the
    file is untouched, every test passes, and the row reads SURVIVED."""
    before = (repo / "pkg" / "mod.py").read_bytes()
    result = mutate(str(battery(repo, clamp_mutant(old="min(value, CEILING)"))), cwd=repo)

    assert result.returncode == 1
    assert "occurs 0 times" in result.stderr
    assert "would read SURVIVED" in result.stderr
    assert "min(value, CEILING)" in result.stderr
    assert (repo / "pkg" / "mod.py").read_bytes() == before
    assert_nothing_ran(result)


def test_an_anchor_that_matches_twice_refuses_rather_than_choosing(repo: Path) -> None:
    """Two matches mean the battery did not say which line it meant. Replacing both is a different
    mutant from the one written down, and replacing the first is a coin toss."""
    result = mutate(str(battery(repo, clamp_mutant(old="value", new="other"))), cwd=repo)

    assert result.returncode == 1
    assert "exactly once" in result.stderr
    assert "not stated" in result.stderr
    assert_nothing_ran(result)


def test_a_stale_anchor_in_the_last_mutant_refuses_before_the_first_one_runs(repo: Path) -> None:
    """Why the anchor check is a pre-flight and not only a per-mutant check.

    A typo in the third anchor is the commonest battery error, since anchors are hand-copied source
    fragments. Checked only at write time it would mutate and run two mutants first, then unwind
    with no summary at all — two pytest runs whose results are discarded.
    """
    path = battery(
        repo,
        clamp_mutant(name="one"),
        clamp_mutant(name="two", old="nothing asserts this", new="x"),
        clamp_mutant(name="three, with a stale anchor", old="min(value, GONE)"),
    )
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "occurs 0 times" in result.stderr
    assert_nothing_ran(result)


def test_a_mutant_whose_old_and_new_are_identical_is_refused(repo: Path) -> None:
    """The file would not change, so the row would read SURVIVED whatever the tests do."""
    result = mutate(str(battery(repo, clamp_mutant(new="min(value, MAX)"))), cwd=repo)

    assert result.returncode == 1
    assert "identical" in result.stderr


def test_an_indentation_only_mutant_is_not_rendered_as_a_no_op(repo: Path) -> None:
    """The report collapses a multi-line anchor to one line by stripping each line, which erases an
    indentation-only mutant: both sides of the arrow print the same string and the row says nothing
    about what changed. It falls back to `repr` when that would happen."""
    path = battery(
        repo,
        clamp_mutant(
            name="the return is indented one level deeper",
            old="    return min(value, MAX)",
            new="        return min(value, MAX)",
        ),
    )
    result = mutate(str(path), cwd=repo)

    assert "`return min(value, MAX)` → `return min(value, MAX)`" not in result.stdout
    assert "'    return min(value, MAX)'" in result.stdout


# ---------------------------------------------------------------------------------------------
# The target, and getting it back
# ---------------------------------------------------------------------------------------------


def test_a_target_that_differs_from_head_is_refused_before_the_first_write(repo: Path) -> None:
    """Six recorded incidents end `git checkout <file>`, which restores to the last commit and
    takes the uncommitted fix with it. This harness restores from a snapshot instead — but a
    snapshot dies with the process, so `HEAD` is the only recovery after a hard kill."""
    source = repo / "pkg" / "mod.py"
    source.write_text(ORIGINAL_MODULE + "\n# an uncommitted fix\n", encoding="utf-8")
    before = source.read_bytes()

    result = mutate(str(battery(repo, clamp_mutant())), cwd=repo)

    assert result.returncode == 1
    assert "differ from HEAD" in result.stderr
    assert "pkg/mod.py" in result.stderr
    assert source.read_bytes() == before, "the refusal must not have touched the file"
    assert_nothing_ran(result)


def test_a_gitignored_target_is_refused_because_git_checkout_could_not_recover_it(
    repo: Path,
) -> None:
    """`git status --porcelain` prints nothing for an ignored file, so cleanliness alone passes a
    file with no `HEAD` version at all — and for that file the `git checkout --` this refusal
    exists to guarantee answers "did not match any file(s) known to git"."""
    (repo / ".gitignore").write_text("generated.py\n", encoding="utf-8")
    (repo / "generated.py").write_text("VALUE = 1\n", encoding="utf-8")
    _ = git("add", "-A", cwd=repo)
    _ = git("commit", "-q", "-m", "ignore a generated module", cwd=repo)
    assert git("status", "--porcelain", "--", "generated.py", cwd=repo) == "", (
        "fixture: git must consider this file clean, which is the whole trap"
    )

    path = battery(repo, clamp_mutant(file="generated.py", old="VALUE = 1", new="VALUE = 2"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "not tracked by git" in result.stderr
    assert "generated.py" in result.stderr
    assert_nothing_ran(result)


def test_a_test_file_target_is_refused_because_mutating_a_test_stays_manual(repo: Path) -> None:
    """A mutant in the file its own selector runs can make that test vacuous — delete the
    assertion and the test still passes — and SURVIVED is then a statement about nothing."""
    path = battery(
        repo,
        clamp_mutant(file="tests/test_pkg.py", old="clamp(10) == 3", new="clamp(10) == clamp(10)"),
    )
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "mutating a test stays manual" in result.stderr
    assert "tests/test_pkg.py" in result.stderr
    assert_nothing_ran(result)


def test_the_target_is_restored_byte_for_byte_after_a_run(repo: Path) -> None:
    source = repo / "pkg" / "mod.py"
    before = source.read_bytes()

    result = mutate(str(battery(repo, clamp_mutant())), cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert source.read_bytes() == before
    assert git("status", "--porcelain", "--", "pkg/mod.py", cwd=repo) == ""


@pytest.mark.parametrize("signum", [signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT])
def test_the_target_is_restored_when_the_run_is_killed_mid_flight(
    repo: Path, signum: signal.Signals
) -> None:
    """These signals end the process without unwinding, so a plain `try/finally` never runs and the
    mutant stays on disk — measured for SIGTERM, 1 of 1, before the handler existed.

    Parametrised because handling one of them is not handling the others, and dropping the other
    two from `UNWINDLESS_SIGNALS` is a one-word edit that a SIGTERM-only test cannot see. SIGINT is
    absent: Python already raises `KeyboardInterrupt` for it, which is why the hazard is invisible
    to anyone who only ever tests with Ctrl-C.
    """
    source = repo / "pkg" / "mod.py"
    before = source.read_bytes()
    path = battery(
        repo,
        clamp_mutant(
            name="the marker mutant, which makes the slow test sleep",
            old='MARKER = "original"',
            new='MARKER = "mutated!"',
            kills="tests/test_slow.py::test_clamp_caps_at_the_maximum_slowly",
        ),
    )

    process = subprocess.Popen(
        [sys.executable, str(TOOL), str(path)],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 60
        while source.read_bytes() == before:
            assert time.monotonic() < deadline, "the mutant was never written"
            assert process.poll() is None, "the run ended before the mutant was applied"
            time.sleep(0.05)
        process.send_signal(signum)
        _, stderr = process.communicate(timeout=60)
    finally:
        if process.poll() is None:  # pragma: no cover — only on a failed run
            process.kill()

    assert source.read_bytes() == before, f"{signum.name} left the mutant on disk"
    assert "restored" in stderr


def test_a_restore_that_did_not_take_is_caught_rather_than_trusted(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The plan's step 5, and the guard nothing had ever watched fire.

    Verifying the restored bytes is the last line of defence for the failure class the tool exists
    for, and it can only be observed by making the write silently not take — which no battery can
    do. The seam is `Path.write_bytes`, neutered for the *restore* call and nothing else; the region
    it removes from coverage is one statement wide, and the test above drives the real thing.
    """
    module = tool_module()
    source = repo / "pkg" / "mod.py"
    mutant = module.Mutant(
        name="the restore is sabotaged",
        path=source,
        old="min(value, MAX)",
        new="max(value, MAX)",
        selectors=("tests/test_pkg.py",),
    )

    real_write = Path.write_bytes
    writes: list[int] = []

    def flaky(self: Path, data: bytes) -> int:
        writes.append(1)
        if len(writes) == 2 and self == source:  # the restore, and only the restore
            return len(data)
        return real_write(self, data)

    monkeypatch.setattr(Path, "write_bytes", flaky)
    with (
        pytest.raises(module.MutationError, match="was NOT restored"),
        module.applied(mutant),
    ):
        pass
    monkeypatch.undo()

    assert "max(value, MAX)" in source.read_text(encoding="utf-8"), (
        "fixture: the sabotage should have left the mutant in place — that is what was detected"
    )
    source.write_text(ORIGINAL_MODULE, encoding="utf-8")


def test_a_body_that_raises_still_restores(repo: Path) -> None:
    """L6, exercised on the `finally` itself rather than inferred from a later mutant's result.

    A syntactically invalid mutant does not raise in *this* process — pytest merely exits 2 — so
    the batch-ordering test below never enters an exception path at all. Raising inside the body is
    what proves the restore is in a `finally` and not merely at the end of the block.
    """
    module = tool_module()
    source = repo / "pkg" / "mod.py"
    before = source.read_bytes()
    mutant = module.Mutant(
        name="raise inside the body",
        path=source,
        old="min(value, MAX)",
        new="max(value, MAX)",
        selectors=("tests/test_pkg.py",),
    )

    with pytest.raises(RuntimeError, match="the run blew up"), module.applied(mutant):
        assert source.read_bytes() != before, "the mutant should be on disk here"
        raise RuntimeError("the run blew up")

    assert source.read_bytes() == before


def test_applied_refuses_a_bad_anchor_even_though_the_pre_flight_already_checked(
    repo: Path,
) -> None:
    """The redundant check, which nothing reaching the CLI can ever exercise.

    `run_battery` validates every anchor against the pristine files before the first write, so by
    the time `applied()` runs the question is settled — and a mutant deleting `applied()`'s own
    check would survive a battery-driven suite entirely. It is kept because `applied()` is a public
    context manager that may never write a mutant it cannot place, and redundancy nothing tests is
    indistinguishable from redundancy that has quietly stopped working.
    """
    module = tool_module()
    mutant = module.Mutant(
        name="an anchor that is not there",
        path=repo / "pkg" / "mod.py",
        old="min(value, CEILING)",
        new="max(value, CEILING)",
        selectors=("tests/test_pkg.py",),
    )
    before = (repo / "pkg" / "mod.py").read_bytes()

    with pytest.raises(module.MutationError, match="occurs 0 times"):  # noqa: SIM117
        with module.applied(mutant):
            pytest.fail("the body must never run for a mutant that cannot be placed")

    assert (repo / "pkg" / "mod.py").read_bytes() == before


def test_a_later_mutant_is_measured_on_a_clean_file(repo: Path) -> None:
    """Ordering: the invalid mutant goes first, and the valid one after it must still be killed."""
    path = battery(
        repo,
        clamp_mutant(name="a mutant that does not parse", new="min(value, MAX"),
        clamp_mutant(name="the good one, which must be unaffected"),
    )
    result = mutate(str(path), cwd=repo)

    assert "| a mutant that does not parse | ERRORED |" in result.stdout
    assert "| the good one, which must be unaffected | KILLED |" in result.stdout
    assert "1 killed, 0 survived, 1 errored" in result.stdout
    assert git("status", "--porcelain", "--", "pkg/mod.py", cwd=repo) == ""


# ---------------------------------------------------------------------------------------------
# The bytecode cache (T3) — the pin, and the control that proves it is not ceremony
# ---------------------------------------------------------------------------------------------


def pyc_of(source: Path) -> Path:
    matches = sorted((source.parent / "__pycache__").glob(f"{source.stem}.*.pyc"))
    assert len(matches) == 1, f"expected one cached bytecode file, found {matches}"
    return matches[0]


def test_the_bytecode_cache_is_cleared_after_the_write_and_after_the_restore(repo: Path) -> None:
    """The invalidation, pinned directly rather than through its consequence.

    Asserting the *outcome* of a same-length mutant would not pin this: whether the stale `.pyc` is
    used depends on the write landing in the same wall-clock second as the previous compile, which
    a slower machine would lose. The absence of the file is the same fact with no clock in it — and
    deleting either `clear_pycache` call turns this red.
    """
    module = tool_module()
    source = repo / "pkg" / "mod.py"
    warm(repo)
    assert module.pycache_entries(source), "fixture: nothing warmed the cache"

    mutant = module.Mutant(
        name="same length",
        path=source,
        old="min(value, MAX)",
        new="max(value, MAX)",
        selectors=("tests/test_pkg.py",),
    )
    with module.applied(mutant):
        assert module.pycache_entries(source) == [], "the cache survived the write"
        warm(repo)
        assert module.pycache_entries(source), "fixture: the mutated source was never compiled"
    assert module.pycache_entries(source) == [], "the cache survived the restore"


def test_a_stale_pyc_really_does_report_a_same_length_mutant_as_survived(repo: Path) -> None:
    """The control for the test above. Without it, clearing `__pycache__` is a ritual nobody has
    watched fail.

    CPython validates a timestamp `.pyc` on `(mtime-to-the-second, size)`. `min` → `max` changes
    neither, so the stale bytecode runs and the test passes with the mutant on disk. The condition
    is forged here — the source's mtime is set to the one the header recorded — rather than raced
    for, which is the only difference between this and the six-out-of-six reproduction that
    motivated the clearing.
    """
    source = repo / "pkg" / "mod.py"
    warm(repo)
    header = pyc_of(source).read_bytes()[:16]
    _, flags, recorded_mtime, recorded_size = struct.unpack("<4sIII", header)
    assert flags == 0, "not a timestamp-invalidated .pyc, so this control does not apply"

    original = source.read_text(encoding="utf-8")
    mutated = original.replace("min(value, MAX)", "max(value, MAX)")
    assert len(mutated) == len(original) == recorded_size, "the control needs a same-length mutant"
    source.write_text(mutated, encoding="utf-8")
    os.utime(source, (time.time(), recorded_mtime))

    stale = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_pkg.py"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert stale.returncode == 0, (
        "the stale .pyc no longer shadows a same-length mutant, so the clearing in `applied()` is "
        "now guarding a condition this interpreter does not produce:\n" + stale.stdout
    )

    pyc_of(source).unlink()
    fresh = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_pkg.py"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert fresh.returncode == 1, "clearing the cache must be what makes the mutant visible"


def test_a_same_length_mutant_is_killed_end_to_end(repo: Path) -> None:
    """The same mutant, through the real command. The two tests above say why this one passes."""
    warm(repo)
    result = mutate(str(battery(repo, clamp_mutant())), cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 killed" in result.stdout


def test_a_relocated_bytecode_cache_is_refused_rather_than_guessed_at(repo: Path) -> None:
    """`PYTHONPYCACHEPREFIX` puts every `.pyc` in a mirrored tree. Measured: with it set,
    `pkg/__pycache__` is never created at all — so the clearing finds nothing, removes nothing,
    reports success, and a same-length mutant reads SURVIVED off bytecode never seen."""
    result = subprocess.run(
        [sys.executable, str(TOOL), str(battery(repo, clamp_mutant()))],
        cwd=repo,
        env=dict(os.environ, PYTHONPYCACHEPREFIX=str(repo / "elsewhere")),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "PYTHONPYCACHEPREFIX" in result.stderr
    assert_nothing_ran(result)


# ---------------------------------------------------------------------------------------------
# `-x`, from all three directions it can arrive from
# ---------------------------------------------------------------------------------------------


def test_a_battery_that_asks_for_x_in_its_pytest_command_is_refused(repo: Path) -> None:
    path = battery(repo, clamp_mutant(), command=[sys.executable, "-m", "pytest", "-x"])
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "stops at the first failure" in result.stderr


def test_a_selector_that_smuggles_x_in_is_refused_too(repo: Path) -> None:
    """`kills` is passed to pytest verbatim, so it is the second door into the same room."""
    result = mutate(str(battery(repo, clamp_mutant(kills=["-x", "tests/test_pkg.py"]))), cwd=repo)

    assert result.returncode == 1
    assert "stops at the first failure" in result.stderr


def test_pytest_addopts_in_the_environment_cannot_narrow_the_run(repo: Path) -> None:
    """Measured: `PYTEST_ADDOPTS="-x"` turns a two-failure kill into a one-failure kill. It is
    inherited by any pytest, so without dropping it the "never `-x`" promise depends on the
    operator's shell — and the row would under-report which tests catch the mutant."""
    (repo / "tests" / "test_second.py").write_text(
        textwrap.dedent(
            """\
            from pkg.mod import clamp


            def test_clamp_caps_from_the_other_side() -> None:
                assert clamp(99) == 3
            """
        ),
        encoding="utf-8",
    )
    _ = git("add", "-A", cwd=repo)
    _ = git("commit", "-q", "-m", "a second test that catches the same mutant", cwd=repo)

    path = battery(repo, clamp_mutant(kills=["tests/test_pkg.py", "tests/test_second.py"]))
    result = subprocess.run(
        [sys.executable, str(TOOL), str(path)],
        cwd=repo,
        env=dict(os.environ, PYTEST_ADDOPTS="-x"),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "KILLED — 2 of 2 test(s) in the selector failed" in result.stdout, result.stdout


# ---------------------------------------------------------------------------------------------
# The controls the report refuses to run without
# ---------------------------------------------------------------------------------------------


def unpinned_battery(repo: Path) -> Path:
    return battery(
        repo,
        clamp_mutant(
            name="nothing asserts the description",
            old="nothing asserts this",
            new="something else entirely",
        ),
    )


def test_a_batch_with_no_kills_exits_non_zero_as_a_broken_harness(repo: Path) -> None:
    """A run where nothing died is the signature of a harness that is not reaching the code at
    all — a `.venv` carried into a copied tree, a non-editable install, a selector aimed elsewhere.
    Reporting it as a clean bill is the most expensive thing this tool could do."""
    result = mutate(str(unpinned_battery(repo)), cwd=repo)

    assert result.returncode == 1
    assert "0 killed, 1 survived" in result.stdout
    assert "nothing died" in result.stderr
    assert "broken harness" in result.stderr


def test_allow_zero_kills_accepts_the_same_batch(repo: Path) -> None:
    """The escape hatch the plan asks for: a deliberate probe of a backstop already documented as
    unpinned. It must change the exit status and nothing else about the report."""
    result = mutate(str(unpinned_battery(repo)), "--allow-zero-kills", cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 killed, 1 survived" in result.stdout
    assert "nothing died" not in result.stderr


# ---------------------------------------------------------------------------------------------
# The baseline — the ways a battery reports on a question it never asked
# ---------------------------------------------------------------------------------------------


def test_a_selector_whose_tests_all_skip_is_refused_before_anything_is_written(repo: Path) -> None:
    """Measured while building this, and not in the plan: a skipped test exits 0, byte for byte the
    SURVIVED signal. Pinakes skips on a missing extra as a matter of course (`pdf`, `paid`,
    `model`), so a battery aimed at one of those in a `[light]` checkout would report SURVIVED for
    every mutant in it and read as a clean bill."""
    (repo / "tests" / "test_skipped.py").write_text(
        textwrap.dedent(
            """\
            import pytest


            @pytest.mark.skip(reason="needs an extra")
            def test_needs_an_extra() -> None:
                assert False
            """
        ),
        encoding="utf-8",
    )
    _ = git("add", "-A", cwd=repo)
    _ = git("commit", "-q", "-m", "a test that skips here", cwd=repo)
    before = (repo / "pkg" / "mod.py").read_bytes()

    result = mutate(str(battery(repo, clamp_mutant(kills="tests/test_skipped.py"))), cwd=repo)

    assert result.returncode == 1
    assert "skipped in this checkout" in result.stderr
    assert "would read SURVIVED" in result.stderr
    assert (repo / "pkg" / "mod.py").read_bytes() == before
    assert "[1/" not in result.stdout


def test_a_selector_that_is_already_red_is_refused_rather_than_killing_every_mutant(
    repo: Path,
) -> None:
    """The other direction, and the worse one: against a red selector every mutant reads KILLED,
    including the ones nothing catches. The report is then a list of assertions certified as pinned
    by a test that was failing before the run began."""
    (repo / "tests" / "test_red.py").write_text(
        "def test_already_failing() -> None:\n    assert 1 == 2\n", encoding="utf-8"
    )
    _ = git("add", "-A", cwd=repo)
    _ = git("commit", "-q", "-m", "a red test", cwd=repo)

    path = battery(repo, clamp_mutant(kills="tests/test_red.py::test_already_failing"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "not green before any mutation" in result.stderr
    assert "tests/test_red.py::test_already_failing" in result.stderr
    assert "[1/" not in result.stdout


def test_a_selector_that_collects_nothing_is_refused(repo: Path) -> None:
    """pytest exits 5 and prints "no tests ran", which is not a failure — so an empty selector
    would otherwise report SURVIVED for everything aimed at it."""
    path = battery(repo, clamp_mutant(kills=["tests/test_pkg.py", "-k", "nothing_matches_this"]))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "collected no tests" in result.stderr


def test_a_selector_pytest_rejects_is_refused_naming_it(repo: Path) -> None:
    """A renamed test is the common case: the battery still names the old id, pytest exits 4, and
    nothing about the mutant was learned."""
    path = battery(repo, clamp_mutant(kills="tests/test_pkg.py::test_renamed_last_week"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "rejected the selector" in result.stderr
    assert "test_renamed_last_week" in result.stderr


def test_the_baseline_reports_how_many_tests_it_ran(repo: Path) -> None:
    """The count is the only thing that makes a silently narrowed selector visible — the recorded
    `-k` battery that selected four of six tests looked exactly like a correct one."""
    result = mutate(str(battery(repo, clamp_mutant(kills="tests/test_pkg.py"))), cwd=repo)

    assert "baseline: 1 test(s) ran and passed" in result.stdout


def test_a_mutant_that_never_terminates_is_errored_rather_than_hanging_the_battery(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A mutant that removes a loop's exit condition would otherwise block forever with itself on
    disk. The bound is derived from the selector's own measured baseline rather than configured, so
    it needs no knob and cannot be set to something meaningless; the two constants are lowered here
    so the test costs a second instead of a minute."""
    module = tool_module()
    monkeypatch.setattr(module, "TIMEOUT_FLOOR_SECONDS", 1.0)
    monkeypatch.setattr(module, "TIMEOUT_FACTOR", 1)

    path = battery(
        repo,
        clamp_mutant(
            name="the marker mutant, which makes the slow test sleep",
            old='MARKER = "original"',
            new='MARKER = "mutated!"',
            kills="tests/test_slow.py::test_clamp_caps_at_the_maximum_slowly",
        ),
    )
    root = module.repo_root(repo)
    results = module.run_battery(root, module.load_battery(path, root))
    _ = capsys.readouterr()

    assert len(results) == 1
    assert results[0].outcome is module.Outcome.ERRORED
    assert results[0].run.timed_out
    assert (repo / "pkg" / "mod.py").read_text(encoding="utf-8") == ORIGINAL_MODULE


# ---------------------------------------------------------------------------------------------
# The battery file, and the command line
# ---------------------------------------------------------------------------------------------


def test_a_malformed_battery_is_a_refusal_not_a_traceback(repo: Path) -> None:
    path = repo / "broken.toml"
    path.write_text("[[mutant]\nfile = ", encoding="utf-8")
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert result.stderr.startswith("mutate: ")


def test_a_battery_that_does_not_exist_is_a_refusal_not_a_traceback(repo: Path) -> None:
    result = mutate(str(repo / "absent.toml"), cwd=repo)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert result.stderr.startswith("mutate: ")


def test_a_battery_with_no_mutants_is_refused(repo: Path) -> None:
    path = repo / "empty.toml"
    path.write_text('pytest = ["true"]\n', encoding="utf-8")
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "no mutants" in result.stderr


def test_a_mutant_missing_a_key_is_refused_naming_the_key(repo: Path) -> None:
    path = repo / "partial.toml"
    path.write_text('[[mutant]]\nfile = "pkg/mod.py"\nold = "a"\n', encoding="utf-8")
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "missing new, kills" in result.stderr


def test_a_target_outside_the_repository_is_refused(repo: Path) -> None:
    """A battery may only mutate the tree it is being run against — `../` is not a mutation."""
    result = mutate(str(battery(repo, clamp_mutant(file="../outside.py"))), cwd=repo)

    assert result.returncode == 1
    assert "outside the repository" in result.stderr


def test_a_target_that_does_not_exist_is_refused(repo: Path) -> None:
    result = mutate(str(battery(repo, clamp_mutant(file="pkg/gone.py"))), cwd=repo)

    assert result.returncode == 1
    assert "no such file" in result.stderr


def test_repo_selects_the_working_tree_to_mutate(tmp_path: Path, repo: Path) -> None:
    """`--repo` decides which files on disk get written to, which makes it the one argument worth
    being sure of. Driven from a directory that is not a git working tree at all, so a default
    would fail rather than quietly succeed against the wrong tree."""
    elsewhere = tmp_path / "not-a-repo"
    elsewhere.mkdir()
    path = battery(repo, clamp_mutant())

    result = mutate(str(path), "--repo", str(repo), cwd=elsewhere)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 killed" in result.stdout
    assert str(repo) in result.stdout


def test_a_repo_that_does_not_exist_is_a_refusal_not_a_traceback(repo: Path) -> None:
    result = mutate(str(battery(repo, clamp_mutant())), "--repo", str(repo / "absent"), cwd=repo)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "not a directory" in result.stderr


def test_a_directory_that_is_not_a_git_working_tree_is_refused(tmp_path: Path, repo: Path) -> None:
    outside = tmp_path / "bare"
    outside.mkdir()
    result = mutate(str(battery(repo, clamp_mutant())), "--repo", str(outside), cwd=repo)

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "not inside a git working tree" in result.stderr
