"""Every module of the *installed* Pinakes imports, against a freshly-resolved dependency set.

**Why this exists.** `pnk serve` raised `ModuleNotFoundError: No module named
'mcp.server.fastmcp'` on every fresh install from the first PyPI release until this was written
(20260822) — a whole command dead for the entire published life of the project. `pyproject.toml`
said `mcp>=1.28` with no upper bound, `uv.lock` pinned 1.28.1, and all 37 `uv` invocations in
`.github/workflows/ci.yml` *outside the one job that resolves fresh* carry `--frozen` (28
`uv run`, 9 `uv sync`), so **no job in this repository had ever resolved that
dependency**. The one job that does resolve fresh — `build`, through `uv run --isolated
--no-project --with dist/*.whl` — ran `pnk --version`, `pnk init`, two `find_spec` calls and two
data files, and never imported `pinakes.serve`: `grep -c 'pinakes.serve' .github/workflows/ci.yml`
returned 0.

**So a cap was never the fix.** Capping `mcp` below 2.0 closed that day's instance and left the
class open for every other dependency's next major; the cap is gone again as of the port to the
2.x API, and this gate is what remained. It closes the class: it discovers the installed package's
modules by walking its directory tree and imports **every one of them**, so a module added tomorrow
is covered without anyone remembering that this file exists.

**What it cannot see — named rather than implied.**

* **Only import-time breaks.** A dependency that keeps its module layout and changes a signature
  passes this gate and fails at runtime. `anthropic` 1.0.0 and `sentence-transformers` 6.0.0 were
  both measured surface-compatible with what `src/` calls (20260822); neither claim comes from
  here.
* **Nothing imported lazily.** `src/` imports `anthropic` inside `AnthropicTransport` and loads
  both embedding backends through `importlib.import_module`, deliberately, so no walk reaches
  them. `--also-import` names the libraries a given leg should load anyway; the two embedding
  backends stay out of reach, because loading one means downloading a model.
* **Only the install states it is run against.** It knows nothing about `[st]` or `[light]` unless
  a caller installs them.

**Four ways a walk like this reports a pass it did not earn**, each refused here:

* **importing a source tree instead of the install.** The gate would then be evidence about a
  repository, where every dependency comes from `uv.lock`, while its output claimed to be about a
  fresh resolve. Refusing `<this checkout>/src` is not enough: this project mandates a worktree
  per change, so *another* checkout's editable install passes that test — demonstrated by review,
  20260822, with a clean green run over `src/pinakes`. So the check is **positive**: the package
  must live in a `site-packages` or `dist-packages` directory, which is what installing produces
  and what an editable checkout never is. A package with no `__file__` at all is refused rather
  than resolving to the working directory.
* **walking nothing.** `pkgutil` returning an empty iterator reports zero failures, exactly like a
  clean run. `--min-modules` refuses it, and `--require` names the modules that must have been
  reached — `pinakes.serve` above all, since it is the one this gate was written for.
* **an allowance that no longer applies.** `--allow-missing pinakes.extract.pdfium:pypdfium2` on a
  bare wheel is how the one module needing an extra is permitted to fail; if it *does not* fail,
  either the extras moved or the walk stopped detecting missing dependencies. Either way this
  exits non-zero, which is what makes the positive run its own negative check.
* **an allowance that excuses the wrong module.** An allowance naming only the library would
  forgive *any* module failing on it — including `pinakes.serve`, the module the gate exists for,
  had anything on its import chain ever reached `pypdfium2`. Found by review, 20260822, against a
  first version that did exactly that and reported a green run. So an allowance names the
  **module and the library**, and a `--require`d module may never appear in one.

Discovery is `pkgutil.iter_modules` over the package's *paths*, recursively — the filesystem,
never an import. `pkgutil.walk_packages` recurses by importing each subpackage and hands failures
to an `onerror` that defaults to **swallowing them silently**: a broken `__init__.py` would drop
every module beneath it from the walk and report nothing.

Stdlib-only, and it imports nothing from this repository, because it runs inside an isolated
environment that holds the built wheel and its dependencies and nothing else:

    uv run --isolated --no-project --with dist/pinakes-x.y.z-py3-none-any.whl \\
        python tools/wheel_import_gate.py --require pinakes.serve \\
        --allow-missing pinakes.extract.pdfium:pypdfium2
    uv run --isolated --no-project --with \\
        'pinakes[light,pdf,claude] @ file:///abs/dist/pinakes-x.y.z-py3-none-any.whl' \\
        python tools/wheel_import_gate.py --require pinakes.serve --also-import anthropic

`--package` exists for the tests, which point it at a synthetic package rather than at a wheel
this repository would have to build first.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import pkgutil
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_TREE = REPO / "src"
"""This checkout's source tree — named separately only so its refusal can say so. It is **not**
the check: a sibling worktree's `src/` is somebody else's path and passes it."""

INSTALL_DIRECTORIES = ("site-packages", "dist-packages")
"""Where installing a wheel puts a package on the layouts this is actually invoked from — a
virtualenv, `uv`'s isolated environment cache, a Debian interpreter. An editable checkout is in
none of them, which is the whole point: the test is what an install *is*, not what one particular
source tree is."""

DIST_INFO = "*.dist-info"
"""The other half, and the layout-independent one: an installed distribution has a `.dist-info`
directory beside it, wherever it was put. Without this a `pip install --target` — and a zipapp, a
pex, a Lambda layer — was refused as "a source tree", which is a false answer even though no call
site here reaches it (review, 20260822). A checkout has no `.dist-info` beside `src/pinakes`, so
the refusal that matters is unaffected."""

#: The distribution name at the head of a `Requires-Dist` entry — `mcp>=1.28,<2`,
#: `pinakes[pdf]`, `sentence-transformers>=5.0; extra == 'st'`.
DISTRIBUTION = re.compile(r"^([A-Za-z0-9._-]+)")

FAILURE_HEADLINE = "did not import against the resolved dependency set"
"""Printed only when a *module of the walked package* failed. A crash, a missing wheel or `uv`
falling over all produce a non-zero exit too, and none of them prints this."""

PACKAGE_HEADLINE = "is not importable at all"
"""Deliberately **not** `FAILURE_HEADLINE`. A `--with` that installed nothing — a mistyped extra
syntax does exactly that, measured 20260822 — would otherwise print the string CI's negative check
greps for, and a step asserting "the gate can still fail" would be satisfied by an environment
where the gate never ran. Found by review, in the step written to prevent that class."""


def _module_names(package_name: str, paths: list[str]) -> list[str]:
    """Every module under `paths`, found by reading the filesystem rather than by importing."""
    found: list[str] = []
    stack: list[tuple[list[str], str]] = [(paths, package_name)]
    while stack:
        current, prefix = stack.pop()
        for info in pkgutil.iter_modules(current):
            name = f"{prefix}.{info.name}"
            found.append(name)
            if info.ispkg:
                stack.append(([str(Path(path) / info.name) for path in current], name))
    return sorted(found)


def _allowance(value: str) -> tuple[str, str]:
    """Parse `MODULE:LIBRARY`, the only shape an allowance may take.

    Both halves, never the library alone: an allowance keyed on the library forgives every module
    that fails on it, which is how the first version of this gate reported a green run for a
    `pinakes.serve` that had not imported (review, 20260822).
    """
    module, separator, library = value.partition(":")
    if not separator or not module.strip() or not library.strip():
        raise argparse.ArgumentTypeError(
            f"{value!r} is not MODULE:LIBRARY — an allowance names the module permitted to fail "
            f"and the library it may be missing, e.g. pinakes.extract.pdfium:pypdfium2"
        )
    return module.strip(), library.strip()


def _resolved_versions(package_name: str) -> list[str]:
    """What the resolve actually took, per declared dependency — the log's own evidence.

    Read from the *installed* distribution's metadata, so it describes the environment the walk
    ran in and not what `pyproject.toml` in this checkout happens to say.

    `metadata.requires`/`metadata.version` take a **distribution** name and are handed the
    `--package` import name, which coincide for `pinakes` and need not for anything else. This
    output is informational; a mismatch prints nothing rather than reporting anything false.
    """
    try:
        declared = metadata.requires(package_name) or []
    except metadata.PackageNotFoundError:
        return []

    lines: list[str] = []
    for requirement in declared:
        match = DISTRIBUTION.match(requirement)
        if match is None:
            continue
        name = match.group(1)
        if name == package_name:  # `pinakes[pdf]`, the self-referential extra
            continue
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue  # an extra this leg did not install
        line = f"{name} {installed}  (declared {requirement})"
        if line not in lines:
            lines.append(line)
    return sorted(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wheel_import_gate", description=__doc__)
    parser.add_argument(
        "--package",
        default="pinakes",
        help="the installed package to walk (default: pinakes; the tests point this elsewhere)",
    )
    parser.add_argument(
        "--allow-missing",
        action="append",
        default=[],
        type=_allowance,
        metavar="MODULE:LIBRARY",
        help=(
            "one module permitted to fail, and the one library it may be missing — e.g. "
            "pinakes.extract.pdfium:pypdfium2 on a bare wheel. An allowance nothing uses fails "
            "the gate, and a --require'd module may never appear in one"
        ),
    )
    parser.add_argument(
        "--also-import",
        action="append",
        default=[],
        metavar="MODULE",
        help="a library src/ imports lazily, so the walk never reaches it (e.g. anthropic)",
    )
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        metavar="MODULE",
        help="a module the walk must have reached — a walk that found nothing fails no imports",
    )
    parser.add_argument(
        "--min-modules",
        type=int,
        default=20,
        # `%(default)s`, never a typed-out number: the help text and the default are then one
        # value. They were two, and lowering the default to 0 left the help still saying 20 —
        # which is what a test reading `--help` would have believed (battery, 20260822).
        help="fewer modules than this and the walk found nothing to import (default: %(default)s)",
    )
    args = parser.parse_args(argv)
    package_name: str = args.package
    given: list[tuple[str, str]] = args.allow_missing
    repeated = sorted({name for name, _ in given if [n for n, _ in given].count(name) > 1})
    if repeated:
        print(
            f"wheel-import: {', '.join(repeated)} carries more than one --allow-missing. Only the "
            f"last would apply, so the earlier ones could never go stale and could never fail "
            f"this run — an allowance nobody can retire is not an allowance",
            file=sys.stderr,
        )
        return 1
    allowances: dict[str, str] = dict(given)
    also_import: list[str] = args.also_import
    required: list[str] = args.require
    min_modules: int = args.min_modules

    shielded = sorted(set(required) & set(allowances))
    if shielded:
        print(
            f"wheel-import: {', '.join(shielded)} is both --require'd and --allow-missing. A "
            f"module the gate exists to import cannot also be excused from importing",
            file=sys.stderr,
        )
        return 1

    try:
        package = importlib.import_module(package_name)
    except Exception as exc:  # noqa: BLE001 — any import failure is the answer, not a surprise
        print(
            f"wheel-import: {package_name} {PACKAGE_HEADLINE}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    origin = getattr(package, "__file__", None)
    if origin is None:
        print(
            f"wheel-import: {package_name} has no __file__, so this gate cannot tell an installed "
            f"copy from the source tree. It refuses rather than resolving to the working "
            f"directory and reporting a pass it did not earn",
            file=sys.stderr,
        )
        return 1

    location = Path(str(origin)).resolve()
    in_install_directory = bool(set(INSTALL_DIRECTORIES) & set(location.parts))
    beside_dist_info = any(location.parent.parent.glob(DIST_INFO))
    if not (in_install_directory or beside_dist_info):
        where = "the source tree" if location.is_relative_to(SOURCE_TREE) else "an unpacked tree"
        print(
            f"wheel-import: {package_name} resolved to {where} at {location}, which is in no "
            f"{' or '.join(INSTALL_DIRECTORIES)} directory and has no {DIST_INFO} beside it, so "
            f"it is not an installed copy. This gate is only ever evidence about an install, so "
            f"it refuses rather than reporting a pass it did not earn — run it inside "
            f"`uv run --isolated --no-project --with <wheel>`",
            file=sys.stderr,
        )
        return 1

    paths = [str(path) for path in getattr(package, "__path__", [])]
    modules = _module_names(package_name, paths)

    if len(modules) < min_modules:
        print(
            f"wheel-import: found {len(modules)} module(s) under {location.parent}, fewer than "
            f"the {min_modules} required. A walk that finds nothing imports nothing and reports "
            f"no failures, which is indistinguishable from a clean run",
            file=sys.stderr,
        )
        return 1

    unreached = [name for name in required if name not in modules]
    if unreached:
        print(
            f"wheel-import: the walk never reached {', '.join(sorted(unreached))}. Either the "
            f"module was renamed or removed, or the walk is no longer finding it — and an "
            f"unimported module cannot fail",
            file=sys.stderr,
        )
        return 1

    failures: list[str] = []
    used: dict[str, str] = {}

    for name in modules:
        try:
            importlib.import_module(name)
        except ModuleNotFoundError as exc:
            root = (exc.name or "").split(".")[0]
            if allowances.get(name) == root:
                used[name] = root
            else:
                failures.append(f"{name}: ModuleNotFoundError: {exc}")
        except Exception as exc:  # noqa: BLE001 — an import that raises anything is a failure
            failures.append(f"{name}: {type(exc).__name__}: {exc}")

    for name in also_import:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 — same
            failures.append(f"{name} (--also-import): {type(exc).__name__}: {exc}")

    if failures:
        print(
            f"wheel-import: {len(failures)} module(s) {FAILURE_HEADLINE}:\n  "
            + "\n  ".join(failures),
            file=sys.stderr,
        )
        return 1

    unused = sorted(f"{name}:{library}" for name, library in allowances.items() if name not in used)
    if unused:
        print(
            f"wheel-import: --allow-missing named {', '.join(unused)} and it did not fail that "
            f"way. Either the allowance is stale, or this walk has stopped detecting a missing "
            f"dependency — which is the only thing between it and a pass it did not earn",
            file=sys.stderr,
        )
        return 1

    print(f"wheel-import: {len(modules)} module(s) imported from {location.parent}")
    for line in _resolved_versions(package_name):
        print(f"  {line}")
    for name, library in sorted(used.items()):
        print(f"  --allow-missing {name}: no {library}, as declared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
