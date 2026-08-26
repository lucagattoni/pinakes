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
