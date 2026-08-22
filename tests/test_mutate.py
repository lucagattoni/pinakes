"""`tools/mutate.py` — the CLI as a subprocess, the invalidation in-process.

A subprocess for the reason `tests/test_land.py` gives: it exercises the same artifact a human
runs, argument parsing included, with no `sys.path` surgery. The in-process half exists for the one
property a subprocess cannot observe — whether a `.pyc` existed *during* a mutation — in the sense
`tests/test_deep_reservation.py` uses.

**The assertion that matters is not "it ran a battery".** It is that the harness refuses, or reports
its own brokenness, in each of the ways a mutation run has silently lied here before. A suite that
only drove the happy path would pass with every guard deleted, and the guards *are* the tool: a
broken harness prints SURVIVED and KILLED in the same shape a working one does.

So two rules hold throughout:

* **every refusal asserts the stated reason**, never merely a non-zero exit;
* **every guard has a control that proves it is not ceremony.** The bytecode-invalidation pin
  (`test_the_bytecode_cache_is_cleared_after_the_write_and_after_the_restore`) is followed by
  `test_a_stale_pyc_really_does_report_a_same_length_mutant_as_survived`, which forges the exact
  condition by hand and watches the mutant vanish. If the second ever stops reproducing, the first
  is guarding nothing.

The scratch repository runs `sys.executable -m pytest` rather than the battery's default
`uv run --frozen pytest`: `-m` puts the working directory on `sys.path`, which is how a package
that was never installed becomes importable. That is the battery's `pytest` key doing its job, and
it keeps the nested run to a few hundred milliseconds.
"""

import importlib.util
import os
import struct
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest

TOOL = Path(__file__).parent.parent / "tools" / "mutate.py"

ORIGINAL_MODULE = '''\
"""A scratch module with one pinned assertion, one unpinned function, and a marker."""

MAX = 3
MARKER = "original"


def clamp(value: int) -> int:
    return min(value, MAX)


def describe() -> str:
    return "nothing asserts this"
'''

PINNING_TESTS = """\
from pkg.mod import clamp


def test_clamp_caps_at_the_maximum() -> None:
    assert clamp(10) == MAX_EXPECTED


MAX_EXPECTED = 3
"""

SLOW_TEST = """\
import time

import pkg.mod
from pkg.mod import clamp


def test_clamp_caps_at_the_maximum_slowly() -> None:
    # Fast at baseline, thirty seconds once the marker mutant is in place: that is what gives the
    # kill-it-mid-run test a window it does not have to race for.
    if pkg.mod.MARKER != "original":
        time.sleep(30)
    assert clamp(10) == 3
"""


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def mutate(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed scratch repository: a package, a test that pins one line of it, and a config.

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


# ---------------------------------------------------------------------------------------------
# The two outcomes a battery is allowed to report
# ---------------------------------------------------------------------------------------------


def test_a_mutant_the_tests_catch_is_killed_and_names_the_test_that_caught_it(repo: Path) -> None:
    """KILLED is not "a test failed" — it is *which* test failed, and on what assertion. A row that
    named neither would be satisfied by a selector that is simply red (see the baseline tests)."""
    result = mutate(str(battery(repo, clamp_mutant())), cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "KILLED" in result.stdout
    assert "tests/test_pkg.py::test_clamp_caps_at_the_maximum" in result.stdout
    assert "assert 10 == 3" in result.stdout
    assert "1 killed, 0 survived, 0 errored" in result.stdout


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
    path = battery(
        repo,
        clamp_mutant(name="a mutant that does not parse", new="min(value, MAX"),
    )
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "ERRORED" in result.stdout
    assert "KILLED" not in result.stdout
    assert "SURVIVED" not in result.stdout
    assert "0 killed, 0 survived, 1 errored" in result.stdout
    assert "neither killed nor survived" in result.stderr


# ---------------------------------------------------------------------------------------------
# The anchor
# ---------------------------------------------------------------------------------------------


def test_an_anchor_that_matches_nothing_refuses_before_writing_anything(repo: Path) -> None:
    """`str.replace` that matches nothing returns the string unchanged and reports to no one: the
    file is untouched, every test passes, and the row reads SURVIVED."""
    before = (repo / "pkg" / "mod.py").read_bytes()
    path = battery(repo, clamp_mutant(old="min(value, CEILING)"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "occurs 0 times" in result.stderr
    assert "would read SURVIVED" in result.stderr
    assert "min(value, CEILING)" in result.stderr
    assert (repo / "pkg" / "mod.py").read_bytes() == before


def test_an_anchor_that_matches_twice_refuses_rather_than_choosing(repo: Path) -> None:
    """Two matches mean the battery did not say which line it meant. Replacing both is a different
    mutant from the one that was written down, and replacing the first is a coin toss."""
    path = battery(repo, clamp_mutant(old="value", new="other"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "times" in result.stderr and "exactly once" in result.stderr
    assert "not stated" in result.stderr


def test_a_mutant_whose_old_and_new_are_identical_is_refused(repo: Path) -> None:
    """The file would not change, so the row would read SURVIVED whatever the tests do."""
    result = mutate(str(battery(repo, clamp_mutant(new="min(value, MAX)"))), cwd=repo)

    assert result.returncode == 1
    assert "identical" in result.stderr


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


def test_the_target_is_restored_byte_for_byte_after_a_run(repo: Path) -> None:
    source = repo / "pkg" / "mod.py"
    before = source.read_bytes()

    result = mutate(str(battery(repo, clamp_mutant())), cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert source.read_bytes() == before
    assert git("status", "--porcelain", "--", "pkg/mod.py", cwd=repo) == ""


def test_the_target_is_restored_when_the_run_is_killed_mid_flight(repo: Path) -> None:
    """SIGTERM's default disposition ends the process without unwinding, so a plain `try/finally`
    never runs and the mutant stays on disk — measured, 1 of 1, before the handler existed. SIGINT
    already raises; SIGTERM is the one that needed turning back into an exception."""
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
        process.terminate()
        _, stderr = process.communicate(timeout=60)
    finally:
        if process.poll() is None:  # pragma: no cover — only on a failed run
            process.kill()

    assert source.read_bytes() == before, "SIGTERM left the mutant on disk"
    assert "restored" in stderr


def test_a_run_that_errored_does_not_poison_the_mutants_after_it(repo: Path) -> None:
    """L6: the restore is in a `finally` so that a mutant which blew up cannot leave its edit in
    place for the next one to be measured on top of. Ordering matters here — the invalid mutant
    goes first, and the valid one after it must still be killed on a clean file."""
    path = battery(
        repo,
        clamp_mutant(name="a mutant that does not parse", new="min(value, MAX"),
        clamp_mutant(name="the good one, which must be unaffected"),
    )
    result = mutate(str(path), cwd=repo)

    assert "ERRORED   a mutant that does not parse" in result.stdout
    assert "KILLED    the good one, which must be unaffected" in result.stdout
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

    Asserting the *outcome* of a same-length mutant would not pin this: whether the stale `.pyc`
    is used depends on the write landing in the same wall-clock second as the previous compile,
    which a slower machine would lose. The absence of the file is the same fact with no clock in
    it — and deleting either `clear_pycache` call turns this red.
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


# ---------------------------------------------------------------------------------------------
# The controls the report refuses to run without
# ---------------------------------------------------------------------------------------------


def test_a_batch_with_no_kills_exits_non_zero_as_a_broken_harness(repo: Path) -> None:
    """A run where nothing died is the signature of a harness that is not reaching the code at
    all — an uninstalled package, a stale cache, a selector aimed elsewhere. Reporting it as a
    clean bill is the single most expensive thing this tool could do."""
    path = battery(
        repo,
        clamp_mutant(
            name="nothing asserts the description",
            old="nothing asserts this",
            new="something else entirely",
        ),
    )
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "0 killed, 1 survived" in result.stdout
    assert "nothing died" in result.stderr
    assert "broken harness" in result.stderr


def test_allow_zero_kills_accepts_the_same_batch(repo: Path) -> None:
    """The escape hatch the plan asks for: a deliberate probe of a backstop already documented as
    unpinned. It must change the exit status and nothing else about the report."""
    path = battery(
        repo,
        clamp_mutant(
            name="nothing asserts the description",
            old="nothing asserts this",
            new="something else entirely",
        ),
    )
    result = mutate(str(path), "--allow-zero-kills", cwd=repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 killed, 1 survived" in result.stdout
    assert "nothing died" not in result.stderr


# ---------------------------------------------------------------------------------------------
# The baseline — two ways a battery reports confidently on a question it never asked
# ---------------------------------------------------------------------------------------------


def test_a_selector_whose_tests_all_skip_is_refused_before_anything_is_written(
    repo: Path,
) -> None:
    """Measured while building this, and not in the plan: a skipped test exits 0, byte for byte
    the SURVIVED signal. Pinakes skips on a missing extra as a matter of course (`pdf`, `paid`,
    `model`), so a battery aimed at one of those in a `[light]` checkout would report SURVIVED for
    every mutant in it and read as a clean bill."""
    (repo / "tests" / "test_skipped.py").write_text(
        'import pytest\n\n\n@pytest.mark.skip(reason="needs an extra")\ndef test_skipped() -> None:'
        "\n    assert False\n",
        encoding="utf-8",
    )
    _ = git("add", "-A", cwd=repo)
    _ = git("commit", "-q", "-m", "a test that skips here", cwd=repo)
    before = (repo / "pkg" / "mod.py").read_bytes()

    path = battery(repo, clamp_mutant(kills="tests/test_skipped.py"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "skipped in this checkout" in result.stderr
    assert "would read SURVIVED" in result.stderr
    assert (repo / "pkg" / "mod.py").read_bytes() == before


def test_a_selector_that_is_already_red_is_refused_rather_than_killing_every_mutant(
    repo: Path,
) -> None:
    """The other direction, and the worse one: against a red selector every mutant reads KILLED,
    including the ones nothing catches. The report is then a list of assertions certified as
    pinned by a test that was failing before the run began."""
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


# ---------------------------------------------------------------------------------------------
# The battery file itself
# ---------------------------------------------------------------------------------------------


def test_a_malformed_battery_is_a_refusal_not_a_traceback(repo: Path) -> None:
    path = repo / "broken.toml"
    path.write_text("[[mutant]\nfile = ", encoding="utf-8")
    result = mutate(str(path), cwd=repo)

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
    path = battery(repo, clamp_mutant(file="../outside.py"))
    result = mutate(str(path), cwd=repo)

    assert result.returncode == 1
    assert "outside the repository" in result.stderr


def test_a_target_that_does_not_exist_is_refused(repo: Path) -> None:
    result = mutate(str(battery(repo, clamp_mutant(file="pkg/gone.py"))), cwd=repo)

    assert result.returncode == 1
    assert "no such file" in result.stderr
