"""`tools/vacuous_injection_audit.py` — the two properties that make its output quotable.

The audit itself is exercised by running it; what this file pins is narrower and is the half that
fails *silently*. A verdict here can be **a claim about an environment** — the module's own
docstring says a `VACUOUS` row may mean *the real environment does it anyway*, and that such a site
is not rulable from one platform — so a report that cannot name its interpreter and filesystem
cannot state its own limit, and a reader quoting `15 sites · 1 vacuous` a year later has no way to
know which machine produced it.

The second property is the exit status. `mutate.py` exits 0 on a survivor because a survivor is a
finding; this tool exits **non-zero on the unruled set** because `UNSTABLE`, `INCONCLUSIVE` and
*no caller found* mean the instrument did not rule at all. Those are opposite answers to
superficially similar questions, and the reason they differ is the reason both are tested.

In-process, by loading the module by path — `test_mutate.py`'s idiom, which cites
`test_deep_reservation.py` for it. `main()` is driven with `sites` and `probe` replaced, because
the properties under test are about what the *report* says, and a real 15-site run costs 40s to
re-derive facts these fakes state directly.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

TOOL = Path(__file__).parent.parent / "tools" / "vacuous_injection_audit.py"


def tool_module() -> ModuleType:
    """`tools/` is not a package, so the tool is loaded by path."""
    spec = importlib.util.spec_from_file_location("pnk_injection_audit", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["pnk_injection_audit"] = module
    spec.loader.exec_module(module)
    return module


#: A sample injection line as fixture data — **assembled, never written out literally.**
#:
#: The tool's `TARGET` greps every `tests/test_*.py` for `monkeypatch.setattr(Path|os|paths, …)`
#: on a line ending in `)`. Writing one out here as a string literal therefore adds *this file* to
#: the audit's own population, and it did: the run went from 15 sites to **17**, and the probe that
#: neutralised a line inside a string literal broke the file it lived in and came back
#: `INCONCLUSIVE` — turning the whole audit red on a site that does not exist.
#:
#: `test_mutate.py` carries the same warning for a different gate: its fixtures are `dedent`ed
#: because `test_verification.py` scans for `^def (\w+)` and would resolve a test defined only
#: inside a string. **A grep over source lines cannot tell fixture data from code**, and a test
#: file *about* an instrument is exactly where that data lives.
SAMPLE = "monkeypatch." + 'setattr(os, "stat", denied)'
SAMPLE_PATH = "monkeypatch." + 'setattr(Path, "read_bytes", denied)'


def ruling(verdict: str) -> Callable[..., str]:
    """A `probe` that always returns `verdict`, typed so pyright strict can see through it."""

    def probe(*_args: Any, **_kwargs: Any) -> str:
        return verdict

    return probe


def naming(where: str | None) -> Callable[[Path], str | None]:
    """An `environment` that always answers `where` — `None` being the "could not tell" case."""

    def environment(_root: Path) -> str | None:
        return where

    return environment


def drifting(first: str, second: str) -> Callable[[Path], str | None]:
    """An `environment` that answers differently the second time it is asked.

    `main` asks once before the probe loop and once after; this is the shape that says the run
    cannot be attributed to either answer.
    """
    answers = iter((first, second))

    def environment(_root: Path) -> str | None:
        return next(answers)

    return environment


def fake_sites(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    rows: list[tuple[str, int, list[str], str]],
) -> None:
    """Replace site discovery with a fixed list, so `main` reports on exactly these.

    **Through `monkeypatch`, never by assignment.** A bare `module.attr = …` on a module object is
    process-global and is never undone — the first draft of this file set `subprocess.run` that
    way and would have handed every later test in the session a fake. The audit this file tests
    exists to catch instruments that quietly stop measuring; leaving one behind here would have
    been the joke writing itself.
    """

    def sites(_root: Path) -> list[tuple[Path, int, list[str], str]]:
        return [(Path("tests") / name, index, targets, text) for name, index, targets, text in rows]

    monkeypatch.setattr(module, "sites", sites)


# --- the environment line ---------------------------------------------------------------------


def test_the_environment_is_asked_of_the_launcher_not_of_this_process() -> None:
    """The distinction is the whole point, and on this machine the two really do differ.

    The documented invocation is `python3 tools/vacuous_injection_audit.py` — whatever system
    Python is on `PATH` — while every probe runs under `uv run --frozen pytest`, the project venv.
    Measured 20260904 in the row-42 worktree: launcher **3.14.7**, probes **3.13.15**, at the same
    moment. Printing the launcher's own `sys.version` would name a Python that decided nothing
    here, and would read as measured.

    Asserted as a *shape* rather than against a version literal: pinning `3.13` would make this
    test fail the day the floor moves, which is a fact about `pyproject.toml` and not about this
    function. What is pinned is that the answer names a Python, a platform and a `NAME_MAX` — the
    three qualifiers a `VACUOUS` row cannot be read without.
    """
    module = tool_module()
    answer = module.environment(module.ROOT)

    assert answer is not None, "the probe must reach the launcher in a working checkout"
    assert answer.startswith("Python "), answer
    assert "NAME_MAX=" in answer, answer
    # The platform is named, and it is the one this process is actually on.
    assert sys.platform.startswith(("darwin", "linux", "win")), sys.platform


def test_the_probe_runs_the_same_launcher_the_probes_do(monkeypatch: pytest.MonkeyPatch) -> None:
    """One tuple, rewritten — never a second spelling of `uv run --frozen` that can drift.

    A probe command and a report line that disagree about which launcher was used is the failure
    this indirection removes: the line would name an interpreter no test ran under, which is worse
    than naming none.
    """
    module = tool_module()
    seen: list[list[str]] = []

    def spy(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        seen.append(command)
        return subprocess.CompletedProcess(
            command, 0, "Python 9.9.9 on Linux 1 (x86_64), NAME_MAX=255\n", ""
        )

    monkeypatch.setattr(module.subprocess, "run", spy)
    answer = module.environment(module.ROOT)

    assert answer == "Python 9.9.9 on Linux 1 (x86_64), NAME_MAX=255"
    assert len(seen) == 1, seen
    assert seen[0][: len(module.PYTEST) - 1] == list(module.PYTEST[:-1]), (
        f"the probe must reuse PYTEST's launcher, got {seen[0]!r}"
    )
    assert seen[0][len(module.PYTEST) - 1] == "python", seen[0]
    assert "pytest" not in seen[0], "the probe prints an interpreter; it must not run the suite"


def test_an_environment_the_run_cannot_establish_is_said_so_never_guessed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`None` rather than this process's own version — the same stance `mutate.py` takes.

    A failed probe that silently fell back to the launcher would produce the one output that is
    worse than an admission: a confident line naming the wrong Python.
    """
    module = tool_module()

    def refuse(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise OSError("uv is not installed")

    monkeypatch.setattr(module.subprocess, "run", refuse)
    assert module.environment(module.ROOT) is None


def test_a_probe_that_exits_non_zero_is_unknown_not_its_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exit status is checked, not merely that something was printed on stdout."""
    module = tool_module()

    def exited_one(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command, 1, "Python 9.9.9 on Linux 1 (x86_64), NAME_MAX=255\n", "boom"
        )

    monkeypatch.setattr(module.subprocess, "run", exited_one)
    assert module.environment(module.ROOT) is None


def test_the_environment_line_sits_beside_the_counts_not_above_the_table(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`mutate.py`'s stated reason, and it holds here for the same one.

    The counts are what gets pasted into a commit message or a plan row; a qualifier printed above
    the table is the half that gets left behind in the terminal.
    """
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, ["test_a"], SAMPLE)])
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main(["--min-sites", "0"]) == 0
    out = capsys.readouterr().out

    assert "probed under Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255." in out, out
    assert out.index("probed under") > out.index("1 sites"), (
        "the environment belongs with the counts it qualifies, not above the table"
    )


def test_an_unidentifiable_environment_says_the_verdicts_cannot_be_read_without_it(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The admission has to name the consequence, or it reads as a cosmetic omission."""
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, ["test_a"], SAMPLE)])
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(module, "environment", naming(None))

    assert module.main(["--min-sites", "0"]) == 0
    out = capsys.readouterr().out

    assert "could not identify" in out, out
    assert "probed under Python" not in out, "an unknown environment must not read as a known one"


# --- the exit status --------------------------------------------------------------------------


def test_a_vacuous_row_is_reported_and_exits_zero(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A `VACUOUS` row is three findings wearing one label and only one is a defect.

    Failing on it would fail the build on *the real environment does it anyway* — the case row 42
    exists to settle — which is why this exits 0 for the same reason `mutate.py` does on a
    survivor.
    """
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, ["test_a"], SAMPLE)])
    monkeypatch.setattr(module, "probe", ruling("VACUOUS"))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main(["--min-sites", "0"]) == 0
    assert "VACUOUS   test_x.py:1" in capsys.readouterr().out


@pytest.mark.parametrize("verdict", ["UNSTABLE", "INCONCLUSIVE"])
def test_a_site_the_instrument_could_not_rule_exits_non_zero(
    verdict: str, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The instrument failing to rule is the failure; the finding it might have made is not.

    An audit that cannot rule a site while exiting 0 reports success for a measurement that did not
    happen — the "review harness reported success because every agent died" shape.
    """
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, ["test_a"], SAMPLE)])
    monkeypatch.setattr(module, "probe", ruling(verdict))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main(["--min-sites", "0"]) == 1
    assert "NOT RULED test_x.py:1" in capsys.readouterr().out


def test_a_site_with_no_caller_found_exits_non_zero_too(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The third unruled shape, and it never reaches `probe` at all.

    A site whose enclosing `def` resolves to no test is an injection nobody exercises *or* a hole
    in the attribution walk; either way the audit ruled nothing about it, and the count of sites
    would otherwise imply it did.
    """
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, [], SAMPLE)])

    def never(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("a site with no target must not be probed")

    monkeypatch.setattr(module, "probe", never)
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main(["--min-sites", "0"]) == 1
    assert "no caller found" in capsys.readouterr().out


def test_an_all_sound_run_exits_zero(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The control. Without it the two tests above are satisfied by a tool that always exits 1."""
    module = tool_module()
    fake_sites(
        monkeypatch,
        module,
        [
            ("test_x.py", 0, ["test_a"], SAMPLE),
            ("test_y.py", 4, ["test_b"], SAMPLE_PATH),
        ],
    )
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main(["--min-sites", "0"]) == 0
    out = capsys.readouterr().out
    assert "2 sites · 0 vacuous · 0 not ruled" in out, out


# --- `probe`: a skip is not a pass --------------------------------------------------------------


def completed(stdout: str, returncode: int) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["pytest"], returncode, stdout, "")


@pytest.mark.parametrize(
    ("stdout", "returncode", "expected"),
    [
        ("1 skipped in 0.01s", 0, "INCONCLUSIVE"),
        ("8 skipped in 0.04s", 0, "INCONCLUSIVE"),
        ("no tests ran in 0.01s", 5, "INCONCLUSIVE"),
        ("0 passed in 0.01s", 0, "INCONCLUSIVE"),
        ("2 deselected in 0.01s", 0, "INCONCLUSIVE"),
        ("1 passed in 0.05s", 0, "VACUOUS"),
        ("7 passed, 1 skipped in 0.20s", 0, "VACUOUS"),
        ("1 failed in 0.05s", 1, "sound"),
        ("1 failed, 7 passed in 0.30s", 1, "sound"),
    ],
)
def test_a_run_that_passed_nothing_is_never_read_as_a_verdict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    stdout: str,
    returncode: int,
    expected: str,
) -> None:
    """`1 skipped` exits 0 and contains neither `no tests ran` nor `0 passed`.

    The comment at this site already said *"a skipped test also exits 0, and a skip is not a pass"*
    while the code tested for two spellings out of at least four, so an all-skipped selector fell
    through to `VACUOUS` with the exit status agreeing. That is a **false finding**, and it is the
    one direction this tool must not fail in: a `sound` verdict withholds a finding, while a
    `VACUOUS` verdict is what a person then acts on by deleting a fake.

    The three `sound` and `VACUOUS` rows are the controls. Without them the fix is satisfied by a
    function that answers `INCONCLUSIVE` to everything.
    """
    module = tool_module()
    target = tmp_path / "test_x.py"
    target.write_text(SAMPLE + "\n", encoding="utf-8")

    def run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return completed(stdout, returncode)

    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.probe(tmp_path, target, 0, ["test_a"]) == expected


def test_a_real_always_skipped_test_reports_inconclusive_end_to_end(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The control that proves the trap is real, by forging the condition rather than describing it.

    A parametrised table of summary strings is only as good as the strings in it; this runs pytest
    for real against a test that always skips and asserts the tool does not call that a finding.
    Measured 20260904: the summary is `1 skipped in 0.00s`, which the previous check did not match.
    """
    target = tmp_path / "test_skipped.py"
    # Line 0 is a standalone statement because `probe` replaces *that* line with `pass` — the
    # first draft put `import pytest` there, which the probe deleted, and the resulting collection
    # error came back as `sound`. The fixture has to survive its own neutralisation.
    target.write_text(
        "INJECTION = 1  # the line the probe neutralises\n"
        "import pytest\n\n\n"
        '@pytest.mark.skipif(True, reason="stands in for a geteuid()==0 guard")\n'
        "def test_a() -> None:\n"
        "    assert False\n",
        encoding="utf-8",
    )
    module = tool_module()
    # **The real `run`, captured before the fake replaces it.** Calling `subprocess.run` inside the
    # fake would call the fake — the first version of this test recursed until the stack ran out.
    really_run = subprocess.run

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        real = really_run(
            [sys.executable, "-m", "pytest", str(target), "-q", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "skipped" in real.stdout, real.stdout
        return real

    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.probe(tmp_path, target, 0, ["test_a"]) == "INCONCLUSIVE"


# --- the site floor ----------------------------------------------------------------------------


def test_a_collapsed_site_list_is_refused_rather_than_reported_clean(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`0 sites · 0 vacuous · 0 not ruled` and a green exit is the shape to make impossible.

    `TARGET` is a regex over source lines, so a reformat that wraps a `monkeypatch.setattr` across
    two lines is enough to empty the collection — and the report would then certify that nothing
    was measured. `wheel_import_gate.py` carries `--min-modules` for this exact reason.
    """
    module = tool_module()
    fake_sites(monkeypatch, module, [])

    assert module.main([]) == 2
    out = capsys.readouterr().out
    assert "REFUSED" in out, out
    # The refusal *quotes* the summary it is refusing to emit, so asserting that string is absent
    # would be satisfied by nothing. The header is what a real report always prints first, and the
    # refusal returns before reaching it.
    assert "probes each" not in out, "a refusal must not also print a report header"


def test_the_floor_is_a_value_not_a_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--min-modules 1` survived every test in the sibling gate; this is that lesson applied.

    A check that only asserts the flag is present is satisfied by `--min-sites 1`, which restores
    the hole in full. So the floor is asserted by its effect at a realistic value.
    """
    module = tool_module()
    rows = [("test_x.py", i, ["test_a"], SAMPLE) for i in range(9)]
    fake_sites(monkeypatch, module, rows)
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(module, "environment", naming("Python 3.13.15 on Linux, NAME_MAX=255"))

    assert module.main([]) == 2, "nine sites is below the default floor of ten"
    capsys.readouterr()

    # The same nine, with the floor lowered, are reported normally — so the refusal is the floor
    # doing its job and not the tool being unable to handle a short list.
    assert module.main(["--min-sites", "9"]) == 0
    assert "9 sites · 0 vacuous · 0 not ruled" in capsys.readouterr().out


def test_the_floor_can_be_disabled_outright(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--min-sites 0` is the escape hatch, and it must actually report rather than refuse."""
    module = tool_module()
    fake_sites(monkeypatch, module, [])
    monkeypatch.setattr(module, "environment", naming("Python 3.13.15 on Linux, NAME_MAX=255"))

    assert module.main(["--min-sites", "0"]) == 0
    assert "0 sites · 0 vacuous · 0 not ruled" in capsys.readouterr().out


def test_this_file_does_not_add_itself_to_the_audits_own_population() -> None:
    """A test file *about* injections is where injection-shaped fixture data lives.

    `TARGET` greps every `tests/test_*.py` for `monkeypatch.setattr(Path|os|paths, …)` on a line
    ending in `)`. When this file wrote those out as string literals it joined the population it
    was testing: the run went 15 sites -> **17**, and probing a "site" inside a string literal
    broke the file it lived in and returned `INCONCLUSIVE`, turning the whole audit red over a site
    that does not exist. Measured 20260904 10:19 UTC — read off the run's own artefact, because
    the first version of this sentence carried a time that had not happened yet.

    The guard is here rather than in the tool because **the tool's blind spot is real and is not
    this increment's to close**: a regex over source lines cannot tell fixture data from code, and
    the parse-not-grep question already belongs to an open, planner-owned row. What this pins is
    that *this file* stays out of the way — the same stance `test_mutate.py` takes towards
    `test_verification.py`'s `^def (\\w+)` scan, and for the same reason.
    """
    module = tool_module()
    mine = Path(__file__).name
    offenders = [
        f"{path.name}:{index + 1}  {text}"
        for path, index, _targets, text in module.sites(module.ROOT)
        if path.name == mine
    ]

    assert not offenders, (
        "this file has re-entered the audit's own population — assemble the literal "
        f"(see SAMPLE) rather than writing it out: {offenders}"
    )


# --- the environment must hold still for the verdicts to mean anything --------------------------


def test_the_environment_is_read_before_the_probes_not_after_them(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The line beside the counts must describe the run that produced them.

    Asking at the end reports the environment the run *finished* in. On 20260904 at 10:23/10:24 UTC
    this worktree's venv answered 3.13.15 to the audit and 3.14.7 to the very next command, in the
    same directory with no `uv sync` between them — so "afterwards" is a different question from
    "during", and only one of them qualifies a verdict.
    """
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, ["test_a"], SAMPLE)])
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(module, "environment", drifting("BEFORE-3.13", "AFTER-3.14"))

    module.main(["--min-sites", "0"])
    out = capsys.readouterr().out

    assert "probed under BEFORE-3.13." in out, out
    assert "probed under AFTER-3.14." not in out, (
        "the report must not name the environment it ended in"
    )


def test_an_environment_that_moved_mid_run_makes_every_verdict_unattributable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Not "this site could not be ruled" but "none of them is about anything in particular".

    Both readings are printed rather than a bare mismatch flag, because the two values *are* the
    finding — a reader needs to know which two environments were in play to decide what to re-run.
    """
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, ["test_a"], SAMPLE)])
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(module, "environment", drifting("BEFORE-3.13", "AFTER-3.14"))

    assert module.main(["--min-sites", "0"]) == 1
    out = capsys.readouterr().out
    assert "UNATTRIBUTABLE" in out, out
    assert "BEFORE-3.13" in out and "AFTER-3.14" in out, "both readings are the finding"


def test_a_stable_environment_is_not_reported_as_drift(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The control. Without it the guard is satisfied by one that fires on every run."""
    module = tool_module()
    fake_sites(monkeypatch, module, [("test_x.py", 0, ["test_a"], SAMPLE)])
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(module, "environment", drifting("SAME", "SAME"))

    assert module.main(["--min-sites", "0"]) == 0
    assert "UNATTRIBUTABLE" not in capsys.readouterr().out
