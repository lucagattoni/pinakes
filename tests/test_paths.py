"""`paths` — the predicates several callers share, tested where they live.

Two families, and the file is organised as they are. **Where a relative path lands**:
`lands_inside`, whose extraction is asserted to be behaviour-preserving by the *existing*
`[sources] include` containment tests (`tests/test_sync.py`, `tests/test_manifest.py`); these are
the other half, the predicate's own cases stated once rather than inferred from a manifest error
message. **What the filesystem says about a path**: the predicates that exist because `pathlib`
answers differently on the two interpreters this project supports, and because "I was not allowed
to look" and "it is not there" are the same `False` everywhere else.

Every test in the second family builds its state with `chmod`, which root ignores — hence the
`geteuid` guards. Injection is this repository's default and cannot be used here: what is under
test *is* which syscall raises on which interpreter, and a fake that raises on command would assert
the fixture rather than the platform.
"""

import os
from pathlib import Path

import pytest

from pinakes.paths import (
    is_directory,
    is_symlink,
    lands_inside,
    unreachable,
    unreachable_through_links,
    unreadable_directories,
)

needs_a_non_root_user = pytest.mark.skipif(
    os.geteuid() == 0, reason="root traverses a 0o000 directory, so the state cannot be built"
)


def test_a_dot_dot_that_stays_inside_is_accepted(tmp_path: Path) -> None:
    """Refusing a valid input is the same defect as accepting an invalid one.

    `../notes/x.md` from `docs/` lands inside the KB and is a legitimate thing to write, which is
    why the predicate measures where a path lands and never whether `..` occurs in it.
    """
    anchor = tmp_path.resolve()
    (tmp_path / "docs").mkdir()
    (tmp_path / "notes").mkdir()

    assert lands_inside(anchor, tmp_path / "docs", "../notes/x.md")


def test_a_dot_dot_that_walks_out_is_refused(tmp_path: Path) -> None:
    anchor = (tmp_path / "kb").resolve()
    (tmp_path / "kb").mkdir()

    assert not lands_inside(anchor, tmp_path / "kb", "../../evil.md")


def test_a_symlinked_leaf_stays_readable(tmp_path: Path) -> None:
    """Resolving the *whole* path would refuse this, and it is a file the caller must be able to
    reach: a document inside the KB that happens to be a symlink is still a document inside the KB.
    """
    anchor = (tmp_path / "kb").resolve()
    (tmp_path / "kb").mkdir()
    (tmp_path / "elsewhere.md").write_text("target\n", encoding="utf-8")
    (tmp_path / "kb" / "alpha.md").symlink_to(tmp_path / "elsewhere.md")

    assert lands_inside(anchor, tmp_path / "kb", "alpha.md")


def test_a_symlinked_ancestor_is_caught(tmp_path: Path) -> None:
    """The counterpart to the case above, and why the *parent* is resolved even though the leaf is
    not. The escape here exists only on disk — no `..`, no absolute path, nothing lexical to see.
    """
    anchor = (tmp_path / "kb").resolve()
    (tmp_path / "kb").mkdir()
    (tmp_path / "outside").mkdir()
    (tmp_path / "kb" / "escape").symlink_to(tmp_path / "outside", target_is_directory=True)

    assert not lands_inside(anchor, tmp_path / "kb", "escape/evil.md")


def test_a_trailing_dot_dot_is_refused(tmp_path: Path) -> None:
    """The exemption, and the hole it closes.

    `Path("/kb/..").is_relative_to("/kb")` is lexically **true**, so leaving the final component
    unresolved — which is what keeps a symlinked leaf readable — would let a trailing `..` escape
    through that same leniency. Nothing a caller wants is *named* `..`, so it is resolved whole.
    """
    anchor = (tmp_path / "kb").resolve()
    (tmp_path / "kb").mkdir()

    assert not lands_inside(anchor, tmp_path / "kb", "..")


def test_an_embedded_nul_raises_rather_than_answering_false(tmp_path: Path) -> None:
    """`resolve()` raises on paths a TOML string can legally hold, and that propagates.

    Answering `False` would report "reaches outside the KB" for something that is in fact
    unreadable, sending the user to fix the wrong thing. Each caller wraps it in its own error.
    """
    anchor = tmp_path.resolve()

    with pytest.raises((ValueError, OSError)):
        lands_inside(anchor, tmp_path, "a\x00b/x.md")


# ---------------------------------------------------------------------------------------------
# What the filesystem says about a path
# ---------------------------------------------------------------------------------------------


def test_is_directory_agrees_with_pathlib_on_an_ordinary_tree(tmp_path: Path) -> None:
    """The control, and it is not decorative: every test below asserts a `False`, and a predicate
    that answered `False` unconditionally would pass all of them."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("x\n", encoding="utf-8")

    assert is_directory(tmp_path / "docs")
    assert not is_directory(tmp_path / "docs" / "note.md")
    assert not is_directory(tmp_path / "gone")


@needs_a_non_root_user
def test_is_directory_answers_false_rather_than_raising_behind_a_blocked_ancestor(
    tmp_path: Path,
) -> None:
    """`Path.is_dir()` raises `PermissionError` here on 3.13 and returns `False` on 3.14.

    This is the divergence that ended `pnk sync` in a traceback on the *declared minimum*
    interpreter while losing documents silently on the one CI installed. The assertion is that one
    answer comes back on both, and the `pathlib` half is asserted beside it so the test still says
    what it is *about* on the version where the two happen to agree.
    """
    blocked = tmp_path / "blocked"
    (blocked / "realdocs").mkdir(parents=True)
    os.chmod(blocked, 0o000)
    try:
        assert not is_directory(blocked / "realdocs")
    finally:
        os.chmod(blocked, 0o755)


@needs_a_non_root_user
def test_is_symlink_answers_false_rather_than_raising_under_an_untraversable_parent(
    tmp_path: Path,
) -> None:
    """`lstat` needs `+x` on the **parent**, which is what the note this replaced did not test.

    At `0o400` the directory lists — so a glob still yields the entry — and cannot be traversed, so
    `Path.is_symlink()` raises on 3.13. The earlier measurement built its symlink in a readable
    directory, where the two versions really do agree, and concluded the predicate was
    version-independent.
    """
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "note.md").write_text("x\n", encoding="utf-8")
    os.chmod(locked, 0o400)
    try:
        assert not is_symlink(locked / "note.md")
    finally:
        os.chmod(locked, 0o755)


def test_is_symlink_still_recognises_a_link_it_can_stat(tmp_path: Path) -> None:
    """The control for the one above: `False` for everything would satisfy it alone."""
    (tmp_path / "real.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "alias.md").symlink_to(tmp_path / "real.md")

    assert is_symlink(tmp_path / "alias.md")
    assert not is_symlink(tmp_path / "real.md")


def test_unreachable_is_false_for_a_path_that_is_simply_not_there(tmp_path: Path) -> None:
    """**The load-bearing control.** A document that is genuinely deleted must stay deletable, so
    the one thing this predicate must never do is call an absence a refusal."""
    assert not unreachable(tmp_path / "gone.md")
    assert not unreachable(tmp_path / "gone" / "deeper.md")


def test_unreachable_is_false_for_a_path_that_is_plainly_there(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("x\n", encoding="utf-8")

    assert not unreachable(tmp_path / "note.md")


def test_unreachable_is_false_for_a_dangling_symlink(tmp_path: Path) -> None:
    """`lstat` sees the link itself, so a dangling one is *reachable* and merely unresolvable.

    The distinction matters at the one call site: a dangling link is reported, and a path nobody
    may look at holds a document. Conflating them would report the wrong thing for both.
    """
    (tmp_path / "dangling.md").symlink_to(tmp_path / "nowhere.md")

    assert not unreachable(tmp_path / "dangling.md")


@needs_a_non_root_user
def test_unreachable_is_true_for_an_entry_under_an_untraversable_parent(tmp_path: Path) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "note.md").write_text("x\n", encoding="utf-8")
    os.chmod(locked, 0o400)
    try:
        assert unreachable(locked / "note.md")
    finally:
        os.chmod(locked, 0o755)


def test_unreadable_directories_is_empty_on_a_healthy_tree(tmp_path: Path) -> None:
    """The control. A collector that named every directory would satisfy every assertion below."""
    (tmp_path / "docs" / "sub").mkdir(parents=True)
    (tmp_path / "docs" / "sub" / "note.md").write_text("x\n", encoding="utf-8")

    assert unreadable_directories(tmp_path / "docs") == frozenset()


@needs_a_non_root_user
def test_unreadable_directories_names_a_subdirectory_it_could_not_list(tmp_path: Path) -> None:
    """Recursive, which is the half a one-shot probe of the root cannot do: a `0o000`
    *subdirectory* loses only the documents beneath it, and just as quietly."""
    locked = tmp_path / "docs" / "sub"
    locked.mkdir(parents=True)
    (locked / "note.md").write_text("x\n", encoding="utf-8")
    os.chmod(locked, 0o000)
    try:
        assert unreadable_directories(tmp_path / "docs") == frozenset({locked})
    finally:
        os.chmod(locked, 0o755)


@needs_a_non_root_user
def test_unreadable_directories_names_the_root_itself_when_the_root_is_the_one_refused(
    tmp_path: Path,
) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    (root / "note.md").write_text("x\n", encoding="utf-8")
    os.chmod(root, 0o000)
    try:
        assert unreadable_directories(root) == frozenset({root})
    finally:
        os.chmod(root, 0o755)


def test_unreadable_directories_says_nothing_about_a_root_that_is_not_there(
    tmp_path: Path,
) -> None:
    """**The other load-bearing control**, and the reason the hook filters by exception type.

    A root the user deleted *should* retire the documents under it. Folding `FileNotFoundError`
    into "unreadable" would hold every one of those rows for a directory that is never coming
    back — a KB that can no longer forget anything.
    """
    assert unreadable_directories(tmp_path / "gone") == frozenset()


def test_unreadable_directories_says_nothing_about_a_root_that_is_a_file(tmp_path: Path) -> None:
    """`NotADirectoryError`, the second honest "not a directory to walk" answer."""
    (tmp_path / "notadir").write_text("x\n", encoding="utf-8")

    assert unreadable_directories(tmp_path / "notadir") == frozenset()


@needs_a_non_root_user
def test_unreadable_directories_cannot_see_a_directory_that_lists_but_cannot_be_entered(
    tmp_path: Path,
) -> None:
    """**A stated limit, pinned so it cannot be quietly assumed away.**

    At `0o400` `scandir` succeeds, so no error is raised for `onerror` to receive. The class is
    still covered — `unreachable` catches it one entry at a time, and the walk records the parent
    — but the two are halves of one question rather than alternatives, and a later reader deleting
    the second half because "the directory collector handles it" would reopen the defect.
    """
    locked = tmp_path / "docs" / "sub"
    locked.mkdir(parents=True)
    (locked / "note.md").write_text("x\n", encoding="utf-8")
    os.chmod(locked, 0o400)
    try:
        assert unreadable_directories(tmp_path / "docs") == frozenset()
        assert unreachable(locked / "note.md")
    finally:
        os.chmod(locked, 0o755)


# --- `unreachable_through_links`: the same question, asked of the target ---------------------


def test_through_links_is_false_for_the_three_shapes_that_are_not_refusals(tmp_path: Path) -> None:
    """Absent, not-a-directory and a loop all answer `False`, and none of them is a refusal.

    These are three of the four errnos 3.13's `Path.is_file()` swallows, and the predicate has to
    swallow the same ones or it reports "unreadable" about paths that are merely not there. The
    fourth, `EBADF`, is measured but not pinned here: the `/dev/fd/<n>` shape that produces it on
    macOS is not portable, and asserting it would be a claim about the runner rather than about the
    predicate. `docs`-side note in `paths._NOT_THERE` says which members are measured how.
    """
    (tmp_path / "afile").write_text("x\n", encoding="utf-8")
    (tmp_path / "loop").symlink_to(tmp_path / "loop")
    (tmp_path / "dangling").symlink_to(tmp_path / "nowhere")

    assert not unreachable_through_links(tmp_path / "absent")  # ENOENT
    assert not unreachable_through_links(tmp_path / "afile" / "under")  # ENOTDIR
    assert not unreachable_through_links(tmp_path / "loop")  # ELOOP
    assert not unreachable_through_links(tmp_path / "dangling")  # ENOENT, one hop out
    assert not unreachable_through_links(tmp_path / "afile"), "control: an ordinary file"


@needs_a_non_root_user
def test_through_links_is_true_for_an_entry_under_an_untraversable_parent(tmp_path: Path) -> None:
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "note.md").write_text("x\n", encoding="utf-8")
    os.chmod(locked, 0o000)
    try:
        assert unreachable_through_links(locked / "note.md")
    finally:
        os.chmod(locked, 0o755)


@needs_a_non_root_user
def test_through_links_sees_a_refusal_one_hop_out_that_unreachable_cannot(tmp_path: Path) -> None:
    """The whole reason the sibling exists, asserted as the pair rather than as two facts.

    `lstat` succeeds on a symlink sitting in a readable directory, so `unreachable` answers `False`
    however unreadable the target is — the same `False` it gives for a path that is simply absent.
    A caller that must not confuse *refused* with *absent* therefore cannot use it here, and both
    callers of this predicate turn that confusion into a wrong message: `pnk link` says a document
    is not in the KB, and `pnk doctor` drops a paid document out of both of its staleness lists.

    This is the row-30 shape — a symlinked document under a directory the process may not traverse
    — which is how a permanent ULID came to be offered to `--prune`.
    """
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "real.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "alias.md").symlink_to(locked / "real.md")
    os.chmod(locked, 0o000)
    try:
        assert unreachable_through_links(tmp_path / "alias.md")
        assert not unreachable(tmp_path / "alias.md"), (
            "the sibling's `lstat` sees the link itself and cannot see past it — if this ever "
            "becomes True the two predicates have collapsed into one and `sync`'s retirement pass "
            "needs re-reading before either is used there"
        )
    finally:
        os.chmod(locked, 0o755)
