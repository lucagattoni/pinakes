"""§6.4, row by row. This is the logic that silently corrupts a KB when it is wrong."""

import pytest

from pinakes.errors import DuplicateIdsError
from pinakes.ids import DocId, mint_doc_id
from pinakes.pairing import (
    ACTIVE,
    DELETED,
    Adopt,
    IndexedDocument,
    IndexSnapshot,
    Mint,
    PaidExtractionRequired,
    PairingResult,
    Reembed,
    RefreshMetadata,
    Rename,
    Skip,
    SoftDelete,
    WalkedFile,
    WalkedSidecar,
    WalkSnapshot,
    actions_of,
    describe,
    pair,
)


def indexed(
    doc_id: DocId,
    path: str,
    content_hash: str = "h1",
    sidecar_hash: str | None = None,
    state: str = ACTIVE,
    extraction_backend: str | None = None,
) -> IndexedDocument:
    return IndexedDocument(
        id=doc_id,
        path=path,
        content_hash=content_hash,
        sidecar_hash=sidecar_hash,
        state=state,
        extraction_backend=extraction_backend,
    )


def retires_before_adopting(result: PairingResult) -> bool:
    """No `Adopt` may land on a path whose current row this same plan retires *later*.

    `describe()` cannot see this and two mutants survived because of it. When the same-path branch
    skips a `SoftDelete`, the vanished-path loop re-emits one further down the list, so a plan with
    the two in the wrong order has an **identical census** — same actions, same counts, different
    meaning. Order is what execution depends on: `documents.path` is UNIQUE, so an `Adopt` applied
    while the row it replaces is still active raises `IntegrityError` instead of replacing it.
    """
    # Forward, so a path retired more than once keeps its **latest** position. Built `reversed`
    # first, which kept the earliest — and a plan that retires a path, adopts onto it, then retires
    # it again satisfied the comparison while doing exactly what the sentence above forbids.
    retired_at = {
        action.path: position
        for position, action in enumerate(result.actions)
        if isinstance(action, SoftDelete)
    }
    return all(
        retired_at[action.path] < position
        for position, action in enumerate(result.actions)
        if isinstance(action, Adopt) and action.path in retired_at
    )


def places_each_id_once(result: PairingResult) -> bool:
    """No plan may assert that one id lives at two different paths.

    A `Skip`, `RefreshMetadata`, `Reembed`, `Rename` or `Adopt` all say "this id is *here*". Two of
    them naming one id and two paths is not a plan, it is a contradiction, and which of the two
    wins depends only on which is applied last. `SoftDelete` is excluded deliberately: it names
    where a row *was*, not where it is going.

    Found the hard way. Moving a sidecar from one document onto another produced
    `RefreshMetadata(X, a.md)` beside `Adopt(X, b.md)` — the same-path loop trusted the index row
    because no sidecar contradicted it, while the adoption loop followed the sidecar that had
    walked away. `pnk sync` exited 0 having moved the row to `b.md` and left `a.md` on disk with no
    row at all, indexed yesterday and unfindable today.
    """
    placed: dict[DocId, str] = {}
    for action in result.actions:
        if isinstance(action, SoftDelete | PaidExtractionRequired | Mint):
            continue
        if placed.setdefault(action.doc_id, action.path) != action.path:
            return False
    return True


def every_write_lands_on_a_free_path(result: PairingResult, before: IndexSnapshot) -> bool:
    """Apply the plan against a model of `documents.path` and see whether SQLite would accept it.

    **The property `describe()` and every ordering-free assertion are blind to, and the one S16 is
    about.** `documents.path` is `UNIQUE`, so a plan is applicable only if, at the moment each
    action writes, nothing else still holds the path it wants. That is a fact about the *sequence*,
    not about its contents: a chain of renames emitted forwards and the same chain emitted
    backwards have an identical census, identical ids, identical paths — and one of them is
    rejected by the database at its first write.

    The model is deliberately the database's rule and not the code's: a live row occupies its path
    until something moves it or retires it, and `sync`'s write guard clears a *retired* row out of
    the way. Written from `sync.py`'s behaviour rather than from `pairing`'s, so a bug shared by
    both cannot make this agree with itself.

    Returns `False` for a genuine cycle, which has no applicable order at all — that is the
    deferred half of S16 and is asserted as such rather than smoothed over.
    """
    occupied: dict[str, DocId | None] = {
        document.path: document.id for document in before.documents if document.state == ACTIVE
    }
    for action in result.actions:
        match action:
            case Adopt(old_path=old) | Rename(old_path=old):
                if old is not None:
                    occupied.pop(old, None)
            case SoftDelete(path=path, doc_id=doc_id):
                # Retired in place: the row keeps its path, and `sync`'s write guard is then free
                # to delete it when a different id writes there.
                if occupied.get(path) == doc_id:
                    del occupied[path]
            case _:
                pass
        # `Mint` writes a row with no id yet, which is why the mapping's value is optional: a
        # freshly minted row occupies its path exactly as a known one does, and a plan that mints
        # onto a path someone is still leaving is rejected by SQLite just the same.
        match action:
            case Adopt(path=target, doc_id=writer) | Rename(path=target, doc_id=writer):
                pass
            case Mint(path=target):
                writer = None
            case _:
                continue
        holder = occupied.get(target)
        if holder is not None and holder != writer:
            return False
        occupied[target] = writer
    return True


def walked(path: str, content_hash: str = "h1") -> WalkedFile:
    return WalkedFile(path=path, content_hash=content_hash)


def sidecar(document_path: str, doc_id: DocId, file_hash: str = "s1") -> WalkedSidecar:
    return WalkedSidecar(
        path=f"{document_path}.pnk.yaml",
        document_path=document_path,
        id=doc_id,
        file_hash=file_hash,
    )


# --- Row: path and content unchanged --------------------------------------------------------


def test_unchanged_document_is_skipped() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.md", "h1", "s1"),)),
        WalkSnapshot((walked("docs/a.md", "h1"),), (sidecar("docs/a.md", doc, "s1"),)),
    )
    assert describe(result) == {"Skip": 1}
    assert actions_of(result, Skip)[0].doc_id == doc


# --- Row: sidecar-only edit (design pass 7) -------------------------------------------------


def test_a_sidecar_only_edit_refreshes_metadata_without_re_embedding() -> None:
    """Tags changed, document untouched: re-embedding would be waste, skipping would be a freeze."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.md", "h1", "s1"),)),
        WalkSnapshot((walked("docs/a.md", "h1"),), (sidecar("docs/a.md", doc, "s2"),)),
    )
    assert describe(result) == {"RefreshMetadata": 1}
    assert actions_of(result, RefreshMetadata)[0].sidecar_hash == "s2"


# --- Row: path unchanged, content changed ---------------------------------------------------


def test_edited_document_is_re_embedded_and_keeps_its_id() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.md", "h1"),)),
        WalkSnapshot((walked("docs/a.md", "h2"),), (sidecar("docs/a.md", doc),)),
    )
    assert describe(result) == {"Reembed": 1}
    action = actions_of(result, Reembed)[0]
    assert action.doc_id == doc
    assert action.content_hash == "h2"


# --- Row: rename (one new path, same content) -----------------------------------------------


def test_a_rename_keeps_the_id() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/old.md", "h1"),)),
        WalkSnapshot((walked("docs/new.md", "h1"),), (sidecar("docs/new.md", doc),)),
    )
    assert describe(result) == {"Adopt": 1}
    assert actions_of(result, Adopt)[0].doc_id == doc
    assert actions_of(result, Adopt)[0].old_path == "docs/old.md"


def test_a_rename_without_a_sidecar_is_detected_by_content() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/old.md", "h1"),)),
        WalkSnapshot((walked("docs/new.md", "h1"),), ()),
    )
    assert describe(result) == {"Rename": 1}
    renamed = actions_of(result, Rename)[0]
    assert (renamed.doc_id, renamed.old_path, renamed.path) == (doc, "docs/old.md", "docs/new.md")


# --- Row: duplicate content, ambiguous --------------------------------------------------------


def test_duplicate_content_is_reported_rather_than_guessed() -> None:
    """Attaching the id to the wrong duplicate would silently redirect every inbound link."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/old.md", "h1"),)),
        WalkSnapshot((walked("docs/one.md", "h1"), walked("docs/two.md", "h1")), ()),
    )
    assert len(result.ambiguities) == 1
    assert result.ambiguities[0].candidates == ("docs/one.md", "docs/two.md")
    assert describe(result) == {"SoftDelete": 1, "Mint": 2}


def test_a_sidecar_breaks_the_duplicate_tie() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/old.md", "h1"),)),
        WalkSnapshot(
            (walked("docs/one.md", "h1"), walked("docs/two.md", "h1")),
            (sidecar("docs/two.md", doc),),
        ),
    )
    assert result.ambiguities == ()
    assert actions_of(result, Adopt)[0].path == "docs/two.md"
    assert actions_of(result, Mint)[0].path == "docs/one.md"


# --- Row: new file -----------------------------------------------------------------------------


def test_a_new_file_without_a_sidecar_is_minted() -> None:
    result = pair(IndexSnapshot(), WalkSnapshot((walked("docs/new.md", "h9"),), ()))
    assert describe(result) == {"Mint": 1}
    assert actions_of(result, Mint)[0].path == "docs/new.md"


def test_a_new_file_with_a_sidecar_adopts_its_id() -> None:
    """A KB cloned from a colleague arrives with sidecars and no index; the ids must survive."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot(), WalkSnapshot((walked("docs/a.md", "h1"),), (sidecar("docs/a.md", doc),))
    )
    assert describe(result) == {"Adopt": 1}
    adopted = actions_of(result, Adopt)[0]
    assert adopted.doc_id == doc
    assert adopted.old_path is None


# --- Row: deletion -----------------------------------------------------------------------------


def test_a_vanished_document_is_soft_deleted() -> None:
    doc = mint_doc_id()
    result = pair(IndexSnapshot((indexed(doc, "docs/gone.md", "h1"),)), WalkSnapshot())
    assert describe(result) == {"SoftDelete": 1}
    assert actions_of(result, SoftDelete)[0].doc_id == doc


def test_an_already_deleted_document_is_left_alone() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/gone.md", "h1", state=DELETED),)), WalkSnapshot()
    )
    assert describe(result) == {}


def test_a_returning_file_revives_its_row() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.md", "h1", state=DELETED),)),
        WalkSnapshot((walked("docs/a.md", "h1"),), ()),
    )
    assert describe(result) == {"Reembed": 1}


# --- Row: duplicate ids (fatal) ----------------------------------------------------------------


def test_one_id_in_two_sidecars_is_fatal_and_names_both() -> None:
    doc = mint_doc_id()
    with pytest.raises(DuplicateIdsError) as exc_info:
        pair(
            IndexSnapshot(),
            WalkSnapshot(
                (walked("docs/a.md"), walked("docs/b.md")),
                (sidecar("docs/a.md", doc), sidecar("docs/b.md", doc)),
            ),
        )
    assert "docs/a.md.pnk.yaml" in exc_info.value.message
    assert "docs/b.md.pnk.yaml" in exc_info.value.message
    assert "Never edit the id" in exc_info.value.remedy


# --- Compound cases ----------------------------------------------------------------------------


def test_rename_plus_edit_keeps_the_id_and_emits_no_delete() -> None:
    """The hash tie is gone, but the sidecar travelled — inbound links must survive (§6.4)."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/old.md", "h1"),)),
        WalkSnapshot((walked("docs/new.md", "h2"),), (sidecar("docs/new.md", doc),)),
    )
    assert describe(result) == {"Adopt": 1}
    assert not actions_of(result, SoftDelete)
    assert actions_of(result, Adopt)[0].old_path == "docs/old.md"


def test_rename_plus_edit_without_the_sidecar_is_reported_as_such() -> None:
    """§9's most likely real-world corruption, surfaced at the moment it happens."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/old.md", "h1"),)),
        WalkSnapshot((walked("docs/new.md", "h2"),), ()),
    )
    assert describe(result) == {"SoftDelete": 1, "Mint": 1}
    assert result.moved_without_sidecar == ("docs/old.md",)


def test_a_sidecar_whose_document_is_gone_is_reported_as_orphaned() -> None:
    doc = mint_doc_id()
    result = pair(IndexSnapshot(), WalkSnapshot((), (sidecar("docs/gone.md", doc),)))
    assert result.orphaned_sidecars == ("docs/gone.md.pnk.yaml",)


def test_a_sidecar_disagreeing_with_the_index_wins() -> None:
    """`docs/` is the truth; the index is derived. The stale row is retired, not silently kept."""
    old, new = mint_doc_id(), mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(old, "docs/a.md", "h1"),)),
        WalkSnapshot((walked("docs/a.md", "h1"),), (sidecar("docs/a.md", new),)),
    )
    assert describe(result) == {"SoftDelete": 1, "Adopt": 1}
    assert actions_of(result, SoftDelete)[0].doc_id == old
    assert actions_of(result, Adopt)[0].doc_id == new
    assert retires_before_adopting(result)


def test_a_whole_mixed_sync() -> None:
    kept, edited, renamed, gone = (mint_doc_id() for _ in range(4))
    result = pair(
        IndexSnapshot(
            (
                indexed(kept, "docs/kept.md", "h1", "s1"),
                indexed(edited, "docs/edited.md", "h2"),
                indexed(renamed, "docs/old.md", "h3"),
                indexed(gone, "docs/gone.md", "h4"),
            )
        ),
        WalkSnapshot(
            (
                walked("docs/kept.md", "h1"),
                walked("docs/edited.md", "h2-changed"),
                walked("docs/new.md", "h3"),
                walked("docs/brand-new.md", "h5"),
            ),
            (sidecar("docs/kept.md", kept, "s1"),),
        ),
    )
    assert describe(result) == {"Skip": 1, "Reembed": 1, "Rename": 1, "SoftDelete": 1, "Mint": 1}


def test_pairing_is_pure_and_order_independent() -> None:
    """Same picture, different walk order, same decisions — pairing is set-wise (§6.4)."""
    first, second = mint_doc_id(), mint_doc_id()
    before = IndexSnapshot((indexed(first, "docs/a.md", "h1"), indexed(second, "docs/b.md", "h2")))
    forward = WalkSnapshot((walked("docs/a.md", "h1"), walked("docs/b.md", "h2-new")), ())
    backward = WalkSnapshot((walked("docs/b.md", "h2-new"), walked("docs/a.md", "h1")), ())
    assert describe(pair(before, forward)) == describe(pair(before, backward))


# --- I5: decision 9's backend-aware rows ----------------------------------------------------
#
# `pair()`'s own DB-sourced `before` only ever sees the "same path, same id" instances of these
# rows — the `--rebuild` case (an empty `before`) is `sync.py`'s own `_paid_rebuild_survivors`
# mechanism, covered in `tests/test_sync.py::test_backend_drift` and the rebuild-provenance tests
# instead, since `pair()` alone cannot see it.


def test_free_recorded_paid_effective_reembeds_regardless_of_hash() -> None:
    """Rule 1: stale the moment the effective backend outranks what is recorded — the hash does
    not even factor in."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.pdf", "h1", extraction_backend="pypdfium2"),)),
        WalkSnapshot((walked("docs/a.pdf", "h1"),), (sidecar("docs/a.pdf", doc),)),
        effective_backend="claude-vision",
        paid_backend_names=frozenset({"claude-vision"}),
    )
    assert describe(result) == {"Reembed": 1}


def test_paid_recorded_free_effective_unchanged_hash_is_protected() -> None:
    """Rule 2: never silently downgraded — not by a hook, not by an explicit free `--extract`."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.pdf", "h1", extraction_backend="claude-vision"),)),
        WalkSnapshot((walked("docs/a.pdf", "h1"),), (sidecar("docs/a.pdf", doc),)),
        effective_backend="pypdfium2",
        paid_backend_names=frozenset({"claude-vision"}),
    )
    assert describe(result) == {"Skip": 1}
    assert result.paid_extraction_protected == ("docs/a.pdf",)


def test_paid_recorded_free_effective_changed_hash_requires_paid_extraction() -> None:
    """Rule 3: a changed hash is neither a silent Skip nor a silent overwrite — a named outcome
    the caller must act on (decision 14)."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.pdf", "h1", extraction_backend="claude-vision"),)),
        WalkSnapshot((walked("docs/a.pdf", "h2"),), (sidecar("docs/a.pdf", doc),)),
        effective_backend="pypdfium2",
        paid_backend_names=frozenset({"claude-vision"}),
    )
    assert describe(result) == {"PaidExtractionRequired": 1}
    required = actions_of(result, PaidExtractionRequired)[0]
    assert (required.doc_id, required.path, required.recorded_backend) == (
        doc,
        "docs/a.pdf",
        "claude-vision",
    )


def test_force_alone_without_an_explicit_extract_does_not_override() -> None:
    """`--force` alone changes nothing — only together with an explicit free `--extract`."""
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.pdf", "h1", extraction_backend="claude-vision"),)),
        WalkSnapshot((walked("docs/a.pdf", "h1"),), (sidecar("docs/a.pdf", doc),)),
        effective_backend="pypdfium2",
        paid_backend_names=frozenset({"claude-vision"}),
        force=True,
        explicit_extract=False,
    )
    assert describe(result) == {"Skip": 1}
    assert result.paid_extraction_protected == ("docs/a.pdf",)


def test_force_with_an_explicit_extract_overwrites_and_says_so() -> None:
    doc = mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(doc, "docs/a.pdf", "h1", extraction_backend="claude-vision"),)),
        WalkSnapshot((walked("docs/a.pdf", "h1"),), (sidecar("docs/a.pdf", doc),)),
        effective_backend="pypdfium2",
        paid_backend_names=frozenset({"claude-vision"}),
        force=True,
        explicit_extract=True,
    )
    assert describe(result) == {"Reembed": 1}
    assert result.paid_extraction_overwritten == ("docs/a.pdf",)
    assert result.paid_extraction_protected == ()


def test_omitting_the_new_parameters_behaves_exactly_as_before() -> None:
    """Every caller that has not been taught about backends yet (there are none left in this repo,
    but the defaults are the contract) must see the pre-I5 behaviour: a paid-recorded, unchanged
    document is skipped for the ordinary reason, not "protected" — there is no paid backend name to
    even recognise it by."""
    doc = mint_doc_id()
    before = indexed(doc, "docs/a.pdf", "h1", "s1", extraction_backend="claude-vision")
    result = pair(
        IndexSnapshot((before,)),
        WalkSnapshot((walked("docs/a.pdf", "h1"),), (sidecar("docs/a.pdf", doc, "s1"),)),
    )
    assert describe(result) == {"Skip": 1}
    assert result.paid_extraction_protected == ()
    assert result.paid_extraction_overwritten == ()


def test_a_name_swap_never_retires_an_id_the_same_plan_adopts() -> None:
    """`git mv` two documents past each other, sidecars travelling with them.

    Both rows are moving, so neither is ending. Emitting `SoftDelete` beside the `Adopt` made the
    result depend on application order: the second `SoftDelete` retired the row the first `Adopt`
    had just moved, `pnk sync` reported `2 renamed` at exit 0, and the document left `pnk search`
    with no failure recorded anywhere.
    """
    alpha, beta = mint_doc_id(), mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(alpha, "docs/a.md", "ha"), indexed(beta, "docs/b.md", "hb"))),
        WalkSnapshot(
            (walked("docs/a.md", "hb"), walked("docs/b.md", "ha")),
            (sidecar("docs/a.md", beta), sidecar("docs/b.md", alpha)),
        ),
    )
    assert describe(result) == {"Adopt": 2}
    assert not actions_of(result, SoftDelete)
    assert {(action.doc_id, action.path) for action in actions_of(result, Adopt)} == {
        (beta, "docs/a.md"),
        (alpha, "docs/b.md"),
    }


def test_a_rename_chain_keeps_the_id_its_own_sidecar_carries() -> None:
    """`a.md -> b.md` while `c.md -> a.md`. The id arriving at `a.md` displaces the one leaving it.

    Retiring the displaced id also marked it handled, which is what the adoption loop consults —
    so `b.md` was never adopted at all and fell through to `Mint`. A document whose sidecar carries
    a published id would have been re-numbered, and ULID permanence is an invariant.
    """
    moved, arriving = mint_doc_id(), mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(moved, "docs/a.md", "ha"), indexed(arriving, "docs/c.md", "hc"))),
        WalkSnapshot(
            (walked("docs/a.md", "hc"), walked("docs/b.md", "ha")),
            (sidecar("docs/a.md", arriving), sidecar("docs/b.md", moved)),
        ),
    )
    assert describe(result) == {"Adopt": 2}
    assert not actions_of(result, Mint), "a published id was re-minted"
    adopted = {action.doc_id: action.path for action in actions_of(result, Adopt)}
    assert adopted[moved] == "docs/b.md"
    assert adopted[arriving] == "docs/a.md"


def test_a_three_way_rename_cycle_adopts_every_id_and_retires_none() -> None:
    first, second, third = mint_doc_id(), mint_doc_id(), mint_doc_id()
    result = pair(
        IndexSnapshot(
            (
                indexed(first, "docs/a.md", "ha"),
                indexed(second, "docs/b.md", "hb"),
                indexed(third, "docs/c.md", "hc"),
            )
        ),
        WalkSnapshot(
            (walked("docs/a.md", "hc"), walked("docs/b.md", "ha"), walked("docs/c.md", "hb")),
            (
                sidecar("docs/a.md", third),
                sidecar("docs/b.md", first),
                sidecar("docs/c.md", second),
            ),
        ),
    )
    assert describe(result) == {"Adopt": 3}


def test_an_orphaned_sidecar_does_not_keep_a_replaced_id_alive() -> None:
    """The displaced id's own sidecar is on disk, but the document beside it is gone.

    Nothing is moving anywhere, so the row is being replaced in place and must still be retired.
    The lookahead is deliberately restricted to sidecars sitting beside a file this walk *found*:
    without that restriction a stale sidecar left in the tree would protect a row from deletion
    forever, and the ordinary in-place id change would stop working.
    """
    old, new = mint_doc_id(), mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(old, "docs/a.md", "h1"),)),
        WalkSnapshot(
            (walked("docs/a.md", "h1"),),
            (sidecar("docs/a.md", new), sidecar("docs/gone.md", old)),
        ),
    )
    assert describe(result) == {"SoftDelete": 1, "Adopt": 1}
    assert actions_of(result, SoftDelete)[0].doc_id == old
    assert actions_of(result, Adopt)[0].doc_id == new
    assert retires_before_adopting(result), "the row must be retired before its replacement lands"


def test_a_replaced_row_is_always_retired_before_its_replacement_is_adopted() -> None:
    """The half a census cannot assert, and the half execution actually depends on.

    Both of these plans retire one id and adopt another **at the same path**. Whether the retirement
    is emitted by the same-path branch or picked up by the vanished-path loop further down, the
    counts are identical — so `describe()` reports the same thing for a plan that works and a plan
    that raises `sqlite3.IntegrityError` on the first action. Two mutants survived a suite of 267
    tests on exactly that blindness before this test existed.
    """
    for label, sidecars in (
        ("nothing else claims the displaced id", None),
        ("its own sidecar is orphaned elsewhere", "docs/gone.md"),
    ):
        old, new = mint_doc_id(), mint_doc_id()
        walked_sidecars = [sidecar("docs/a.md", new)]
        if sidecars is not None:
            walked_sidecars.append(sidecar(sidecars, old))
        result = pair(
            IndexSnapshot((indexed(old, "docs/a.md", "h1"),)),
            WalkSnapshot((walked("docs/a.md", "h1"),), tuple(walked_sidecars)),
        )
        kinds = [type(action).__name__ for action in result.actions]
        assert kinds == ["SoftDelete", "Adopt"], f"{label}: {kinds}"
        assert retires_before_adopting(result), label


def test_a_sidecar_moved_onto_another_document_takes_its_id_with_it() -> None:
    """Someone moves `a.md`'s sidecar onto `b.md`. The sidecar is committed truth for identity, so
    the id belongs to `b.md` now — and `a.md`, which no longer has one, is a new document.

    Before this was guarded the same-path loop kept asserting that `a.md` was still that id, because
    nothing beside `a.md` said otherwise, while the disagreement branch adopted the very same id at
    `b.md`. One id, two paths, one plan; applied in order it moved the row and left `a.md` with
    no row at all.
    """
    alpha, beta = mint_doc_id(), mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(alpha, "docs/a.md", "ha"), indexed(beta, "docs/b.md", "hb"))),
        WalkSnapshot(
            (walked("docs/a.md", "ha"), walked("docs/b.md", "hb")),
            (sidecar("docs/b.md", alpha),),
        ),
    )
    assert places_each_id_once(result), "one id was placed at two paths"
    assert retires_before_adopting(result)
    assert describe(result) == {"SoftDelete": 1, "Adopt": 1, "Mint": 1}
    assert actions_of(result, Adopt)[0] == Adopt(
        doc_id=alpha, path="docs/b.md", content_hash="hb", sidecar_hash="s1", old_path="docs/a.md"
    )
    assert actions_of(result, SoftDelete)[0].doc_id == beta
    assert actions_of(result, Mint)[0].path == "docs/a.md"


def test_no_plan_in_this_file_ever_places_one_id_at_two_paths() -> None:
    """The property over every shape this file exercises, not only the one that broke it.

    A helper asserted case by case is a helper nobody runs on the case they did not think of.
    """
    first, second, third = mint_doc_id(), mint_doc_id(), mint_doc_id()
    worlds = (
        # a sidecar moved off one document onto another
        (
            ((first, "docs/a.md", "ha"), (second, "docs/b.md", "hb")),
            (("docs/a.md", "ha"), ("docs/b.md", "hb")),
            (("docs/b.md", first),),
        ),
        # two documents renamed past each other
        (
            ((first, "docs/a.md", "ha"), (second, "docs/b.md", "hb")),
            (("docs/a.md", "hb"), ("docs/b.md", "ha")),
            (("docs/a.md", second), ("docs/b.md", first)),
        ),
        # a rename chain
        (
            ((first, "docs/a.md", "ha"), (third, "docs/c.md", "hc")),
            (("docs/a.md", "hc"), ("docs/b.md", "ha")),
            (("docs/a.md", third), ("docs/b.md", first)),
        ),
        # an in-place id change with the old id orphaned elsewhere
        (
            ((first, "docs/a.md", "ha"),),
            (("docs/a.md", "ha"),),
            (("docs/a.md", second), ("docs/gone.md", first)),
        ),
    )
    for number, (rows, files, sidecars) in enumerate(worlds, start=1):
        result = pair(
            IndexSnapshot(tuple(indexed(i, p, h) for i, p, h in rows)),
            WalkSnapshot(
                tuple(walked(p, h) for p, h in files),
                tuple(sidecar(p, i) for p, i in sidecars),
            ),
        )
        assert places_each_id_once(result), f"world {number}: one id at two paths"
        assert retires_before_adopting(result), f"world {number}: adopted before retiring"


# --- Row: ordering, so a plan the database will accept -----------------------------------------
#
# S16/S19. `documents.path` is `UNIQUE`, so *when* an action writes decides whether it can write at
# all — and `pair()` built its list by walking paths in sorted order, which is a fine order for
# deciding what each file is and an arbitrary one for deciding when to write it. Reproduced end to
# end on `main` 20260826: `pnk sync` exit 1 on a raw `sqlite3.IntegrityError`, `pnk search`
# answering from a path no longer on disk, and `pnk doctor` reporting every row `OK` including
# `failures: none recorded`.


def test_a_rename_chain_of_three_is_ordered_so_every_move_lands_on_a_free_path() -> None:
    """**The pinning case, and it is three long on purpose.**

    `a → b`, `b → c`, `c → d`. The only applicable order is *strictly reverse* of the order the
    paths sort in, so no accident of sorting can produce it and **a fix that merely swaps two
    adjacent actions passes the two-file case below while failing this one**. That is the whole
    reason this is the pinning case rather than the shift: a control is worth writing when it kills
    the plausible-but-wrong fix.

    Asserted as an exact sequence rather than through `every_write_lands_on_a_free_path` alone —
    the property says *some* applicable order was reached, this says *which*, and the two together
    are what stop a later refactor from satisfying the property by luck.
    """
    a, b, c = mint_doc_id(), mint_doc_id(), mint_doc_id()
    before = IndexSnapshot(
        (
            indexed(a, "docs/a.md", "ha"),
            indexed(b, "docs/b.md", "hb"),
            indexed(c, "docs/c.md", "hc"),
        )
    )
    result = pair(
        before,
        WalkSnapshot(
            (walked("docs/b.md", "ha"), walked("docs/c.md", "hb"), walked("docs/d.md", "hc")),
            (sidecar("docs/b.md", a), sidecar("docs/c.md", b), sidecar("docs/d.md", c)),
        ),
    )
    assert [(action.doc_id, action.path) for action in actions_of(result, Adopt)] == [
        (c, "docs/d.md"),
        (b, "docs/c.md"),
        (a, "docs/b.md"),
    ]
    assert every_write_lands_on_a_free_path(result, before)
    assert places_each_id_once(result)


def test_a_two_file_rename_shift_is_ordered_too() -> None:
    """`b → c` and `a → b`: not a cycle, and a valid order exists — free `docs/b.md` first.

    Kept beside the chain because it is the shape a person actually produces (`git mv` twice), and
    it is the case the end-to-end reproduction used. It is **not** the pinning case: reversing two
    adjacent actions satisfies it, and a fix that does only that leaves the chain above broken.
    """
    a, b = mint_doc_id(), mint_doc_id()
    before = IndexSnapshot((indexed(a, "docs/a.md", "ha"), indexed(b, "docs/b.md", "hb")))
    result = pair(
        before,
        WalkSnapshot(
            (walked("docs/b.md", "ha"), walked("docs/c.md", "hb")),
            (sidecar("docs/b.md", a), sidecar("docs/c.md", b)),
        ),
    )
    assert [(action.doc_id, action.path) for action in actions_of(result, Adopt)] == [
        (b, "docs/c.md"),
        (a, "docs/b.md"),
    ]
    assert every_write_lands_on_a_free_path(result, before)


def test_a_move_onto_a_name_nobody_holds_is_not_reordered() -> None:
    """Stability. An action moves only when a constraint forces it, so a plan that was already
    applicable comes out exactly as `pair()` built it — otherwise every unrelated reordering
    becomes a behaviour change nothing asked for, and the diff of a future fix stops being
    readable."""
    a, b = mint_doc_id(), mint_doc_id()
    before = IndexSnapshot((indexed(a, "docs/a.md", "ha"), indexed(b, "docs/b.md", "hb")))
    result = pair(
        before,
        WalkSnapshot(
            (walked("docs/a.md", "ha"), walked("docs/z.md", "hb")),
            (sidecar("docs/a.md", a), sidecar("docs/z.md", b)),
        ),
    )
    assert [type(action).__name__ for action in result.actions] == ["RefreshMetadata", "Adopt"]
    assert every_write_lands_on_a_free_path(result, before)


def test_a_name_swap_is_left_in_its_original_order_because_no_order_works() -> None:
    """**The deferred half of S16, pinned as deferred.**

    A swap is a cycle: whichever document moves first writes onto a path the other still holds, and
    resolving it needs a temporary path `pair()` has no way to create. So the ordering pass leaves
    the cyclic actions exactly where it found them and the sync still fails at the first write, as
    it does in 0.30.2 today.

    **This test exists so that "the chain class is fixed" cannot quietly become "renames are
    fixed".** That is the S17 shape — a defect recorded as open after it had been cured, and here
    the same shape in the other direction. If someone makes swaps work, this test goes red and the
    record has to be updated deliberately rather than by omission.
    """
    a, b = mint_doc_id(), mint_doc_id()
    before = IndexSnapshot((indexed(a, "docs/a.md", "ha"), indexed(b, "docs/b.md", "hb")))
    result = pair(
        before,
        WalkSnapshot(
            (walked("docs/a.md", "hb"), walked("docs/b.md", "ha")),
            (sidecar("docs/a.md", b), sidecar("docs/b.md", a)),
        ),
    )
    assert [(action.doc_id, action.path) for action in actions_of(result, Adopt)] == [
        (b, "docs/a.md"),
        (a, "docs/b.md"),
    ]
    assert not every_write_lands_on_a_free_path(result, before), (
        "a swap has become applicable — the deferred half of S16 has been fixed, or this model of "
        "the UNIQUE constraint has stopped matching the database"
    )
    # The S2 guarantees still hold on a plan that cannot be applied, which is the point of them.
    assert places_each_id_once(result)
    assert retires_before_adopting(result)


def test_a_retire_and_an_adopt_at_one_path_keep_their_order() -> None:
    """The trap the ordering pass fell into on its first draft, kept as a test rather than a memory.

    When a file's sidecar carries a different id from the index row, the same-path loop emits
    `SoftDelete(old id)` then `Adopt(sidecar id)` **at the same path**. The adopt is writing onto a
    path a live row holds, so it depends on that row moving out of the way — and the thing that
    moves it is the `SoftDelete`, not a rename. A first draft recorded only renames as freeing a
    path, so this already-correct pair read as depending on an action that did not exist, and would
    have been reported as unorderable.
    """
    old, new = mint_doc_id(), mint_doc_id()
    before = IndexSnapshot((indexed(old, "docs/a.md", "ha"),))
    result = pair(
        before,
        WalkSnapshot((walked("docs/a.md", "ha"),), (sidecar("docs/a.md", new),)),
    )
    assert [type(action).__name__ for action in result.actions] == ["SoftDelete", "Adopt"]
    assert every_write_lands_on_a_free_path(result, before)
    assert retires_before_adopting(result)


def test_every_plan_in_this_file_is_applicable_except_the_cycle() -> None:
    """The property over every shape, not only the one that broke it — the same reasoning as
    `test_no_plan_in_this_file_ever_places_one_id_at_two_paths`, which this deliberately mirrors.

    **The cycle is listed as expected-inapplicable rather than omitted.** A sweep that quietly
    skipped it would be green both before and after someone fixed swaps, and green is exactly what
    the record must not say while that half is open.
    """
    first, second, third = mint_doc_id(), mint_doc_id(), mint_doc_id()
    worlds = (
        # a rename shift: b → c, a → b. Applicable, in one order only.
        (
            "shift",
            True,
            ((first, "docs/a.md", "ha"), (second, "docs/b.md", "hb")),
            (("docs/b.md", "ha"), ("docs/c.md", "hb")),
            (("docs/b.md", first), ("docs/c.md", second)),
        ),
        # a chain of three: the applicable order is strictly reverse.
        (
            "chain of three",
            True,
            (
                (first, "docs/a.md", "ha"),
                (second, "docs/b.md", "hb"),
                (third, "docs/c.md", "hc"),
            ),
            (("docs/b.md", "ha"), ("docs/c.md", "hb"), ("docs/d.md", "hc")),
            (("docs/b.md", first), ("docs/c.md", second), ("docs/d.md", third)),
        ),
        # a sidecar moved off one document onto another
        (
            "sidecar moved",
            True,
            ((first, "docs/a.md", "ha"), (second, "docs/b.md", "hb")),
            (("docs/a.md", "ha"), ("docs/b.md", "hb")),
            (("docs/b.md", first),),
        ),
        # an in-place id change: retire, then adopt, at one path
        (
            "in-place id change",
            True,
            ((first, "docs/a.md", "ha"),),
            (("docs/a.md", "ha"),),
            (("docs/a.md", second),),
        ),
        # two documents renamed past each other — no order works, and that is still true
        (
            "cycle",
            False,
            ((first, "docs/a.md", "ha"), (second, "docs/b.md", "hb")),
            (("docs/a.md", "hb"), ("docs/b.md", "ha")),
            (("docs/a.md", second), ("docs/b.md", first)),
        ),
    )
    for name, applicable, rows, files, sidecars in worlds:
        before = IndexSnapshot(tuple(indexed(i, p, h) for i, p, h in rows))
        result = pair(
            before,
            WalkSnapshot(
                tuple(walked(p, h) for p, h in files),
                tuple(sidecar(p, i) for p, i in sidecars),
            ),
        )
        assert every_write_lands_on_a_free_path(result, before) is applicable, (
            f"{name}: expected applicable={applicable}"
        )
        assert places_each_id_once(result), f"{name}: one id at two paths"
        assert retires_before_adopting(result), f"{name}: adopted before retiring"


def test_actions_under_no_constraint_keep_their_order_inside_a_plan_that_has_one() -> None:
    """Stability **where it can actually be observed** — and this test exists because the one above
    it could not observe it.

    `test_a_move_onto_a_name_nobody_holds_is_not_reordered` uses a plan with no constraints at all,
    and a plan with no constraints never reaches the topological sort: the pass returns the list
    untouched before it starts. So a mutant that made the sort emit ready actions in arbitrary
    order **survived that test, and survived the entire suite** — 2 221 tests — while changing the
    output of every plan that does have a constraint. Found by running the battery, not by reading.

    Here a rename shift (`b → c`, `a → b`, which must be reordered) shares a plan with two
    untouched documents (which must not be). The whole sequence is asserted, because the property
    is about the actions the constraint does **not** name: they are the ones a re-sort silently
    moves, and the ones whose relative order a reader of a future diff will assume is preserved.
    """
    a, b, d, e = mint_doc_id(), mint_doc_id(), mint_doc_id(), mint_doc_id()
    before = IndexSnapshot(
        (
            indexed(a, "docs/a.md", "ha"),
            indexed(b, "docs/b.md", "hb"),
            indexed(d, "docs/d.md", "hd"),
            indexed(e, "docs/e.md", "he"),
        )
    )
    result = pair(
        before,
        WalkSnapshot(
            (
                walked("docs/b.md", "ha"),
                walked("docs/c.md", "hb"),
                walked("docs/d.md", "hd"),
                walked("docs/e.md", "he"),
            ),
            (sidecar("docs/b.md", a), sidecar("docs/c.md", b)),
        ),
    )
    assert [(type(action).__name__, action.path) for action in result.actions] == [
        ("Skip", "docs/d.md"),
        ("Skip", "docs/e.md"),
        ("Adopt", "docs/c.md"),
        ("Adopt", "docs/b.md"),
    ], "the two untouched documents changed places, so the pass is re-sorting rather than ordering"
    assert every_write_lands_on_a_free_path(result, before)


def test_an_orphaned_sidecar_does_not_cost_a_live_document_its_id() -> None:
    """A sidecar whose document is gone claims an id for nothing, and must not be read as a claim.

    **Found by the battery, and only because an unrelated fix took its old witness away.** The
    mutant that widens `claimed_by_id` to include orphans used to die to an *ordering* assertion:
    it moved a `SoftDelete` after the `Adopt` it belongs before. S16's ordering pass now repairs
    that order globally, so the mutant became invisible — **and running it against all 2 212 tests
    found nothing else that saw it.** A fix that enforces a property globally silently unpins every
    test that asserted that property locally, and this is what was underneath.

    What is underneath is worse than the ordering it was hiding behind. `claimed_by_id` has a
    second reader: a file with **no sidecar of its own** whose index id turns up claimed elsewhere
    is read as *"this row's identity has moved"*, so the path is left to be minted fresh. Let an
    orphan count as a claim and that fires on an ordinary document sitting untouched beside a
    stale `.pnk.yaml` — the document is re-minted under a new id while its old one is retired.
    **That is `docs/INVARIANTS.md`'s ULID permanence**, broken by a leftover file, and every
    inbound `pnk://` link to it dies.

    So the assertion is the action *kind*, not the order: an untouched document is `Skip`ped.
    """
    live, orphan_claim = mint_doc_id(), mint_doc_id()
    result = pair(
        IndexSnapshot((indexed(live, "docs/a.md", "ha"),)),
        WalkSnapshot(
            (walked("docs/a.md", "ha"),),
            # The sidecar names a document this walk did not find, and it claims the live id.
            (sidecar("docs/gone.md", live), sidecar("docs/also-gone.md", orphan_claim)),
        ),
    )
    # The action *kind* is the assertion, and it is read without touching `doc_id` on the union:
    # `Mint` carries none, and the mutant's own outcome is a `Mint` in some walks. Asking for an
    # attribute one member does not have would make this test unable to run on the very output it
    # exists to reject.
    assert [type(action).__name__ for action in result.actions] == ["Skip"], (
        "an untouched document was re-identified because a stale sidecar elsewhere named its id"
    )
    skipped = actions_of(result, Skip)
    assert [action.doc_id for action in skipped] == [live], (
        "the surviving row is not the one that was there — the id did not survive the walk"
    )
    assert result.orphaned_sidecars == ("docs/also-gone.md.pnk.yaml", "docs/gone.md.pnk.yaml"), (
        "the orphans must still be reported — they are the evidence for the user, and reporting "
        "them is what makes ignoring them for identity safe"
    )
