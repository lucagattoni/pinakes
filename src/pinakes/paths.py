"""Path predicates more than one caller needs, and that more than one caller got wrong.

Two families live here. **Where a relative path lands**: a `[sources] include` pattern and a
template's declared `files` entry both name something relative that must end up inside a known
directory, and both are read from a file Pinakes does not write —
`manifest._check_include_containment` records four attempts at that test which each got it wrong
differently. **What the filesystem says about a path**: `is_regular_file` and `resolves`, which
exist because the `pathlib` spellings answer differently on the two Python versions this project
supports.

Both families are here for the same reason, stated in this file since the first: a predicate that
several callers need is re-derived wrongly by the next one unless it has a home. The second family
proved it the hard way — the version fix landed as two private helpers in `sync.py`, and the
adversarial review then found the identical crash in `doctor.py` and `linkscan.py`, which could
not reach them.
"""

import os
from pathlib import Path


def is_regular_file(path: Path) -> bool:
    """`path.is_file()`, except that a path this process cannot reach is `False` on every Python.

    `Path.is_file()` and `Path.exists()` swallow a missing target and a symlink loop everywhere,
    but they disagree about `EACCES` across the versions this project supports. Measured 20260903
    on one symlink into a directory with mode `0o000`:

    | | 3.13.15 | 3.14.7 |
    |---|---|---|
    | `Path.is_file`, `Path.exists` | raise `PermissionError` | `False` |
    | `os.path.isfile`, `os.path.exists` | `False` | `False` |

    `pyproject.toml` requires `>=3.13`, so the `pathlib` spelling ended `pnk sync` and `pnk doctor`
    in a raw traceback on the *minimum supported interpreter* — and for `sync`, on exactly the
    shape its walk exists to report. The `os.path` spelling is not a style preference here: it is
    the only one whose result does not depend on which Python is installed.

    It stayed invisible because nothing ran 3.13 where it mattered. A fresh worktree and CI both
    resolve to 3.14, the primary checkout is 3.13, and CI's matrix varied the *extras* rather than
    the interpreter — so a branch gate went green and the merged gate went red on the same tree.
    `.github/workflows/ci.yml` now runs one leg on the declared minimum for that reason.

    **`False` here means "not a reachable regular file", which is three states, not one**: absent,
    a non-file, or present and unreachable. A caller that must tell them apart cannot use this —
    see `doctor`'s orphan check, which asks `os.path.lexists` instead, because calling an
    unreachable document *deleted* offers its permanent id to `--prune`.

    `is_symlink()` is deliberately not wrapped: it `lstat`s the link rather than the target, so it
    returned `True` on both versions in the same measurement.
    """
    return os.path.isfile(path)


def resolves(path: Path) -> bool:
    """`path.exists()` with the version-independence `is_regular_file` explains — read that first.

    False means *this process cannot follow the path to anything*, which is three causes at once:
    it is missing, it is unreadable, or a link loops. Nothing at this level can tell them apart,
    which is why `sync`'s report names all three rather than picking one.
    """
    return os.path.exists(path)


def lands_inside(anchor: Path, base: Path, relative: str) -> bool:
    """Does `relative`, joined onto `base`, land inside `anchor`?

    **The parent is resolved and the final component is not**, which is the whole of it. Three of
    the four recorded failed attempts are here; the fourth — resolving the fixed prefix before the
    first glob component — is about globbing rather than landing and stayed with
    `manifest._check_include_containment`. Each of these fails on a case the callers really meet:

    * **Not "does it contain `..`"** — `../notes/x.md` from `docs/` lands *inside* and is a
      legitimate thing to write. What matters is where the path lands, never whether `..` occurs in
      it. Refusing a valid input is the same defect as accepting an invalid one.
    * **Not "resolve nothing"** — that is purely lexical, and `Path("/kb/../outside/x")` *is*
      relative to `/kb` as a string.
    * **Not "resolve the whole path"** — that follows a final symlink, so a symlinked *document*
      would be refused as an escape while a glob naming the same file is accepted.

    Parent resolved, final component left alone: `..` collapses, a symlinked *ancestor* is caught,
    and a symlinked leaf stays readable.

    **A trailing `..` is the exemption to that**, and it is not a corner case — it is the hole the
    leniency above would otherwise open. `Path("/kb/..").is_relative_to("/kb")` is lexically
    **true**, so leaving that final component unresolved would let it through. It is resolved whole
    instead, which is safe because nothing a caller wants to read or write is *named* `..`.

    **Glob syntax is the caller's to strip before calling.** `**` matches zero or more components
    while `Path.parts` counts it as one, and what that means for a following `..` is a fact about
    globs rather than about landing. `manifest` drops it; a template's `files` entry is literal and
    has nothing to drop.

    `resolve()` raises `OSError` or `ValueError` on paths a TOML string can legally hold — an
    embedded NUL, for one. **That propagates deliberately**: each caller has its own error type and
    its own message, and answering `False` here would report "reaches outside the KB" for something
    that is in fact unreadable, sending the user to fix the wrong thing.
    """
    probe = base.joinpath(*Path(relative).parts)
    landing = probe.resolve() if probe.name == ".." else probe.parent.resolve() / probe.name
    return landing.is_relative_to(anchor)
