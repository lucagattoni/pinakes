"""`tools/wheel_import_gate.py`, driven as a subprocess — one test per branch.

A subprocess rather than an import, for the reason `tests/test_status_header_gate.py` gives: it
exercises the same artifact CI runs, argument parsing included, with no `sys.path` surgery. Every
branch but one drives a **synthetic** package on `PYTHONPATH`, so the tests need no wheel and no
network; `--package` exists for exactly that.

**What these tests are and are not.** They pin the gate's own logic. They say nothing about
whether `pnk serve` works on a fresh resolve — that question cannot be asked from inside a
`--frozen` pytest run, because the environment it runs in *is* the lockfile. The only thing that
can answer it is CI's `build` job, which resolves fresh; these tests exist so that when it runs,
the gate it runs is not lying. `test_the_real_package_is_refused_from_the_source_tree` is the one
exception and the reason the distinction is worth stating: in this checkout `pinakes` resolves to
`src/`, so the gate refuses — proving the refusal that stops a green run from being evidence about
the repository instead of about an install.
"""

import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).parent.parent / "tools" / "wheel_import_gate.py"

FAILURE_HEADLINE = "did not import against the resolved dependency set"
"""Duplicated from the tool on purpose: an assertion importing the constant it checks would pass
whatever the constant said, and CI's negative check greps this string literally."""

PACKAGE_HEADLINE = "is not importable at all"
"""And this one must stay *different* from the line above. They were the same string until review
found that an environment where `--with` installed nothing printed the phrase CI's "the gate can
still fail" step greps for — so that step would have been satisfied by a run in which the gate
never executed."""


def installed(root: Path) -> Path:
    """The directory synthetic packages are written to.

    Named `site-packages` because the gate refuses a package that is in no `site-packages` or
    `dist-packages` directory — the positive test for "this is an install". A fixture living
    anywhere else would be refused before any branch under test was reached, so the fixture has to
    look like an install; `test_a_package_outside_site_packages_is_refused` is the same fact from
    the other side.
    """
    path = root / "site-packages"
    path.mkdir(exist_ok=True)
    return path


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the gate with `root/site-packages` on `PYTHONPATH`."""
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(installed(root))},
    )


def build_package(root: Path, name: str, modules: dict[str, str]) -> None:
    """Write a package whose modules have exactly the bodies given.

    `modules` maps a dotted name *relative to the package* onto its source; a key ending in
    `.__init__` writes a subpackage's `__init__.py`.
    """
    package = installed(root) / name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    for relative, source in modules.items():
        parts = relative.split(".")
        directory = package.joinpath(*parts[:-1])
        directory.mkdir(parents=True, exist_ok=True)
        for depth in range(1, len(parts)):
            initialiser = package.joinpath(*parts[:depth]) / "__init__.py"
            if not initialiser.exists():
                initialiser.write_text("", encoding="utf-8")
        (directory / f"{parts[-1]}.py").write_text(source, encoding="utf-8")


def clean_package(root: Path, name: str = "synthkit", count: int = 4) -> None:
    build_package(root, name, {f"mod{index}": "value = 1\n" for index in range(count)})


def test_a_package_whose_modules_all_import_passes(tmp_path: Path) -> None:
    clean_package(tmp_path)
    result = run(tmp_path, "--package", "synthkit", "--min-modules", "4")
    assert result.returncode == 0, result.stderr
    assert "4 module(s) imported" in result.stdout


def test_a_module_that_raises_on_import_fails_naming_it(tmp_path: Path) -> None:
    """Not only `ModuleNotFoundError`: a module whose body raises anything at all is a module a
    user's `pnk` command cannot reach."""
    build_package(tmp_path, "brokenkit", {"boom": "raise RuntimeError('module scope blew up')\n"})
    result = run(tmp_path, "--package", "brokenkit", "--min-modules", "1")
    assert result.returncode == 1
    assert FAILURE_HEADLINE in result.stderr
    assert "brokenkit.boom" in result.stderr, "the failure must name the module to fix"
    assert "RuntimeError" in result.stderr, "and what it raised"


def test_a_missing_dependency_fails_by_default(tmp_path: Path) -> None:
    """The defect this gate was written for, in miniature: a module importing something that is
    not installed. Unnamed, it must fail — that is what `pnk serve` needed CI to do."""
    build_package(tmp_path, "needykit", {"uses_absent": "import definitely_not_installed_xyz\n"})
    result = run(tmp_path, "--package", "needykit", "--min-modules", "1")
    assert result.returncode == 1
    assert FAILURE_HEADLINE in result.stderr
    assert "needykit.uses_absent" in result.stderr
    assert "definitely_not_installed_xyz" in result.stderr


def test_an_expected_missing_dependency_is_permitted_and_reported(tmp_path: Path) -> None:
    """`pinakes.extract.pdfium` on a bare wheel. Permitted, never silent: the run says which
    modules the allowance covered, so a growing list is visible rather than absorbed."""
    build_package(
        tmp_path,
        "extraskit",
        {"a": "value = 1\n", "b": "value = 2\n", "needs_extra": "import absent_extra_xyz\n"},
    )
    result = run(
        tmp_path,
        "--package",
        "extraskit",
        "--min-modules",
        "3",
        "--allow-missing",
        "extraskit.needs_extra:absent_extra_xyz",
    )
    assert result.returncode == 0, result.stderr
    assert "extraskit.needs_extra: no absent_extra_xyz, as declared" in result.stdout


def test_an_allowance_nothing_uses_fails(tmp_path: Path) -> None:
    """The gate's own negative check, and the reason CI's positive run is self-proving: if the
    walk ever stops seeing a missing dependency, the allowance goes unused and this fires. A gate
    that quietly imported nothing would otherwise report a clean pass."""
    clean_package(tmp_path)
    result = run(
        tmp_path,
        "--package",
        "synthkit",
        "--min-modules",
        "4",
        "--allow-missing",
        "synthkit.mod0:unused_xyz",
    )
    assert result.returncode == 1
    assert "synthkit.mod0:unused_xyz" in result.stderr
    assert "stale" in result.stderr


def test_a_missing_dependency_is_only_permitted_for_the_module_that_names_it(
    tmp_path: Path,
) -> None:
    """An allowance is per *library*, never a blanket. A second module failing on something else
    still fails, so `--allow-missing pypdfium2` cannot absorb an `mcp` break."""
    build_package(
        tmp_path,
        "mixedkit",
        {
            "needs_extra": "import absent_extra_xyz\n",
            "needs_core": "import absent_core_xyz\n",
            "fine": "value = 1\n",
        },
    )
    result = run(
        tmp_path,
        "--package",
        "mixedkit",
        "--min-modules",
        "3",
        "--allow-missing",
        "mixedkit.needs_extra:absent_extra_xyz",
    )
    assert result.returncode == 1
    assert "mixedkit.needs_core" in result.stderr
    assert "mixedkit.needs_extra" not in result.stderr, "the permitted one must not be reported"


def test_a_broken_subpackage_does_not_hide_the_modules_beneath_it(tmp_path: Path) -> None:
    """Why discovery reads the filesystem instead of using `pkgutil.walk_packages`.

    `walk_packages` recurses by *importing* each subpackage and hands the failure to an `onerror`
    that defaults to swallowing it, so a broken `__init__.py` drops every module below it from the
    walk and reports nothing about them. Here `deep/__init__.py` raises and `deep/leaf.py` is
    perfectly good; both must appear, because a walk that silently stopped at `deep` is the shape
    of a gate reporting a pass it did not earn.
    """
    build_package(
        tmp_path,
        "nestedkit",
        {
            "top": "value = 1\n",
            "deep.__init__": "raise RuntimeError('package scope blew up')\n",
            "deep.leaf": "value = 2\n",
        },
    )
    # `deep.__init__` above lands as `deep/__init__.py` only if written as a module named
    # `__init__`; assert the fixture really did that before reading anything into the result.
    assert (
        (installed(tmp_path) / "nestedkit" / "deep" / "__init__.py")
        .read_text(encoding="utf-8")
        .startswith("raise")
    )
    result = run(tmp_path, "--package", "nestedkit", "--min-modules", "3")
    assert result.returncode == 1
    assert "nestedkit.deep:" in result.stderr
    assert "nestedkit.deep.leaf" in result.stderr, (
        "the module below the broken package was never reached — the walk stops where it should "
        "not, which is exactly what walk_packages would have done silently"
    )


def test_a_walk_that_finds_too_little_fails(tmp_path: Path) -> None:
    """A walk that finds nothing imports nothing and reports no failures — byte for byte the
    signal of a clean run. `--min-modules` is what tells the two apart."""
    clean_package(tmp_path, count=2)
    result = run(tmp_path, "--package", "synthkit", "--min-modules", "20")
    assert result.returncode == 1
    assert "fewer than the 20 required" in result.stderr


def test_a_required_module_the_walk_never_reached_fails(tmp_path: Path) -> None:
    """`--require pinakes.serve` in CI. A module that is no longer found cannot fail to import,
    so its silence has to be an error rather than a pass."""
    clean_package(tmp_path)
    result = run(
        tmp_path, "--package", "synthkit", "--min-modules", "4", "--require", "synthkit.serve"
    )
    assert result.returncode == 1
    assert "never reached synthkit.serve" in result.stderr


def test_a_required_module_the_walk_did_reach_passes(tmp_path: Path) -> None:
    """The other half: `--require` must be satisfiable, or the branch above proves nothing."""
    build_package(tmp_path, "servekit", {"serve": "value = 1\n", "other": "value = 2\n"})
    result = run(
        tmp_path, "--package", "servekit", "--min-modules", "2", "--require", "servekit.serve"
    )
    assert result.returncode == 0, result.stderr


def test_also_import_fails_when_the_named_library_is_absent(tmp_path: Path) -> None:
    """`--also-import anthropic` covers what `src/` imports lazily, which no walk reaches. It has
    to be able to fail, or naming it there is decoration."""
    clean_package(tmp_path)
    result = run(
        tmp_path,
        "--package",
        "synthkit",
        "--min-modules",
        "4",
        "--also-import",
        "absent_lazy_xyz",
    )
    assert result.returncode == 1
    assert FAILURE_HEADLINE in result.stderr
    assert "absent_lazy_xyz (--also-import)" in result.stderr


def test_a_package_that_does_not_exist_at_all_fails(tmp_path: Path) -> None:
    """`--with <wheel>` silently installing nothing, which is what a mistyped extra syntax does:
    measured 20260822, `--with 'dist/x.whl[pdf,claude]'` installed no pinakes at all and the gate
    said so rather than walking zero modules and passing."""
    result = run(tmp_path, "--package", "not_installed_at_all_xyz")
    assert result.returncode == 1
    assert PACKAGE_HEADLINE in result.stderr
    assert FAILURE_HEADLINE not in result.stderr, (
        "this must not print the phrase CI's negative check greps for: an environment where "
        "--with installed nothing would then satisfy a step asserting the gate can still fail"
    )


def test_the_real_package_is_refused_from_the_source_tree() -> None:
    """In this checkout `pinakes` is installed from `src/`, so the gate must refuse.

    This is the branch that keeps a green run meaning what it says. Run against the source tree
    the gate would be evidence about the repository — where every dependency comes from
    `uv.lock` — while its output claimed to be about an install resolved fresh.
    """
    result = subprocess.run(
        [sys.executable, str(TOOL)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 1
    assert "resolved to the source tree" in result.stderr
    assert "src/pinakes" in result.stderr.replace("\\", "/")


def test_an_allowance_cannot_excuse_a_module_failing_on_a_different_library(
    tmp_path: Path,
) -> None:
    """An allowance is `MODULE:LIBRARY`, and both halves bind.

    The first version of this gate keyed allowances on the **library** alone. That forgives any
    module failing on it, so a `--require`d module was excused and the run went green — reproduced
    by review, 20260822, with a `serve` module importing the permitted library. Here the allowance
    names a different library from the one that is actually missing, and must not apply.
    """
    build_package(
        tmp_path,
        "scopedkit",
        {"a": "value = 1\n", "b": "value = 2\n", "needs_extra": "import absent_extra_xyz\n"},
    )
    result = run(
        tmp_path,
        "--package",
        "scopedkit",
        "--min-modules",
        "3",
        "--allow-missing",
        "scopedkit.needs_extra:some_other_library_xyz",
    )
    assert result.returncode == 1
    assert "scopedkit.needs_extra" in result.stderr
    assert "absent_extra_xyz" in result.stderr


def test_a_required_module_may_not_also_be_allowed_to_fail(tmp_path: Path) -> None:
    """The refusal that makes `--require pinakes.serve` mean what it says.

    `--require` asserts the walk *reached* a module, which is a claim about discovery and not
    about importing — so without this, an allowance covering that same module would let it fail
    while the gate reported a clean run. Refused before anything is imported, because the two
    flags contradict each other whatever the wheel contains.
    """
    build_package(tmp_path, "guardkit", {"serve": "import absent_extra_xyz\n", "b": "value = 1\n"})
    result = run(
        tmp_path,
        "--package",
        "guardkit",
        "--min-modules",
        "2",
        "--require",
        "guardkit.serve",
        "--allow-missing",
        "guardkit.serve:absent_extra_xyz",
    )
    assert result.returncode == 1
    assert "guardkit.serve" in result.stderr
    assert "cannot also be excused" in result.stderr


def test_an_allowance_that_is_not_module_colon_library_is_refused(tmp_path: Path) -> None:
    """The old spelling — a bare library name — must not be silently accepted as a module name,
    which would make every allowance stale and every run red for the wrong reason."""
    clean_package(tmp_path)
    result = run(tmp_path, "--package", "synthkit", "--allow-missing", "pypdfium2")
    assert result.returncode == 2, "argparse rejects it before anything is imported"
    assert "MODULE:LIBRARY" in result.stderr


def test_an_allowance_covers_only_the_module_it_names_even_for_the_same_library(
    tmp_path: Path,
) -> None:
    """The other half of the scoping, and the half the first round of tests missed.

    `test_an_allowance_cannot_excuse_a_module_failing_on_a_different_library` varies the
    *library*, so a gate that had gone back to matching on the library alone still passed it — the
    mutation battery found that by surviving. This varies the **module**: two of them fail on the
    same absent library, one is named, and the other must still fail. That is the real shape of
    the defect review caught, where `pinakes.serve` would have been excused by an allowance
    written for `pinakes.extract.pdfium`.
    """
    build_package(
        tmp_path,
        "twinkit",
        {
            "declared": "import absent_shared_xyz\n",
            "undeclared": "import absent_shared_xyz\n",
            "fine": "value = 1\n",
        },
    )
    result = run(
        tmp_path,
        "--package",
        "twinkit",
        "--min-modules",
        "3",
        "--allow-missing",
        "twinkit.declared:absent_shared_xyz",
    )
    assert result.returncode == 1
    assert "twinkit.undeclared" in result.stderr, (
        "a second module failing on the same library was excused by an allowance written for the "
        "first — the allowance is matching on the library, not on the module"
    )
    assert "twinkit.declared:" not in result.stderr, "the declared one must not be reported"


def test_a_package_with_no_file_is_refused_rather_than_resolved_to_the_cwd(
    tmp_path: Path,
) -> None:
    """A namespace package — a directory with no `__init__.py` — has `__file__ is None`.

    Without an explicit refusal the location falls back to the working directory, which is neither
    under `src/` nor anywhere near the install, so the source-tree check silently passes and the
    run reports on a package whose provenance the gate never established. The real `pinakes` has a
    `__file__`, so nothing else here can reach this branch: found by the mutation battery, where
    deleting the refusal survived every other test.
    """
    namespace = installed(tmp_path) / "nskit"
    namespace.mkdir()
    (namespace / "mod.py").write_text("value = 1\n", encoding="utf-8")
    assert not (namespace / "__init__.py").exists(), "the fixture must be a namespace package"

    result = run(tmp_path, "--package", "nskit", "--min-modules", "1")
    assert result.returncode == 1
    assert "no __file__" in result.stderr
    assert "working directory" in result.stderr


def test_a_package_outside_site_packages_is_refused(tmp_path: Path) -> None:
    """Any source tree, not only this checkout's.

    Refusing `<this checkout>/src` is what the gate did first, and it is not enough: this project
    mandates a worktree per change, so another checkout's editable install sits at a path this one
    has never heard of. Review demonstrated it — one checkout's interpreter, another checkout's
    gate, a clean green run over `src/pinakes` (20260822). The check is now positive: an installed
    package lives in a `site-packages` or `dist-packages` directory, and a checkout never does.
    """
    outside = tmp_path / "not-an-install"
    outside.mkdir()
    package = outside / "loosekit"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    for index in range(4):
        (package / f"mod{index}.py").write_text("value = 1\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(TOOL), "--package", "loosekit", "--min-modules", "4"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(outside)},
    )
    assert result.returncode == 1
    assert "site-packages" in result.stderr
    assert "not an installed copy" in result.stderr


def test_one_module_may_carry_only_one_allowance(tmp_path: Path) -> None:
    """Two allowances for the same module: only the last could ever apply, so the first can never
    go stale and can never fail the run — an allowance nobody can retire is not an allowance, and
    it is a silent way to park a module the gate has stopped checking."""
    build_package(tmp_path, "dupkit", {"a": "import absent_one_xyz\n", "b": "value = 1\n"})
    result = run(
        tmp_path,
        "--package",
        "dupkit",
        "--min-modules",
        "2",
        "--allow-missing",
        "dupkit.a:absent_stale_xyz",
        "--allow-missing",
        "dupkit.a:absent_one_xyz",
    )
    assert result.returncode == 1
    assert "dupkit.a" in result.stderr
    assert "more than one --allow-missing" in result.stderr
