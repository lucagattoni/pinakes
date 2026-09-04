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
    fake_sites(
        monkeypatch, module, [("test_x.py", 0, ["test_a"], 'monkeypatch.setattr(os, "stat", f)')]
    )
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main([]) == 0
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
    fake_sites(
        monkeypatch, module, [("test_x.py", 0, ["test_a"], 'monkeypatch.setattr(os, "stat", f)')]
    )
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(module, "environment", naming(None))

    assert module.main([]) == 0
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
    fake_sites(
        monkeypatch, module, [("test_x.py", 0, ["test_a"], 'monkeypatch.setattr(os, "stat", f)')]
    )
    monkeypatch.setattr(module, "probe", ruling("VACUOUS"))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main([]) == 0
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
    fake_sites(
        monkeypatch, module, [("test_x.py", 0, ["test_a"], 'monkeypatch.setattr(os, "stat", f)')]
    )
    monkeypatch.setattr(module, "probe", ruling(verdict))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main([]) == 1
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
    fake_sites(monkeypatch, module, [("test_x.py", 0, [], 'monkeypatch.setattr(os, "stat", f)')])

    def never(*_args: Any, **_kwargs: Any) -> str:
        raise AssertionError("a site with no target must not be probed")

    monkeypatch.setattr(module, "probe", never)
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main([]) == 1
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
            ("test_x.py", 0, ["test_a"], 'monkeypatch.setattr(os, "stat", f)'),
            ("test_y.py", 4, ["test_b"], 'monkeypatch.setattr(Path, "read_bytes", g)'),
        ],
    )
    monkeypatch.setattr(module, "probe", ruling("sound"))
    monkeypatch.setattr(
        module, "environment", naming("Python 3.13.15 on Linux 6.8 (x86_64), NAME_MAX=255")
    )

    assert module.main([]) == 0
    out = capsys.readouterr().out
    assert "2 sites · 0 vacuous · 0 not ruled" in out, out
