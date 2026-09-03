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

    `is_symlink` is wrapped too, and the sentence here used to say it was "deliberately not
    wrapped" because it `lstat`s the link rather than the target and "returned `True` on both
    versions in the same measurement". True, and about one symlink whose **parent was readable** —
    see `is_symlink` for what it does when the parent is not.
    """
    return os.path.isfile(path)


def resolves(path: Path) -> bool:
    """`path.exists()` with the version-independence `is_regular_file` explains — read that first.

    False means *this process cannot follow the path to anything*, which is three causes at once:
    it is missing, it is unreadable, or a link loops. Nothing at this level can tell them apart,
    which is why `sync`'s report names all three rather than picking one.
    """
    return os.path.exists(path)


def is_directory(path: Path) -> bool:
    """`path.is_dir()`, with the version-independence `is_regular_file` explains — read that first.

    The same divergence, and it reached a worse place than the crash did. `sync.walk_sources` skips
    a `[sources]` root this answers `False` for, and `pair()` reasons from *absence*, so a root the
    process could not reach retired **every document under it at exit 0**. Measured 20260903 on a
    root symlinked to an in-KB target under a `0o000` ancestor:

    | | 3.13.15 | 3.14.7 |
    |---|---|---|
    | `Path.is_dir` | raise `PermissionError` | `False` |
    | `os.path.isdir` | `False` | `False` |

    So one KB answered two ways: a traceback on the declared floor, and silent data loss on the
    interpreter CI happened to install.

    **`False` here means "not a reachable directory", which is three states, not one** — absent, a
    non-directory, or present and unreachable. `unreadable_directories` is what tells the third
    apart, and any caller that would *delete* on absence has to ask it as well as this.
    """
    return os.path.isdir(path)


def is_symlink(path: Path) -> bool:
    """`path.is_symlink()`, `False` on every Python for a path this process cannot `lstat`.

    `lstat` needs `+x` on the **parent**, not on the link. Under a parent at `0o400` — listable, so
    a glob still yields the entry, but not traversable — `Path.is_symlink()` raises on 3.13 and
    returns `False` on 3.14. Measured 20260903; it ended `pnk sync` in a traceback at the walk's
    own symlink guard, on the interpreter `pyproject.toml` declares as the floor.

    That is the case the note in `is_regular_file` used to exclude by accident: its measurement
    built a symlink in a readable directory, where `is_symlink()` really does agree across
    versions. A predicate is not version-independent because one fixture found it so.
    """
    return os.path.islink(path)


def unreachable(path: Path) -> bool:
    """The filesystem refused to say anything at all about `path`: neither present nor absent.

    `is_regular_file`, `is_directory`, `is_symlink` and `resolves` all answer `False` for a path
    they were not permitted to look at, which is exactly what they answer for a path that is not
    there. For most callers that conflation is harmless. For the one that **deletes on absence** it
    is the whole defect, and this is the question it has to ask instead.

    `lstat`, not `stat`: the question is whether this entry can be seen at all, and following a
    link would answer about its target instead.

    **Only `FileNotFoundError` and `NotADirectoryError` come back `False`.** They are the two honest
    "not there" answers, and a document that is really gone must stay deletable. Every other
    `OSError` is a refusal rather than an absence — `EACCES`, but equally `EIO` on a failing disk
    and `ESTALE` on an NFS mount — and reading a refusal as an absence is how a KB loses documents
    it still has.
    """
    try:
        os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        return False
    except OSError:
        return True
    return False


def unreadable_directories(root: Path) -> frozenset[Path]:
    """Every directory at or under `root` that this process could not list, `root` included.

    **Asked of the filesystem, never inferred from a yield.** An unreadable directory and an empty
    one hand `root.glob(pattern)` the same thing — nothing, silently, identically on 3.13 and 3.14
    — so a caller reasoning from absence turns the first into a deletion. `os.walk`'s `onerror`
    hook is the one instrument that tells them apart: it fires with the `OSError` whose `filename`
    is the directory `scandir` refused, and it fires for `root` itself when `root` is that
    directory.

    **`FileNotFoundError` and `NotADirectoryError` are excluded deliberately**, on the line
    `unreachable` draws for a single path: a root the user deleted *should* retire the documents
    under it, and folding "gone" into "unreadable" would hold rows for a directory that is never
    coming back.

    **A directory that is readable but not traversable is invisible here**, and that is a property
    of the syscall rather than a choice: at `0o400`, `scandir` succeeds, so no error is raised for
    anyone to hook. Its entries then fail to `stat` one at a time, which is `unreachable`'s half of
    the same question — the two are not alternatives, and a caller wanting the whole class needs
    both.

    **Symlinked directories are not followed**, which is `os.walk`'s default and is kept rather
    than inherited: `followlinks=True` does not terminate on a cycle, and a KB may legitimately
    hold `docs/alias -> docs/real`. So an unreadable directory reachable *only* through a symlinked
    ancestor is outside what this collects — narrower than the glob that finds documents through
    one, and said out loud instead of implied.

    **Not `os.access`**: it answers for the calling uid at one instant, it is a check-then-use race,
    and it cannot enumerate. It belongs in a message, never in a walk.
    """
    refused: set[Path] = set()

    def note(error: OSError) -> None:
        if isinstance(error, FileNotFoundError | NotADirectoryError):
            return
        # `filename` is the path `scandir` was refused. An `OSError` raised without one cannot be
        # attributed to a directory, and guessing `root` would name the wrong one on a subtree.
        if error.filename is not None:
            refused.add(Path(error.filename))

    for _directory, _subdirectories, _files in os.walk(root, onerror=note):
        pass
    return frozenset(refused)


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
