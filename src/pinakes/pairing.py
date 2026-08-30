"""Two-phase sync pairing — deciding what each file *is* before touching anything.

This is docs/DESIGN.md §6.4 as a **pure function**: no filesystem, no SQLite, no clock. Everything
it needs arrives as two snapshots, and it returns a list of actions for I8b to execute. That shape
is deliberate — this is the logic that silently corrupts a KB when it is wrong, and a pure function
can be tested exhaustively against the design's table, row by row.

Pairing is *set-wise*, not per-file: a path that vanished might be a delete, or it might be half of
a rename, and you cannot tell which until you have looked at every other file. Phase 1 is the caller
walking the tree; phase 2 is this module resolving the whole picture at once.

The rules, in the order they are applied:

| Case | Action |
|---|---|
| Path and content unchanged | `Skip` — or `RefreshMetadata` if only the sidecar changed |
| Path unchanged, content changed | `Reembed`, keeping the id |
| Path gone, exactly one new path with the same content | `Rename`, keeping the id |
| Path gone, several share it | prefer the one whose sidecar carries the old id; else report |
| New path with an adjacent sidecar | `Adopt` its id (also how rename+edit keeps its identity) |
| New path, no sidecar | `Mint` |
| Path gone, nothing matches | `SoftDelete` |
| One id in two sidecars | raise — never renumber |

Two consequences worth stating, because both are ways a KB quietly rots:

* **Adoption beats deletion.** When a file is moved *and* edited in one sync, the content hash no
  longer ties the two paths together — but the sidecar travelled with it. The id continues at the
  new path and **no delete is emitted for it**, so inbound links survive.
* **A duplicated id is fatal, not repairable.** Renumbering would break links that were fine, so
  this raises and names both paths (§6.4).
* **No plan ever retires an id it also adopts.** A `SoftDelete` and an `Adopt` for one id in one
  list have an outcome that depends on which is applied last, and both orders are wrong: renaming
  two documents past each other retired the row that had just been adopted, and a rename *chain*
  hid the id from the adoption loop so the file was re-minted under a fresh one. Whether the id is
  ending or moving is a question about the *whole* walk — which sidecar claims it — so it is
  answered here, once, and never at execution time.
"""

import heapq
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from pinakes.errors import DuplicateIdsError
from pinakes.ids import DocId

ACTIVE = "active"
DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class IndexedDocument:
    """One `documents` row, as the previous sync left it."""

    id: DocId
    path: str
    content_hash: str
    sidecar_hash: str | None = None
    state: str = ACTIVE
    extraction_backend: str | None = None
    """`None` for a non-extracted source. `--rebuild` cannot read this from an empty new database
    (I5, decision 11) — its caller seeds it from the sidecar's `provenance.extraction` instead."""


@dataclass(frozen=True, slots=True)
class WalkedFile:
    """One source file found on disk."""

    path: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class WalkedSidecar:
    """One `.pnk.yaml` found on disk, and the document path it sits beside."""

    path: str
    document_path: str
    id: DocId
    file_hash: str


@dataclass(frozen=True, slots=True)
class IndexSnapshot:
    documents: tuple[IndexedDocument, ...] = ()


@dataclass(frozen=True, slots=True)
class WalkSnapshot:
    files: tuple[WalkedFile, ...] = ()
    sidecars: tuple[WalkedSidecar, ...] = ()


@dataclass(frozen=True, slots=True)
class Skip:
    doc_id: DocId
    path: str


@dataclass(frozen=True, slots=True)
class RefreshMetadata:
    """The document is untouched; only its sidecar changed. Re-read metadata, do not re-embed."""

    doc_id: DocId
    path: str
    sidecar_hash: str | None


@dataclass(frozen=True, slots=True)
class Reembed:
    doc_id: DocId
    path: str
    content_hash: str
    sidecar_hash: str | None


@dataclass(frozen=True, slots=True)
class Rename:
    doc_id: DocId
    old_path: str
    path: str
    content_hash: str
    sidecar_hash: str | None


@dataclass(frozen=True, slots=True)
class Adopt:
    """A new path whose sidecar carries an id — either a first ingest of a shared doc, or a move."""

    doc_id: DocId
    path: str
    content_hash: str
    sidecar_hash: str | None
    old_path: str | None


@dataclass(frozen=True, slots=True)
class Mint:
    path: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class SoftDelete:
    doc_id: DocId
    path: str


@dataclass(frozen=True, slots=True)
class PaidExtractionRequired:
    """A paid-extracted document's content changed under a free-effective run (I5, decision 14).

    Neither re-extracting with the downgraded free backend (silently discarding paid quality)
    nor leaving the stale text indexed (silently wrong) is honest — this becomes a `failures` row
    naming the path and the paid backend, so the remedy is a deliberate, paid re-extraction.
    """

    doc_id: DocId
    path: str
    recorded_backend: str


type Action = (
    Skip | RefreshMetadata | Reembed | Rename | Adopt | Mint | SoftDelete | PaidExtractionRequired
)


@dataclass(frozen=True, slots=True)
class Ambiguity:
    """Several new paths carry the content of one vanished document, and nothing breaks the tie."""

    old_doc_id: DocId
    old_path: str
    candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PairingResult:
    actions: tuple[Action, ...] = ()
    ambiguities: tuple[Ambiguity, ...] = ()
    orphaned_sidecars: tuple[str, ...] = ()
    moved_without_sidecar: tuple[str, ...] = ()
    """Paths that were soft-deleted and re-minted because their sidecar did not travel (§9)."""
    paid_extraction_protected: tuple[str, ...] = ()
    """Paths kept at their paid extraction despite a free-effective run — printed once, not
    silently (I5, decision 9)."""
    paid_extraction_overwritten: tuple[str, ...] = ()
    """Paths where `--force` plus an explicit free `--extract` discarded a paid extraction —
    printed *before* it happens, naming what is about to be lost (I5, decision 9)."""


def pair(
    before: IndexSnapshot,
    after: WalkSnapshot,
    *,
    effective_backend: str | None = None,
    paid_backend_names: frozenset[str] = frozenset(),
    force: bool = False,
    explicit_extract: bool = False,
) -> PairingResult:
    """`effective_backend`/`paid_backend_names` classify only the *recorded-paid* direction here
    (decision 9's other two clauses): a document whose `IndexedDocument.extraction_backend` is
    paid, compared against whether the backend in effect *for this run* is paid too. Left at their
    defaults, no document can ever be "recorded paid" against an empty `paid_backend_names`, so
    every existing call site and test that never heard of backends keeps its exact old behaviour.
    """
    _reject_duplicate_ids(after.sidecars)

    sidecar_by_document = {sidecar.document_path: sidecar for sidecar in after.sidecars}
    before_by_path = {document.path: document for document in before.documents}
    before_by_id = {document.id: document for document in before.documents}
    after_by_path = {file.path: file for file in after.files}
    # Every id some *surviving* document's sidecar claims. A set, not a mapping: both readers below
    # ask only whether an id is in it, and a dict would promise a claiming sidecar nobody fetches.
    # Only sidecars sitting beside a file this walk actually found count — an orphaned sidecar
    # claims an id for a document that is no longer there, and treating that as "still ours" would
    # keep a genuinely deleted document out of `SoftDelete` forever.
    claimed_by_id = frozenset(
        sidecar.id for sidecar in after.sidecars if sidecar.document_path in after_by_path
    )

    effective_is_paid = effective_backend is not None and effective_backend in paid_backend_names

    actions: list[Action] = []
    ambiguities: list[Ambiguity] = []
    moved_without_sidecar: list[str] = []
    paid_extraction_protected: list[str] = []
    paid_extraction_overwritten: list[str] = []
    handled_ids: set[DocId] = set()
    handled_paths: set[str] = set()

    # --- Same path: skip, refresh, or re-embed -------------------------------------------------
    for path, file in after_by_path.items():
        document = before_by_path.get(path)
        if document is None:
            continue
        sidecar = sidecar_by_document.get(path)
        sidecar_hash = sidecar.file_hash if sidecar else None

        # The sidecar is committed truth for identity; the index row is derived. If they disagree,
        # the sidecar wins, and the stale row is retired rather than silently kept.
        if sidecar is not None and sidecar.id != document.id:
            # **The displaced id is not automatically dead.** When its own sidecar has turned up
            # beside a *different* file in this same walk, the row is moving, not ending — and the
            # adoption loop below is what carries it there. Retiring it here would put a
            # `SoftDelete` and an `Adopt` for one id into a single plan, whose outcome then depends
            # on which is applied last. On a two-file name swap (`git mv a b` past each other) that
            # is exactly what happened: the later `SoftDelete` retired the row the earlier `Adopt`
            # had just moved, and the document left search silently. On a rename *chain* the same
            # bookkeeping stopped the adoption loop from ever seeing the id, and the file's sidecar
            # was re-minted under a fresh one — an id a KB has published and other KBs link to.
            #
            # Leaving the id unhandled is what lets both loops below do their jobs: adoption claims
            # it at its new path, and if no sidecar claims it anywhere the vanished-path loop still
            # retires it, which is the ordinary in-place id change this branch exists for.
            # No `document_path != path` term, deliberately: the sidecar beside `path` is the one
            # that disagrees, so the sidecar claiming `document.id` is necessarily a different one.
            # A condition that cannot be false is a condition no test can pin.
            if document.id not in claimed_by_id:
                actions.append(SoftDelete(doc_id=document.id, path=path))
                handled_ids.add(document.id)
            actions.append(
                Adopt(
                    doc_id=sidecar.id,
                    path=path,
                    content_hash=file.content_hash,
                    sidecar_hash=sidecar_hash,
                    old_path=before_by_id[sidecar.id].path if sidecar.id in before_by_id else None,
                )
            )
            handled_ids.add(sidecar.id)
            handled_paths.add(path)
            continue

        if sidecar is None and document.id in claimed_by_id:
            # **This row's identity has moved off this path, and nothing here claims it back.**
            # The file has no sidecar of its own, while the id the index records for it has turned
            # up beside a *different* file in this same walk — someone moved the sidecar. The
            # sidecar is committed truth for identity, so the id belongs at its new home and this
            # path is now a document with no id at all.
            #
            # Emitting anything for it here is what made the plan self-inconsistent: `Skip`,
            # `RefreshMetadata` or `Reembed` all assert that this path still *is* that id, while
            # the adoption loop below simultaneously carries the same id somewhere else. One id,
            # two paths, one plan. Applied in order that silently moved the row to the other path
            # and left this file with no row at all — indexed yesterday, unfindable today, `pnk
            # sync` exiting 0 with nothing recorded. `documents.path` being UNIQUE is the only
            # reason the older, unguarded code noticed at all, and it noticed by crashing.
            #
            # Emitting nothing is what makes both loops correct: adoption claims the id at its new
            # path, and this path falls through to `Mint` as the sidecar-less document it has
            # become. That mints a fresh id for a file that had one, which is a real cost — but the
            # sidecar carrying the old id is gone from beside it, and inventing an identity the
            # committed state no longer records is what this module refuses to do.
            continue

        handled_ids.add(document.id)
        handled_paths.add(path)
        hash_changed = document.content_hash != file.content_hash or document.state == DELETED
        recorded_backend = document.extraction_backend
        recorded_is_paid = recorded_backend is not None and recorded_backend in paid_backend_names
        override = force and explicit_extract

        if recorded_is_paid and not effective_is_paid and not override:
            # Decision 9's paid-protection clauses: never silently re-extract with a downgraded
            # backend, and never silently keep indexing text a changed file no longer matches.
            if hash_changed:
                assert recorded_backend is not None  # implied by recorded_is_paid
                actions.append(
                    PaidExtractionRequired(
                        doc_id=document.id, path=path, recorded_backend=recorded_backend
                    )
                )
            else:
                actions.append(Skip(doc_id=document.id, path=path))
                paid_extraction_protected.append(path)
            continue

        if recorded_is_paid and not effective_is_paid and override:
            # `--force` with an explicit free `--extract` is the one path allowed to discard paid
            # text — reported *before* the fact, since a plain Reembed is silent about what a
            # backend downgrade costs. Emitted directly, not left to fall through to the
            # hash-changed check below: an *unchanged* hash is exactly the case this whole branch
            # exists to override, so it must still produce Reembed even though nothing else here
            # would consider that file re-processable.
            paid_extraction_overwritten.append(path)
            actions.append(
                Reembed(
                    doc_id=document.id,
                    path=path,
                    content_hash=file.content_hash,
                    sidecar_hash=sidecar_hash,
                )
            )
            continue

        if not recorded_is_paid and effective_is_paid and recorded_backend is not None:
            # Free-recorded, paid-effective: stale regardless of hash — a content-hash check
            # cannot tell "the file is unchanged" from "the last extraction undersold it" either
            # way (decision 9).
            actions.append(
                Reembed(
                    doc_id=document.id,
                    path=path,
                    content_hash=file.content_hash,
                    sidecar_hash=sidecar_hash,
                )
            )
            continue

        if hash_changed:
            actions.append(
                Reembed(
                    doc_id=document.id,
                    path=path,
                    content_hash=file.content_hash,
                    sidecar_hash=sidecar_hash,
                )
            )
        elif document.sidecar_hash != sidecar_hash:
            actions.append(
                RefreshMetadata(doc_id=document.id, path=path, sidecar_hash=sidecar_hash)
            )
        else:
            actions.append(Skip(doc_id=document.id, path=path))

    # --- New paths carrying a sidecar id we already know: adoption (this covers rename+edit) -----
    for path, file in after_by_path.items():
        if path in handled_paths:
            continue
        sidecar = sidecar_by_document.get(path)
        if sidecar is None:
            continue
        known = before_by_id.get(sidecar.id)
        if known is not None and known.id in handled_ids:
            continue
        actions.append(
            Adopt(
                doc_id=sidecar.id,
                path=path,
                content_hash=file.content_hash,
                sidecar_hash=sidecar.file_hash,
                old_path=known.path if known is not None else None,
            )
        )
        handled_paths.add(path)
        handled_ids.add(sidecar.id)

    # --- Vanished paths: rename by content, ambiguity, or soft delete ---------------------------
    unclaimed = [file for path, file in after_by_path.items() if path not in handled_paths]
    by_hash: dict[str, list[WalkedFile]] = {}
    for file in unclaimed:
        by_hash.setdefault(file.content_hash, []).append(file)

    for document in before.documents:
        if document.id in handled_ids or document.state == DELETED:
            continue
        candidates = [
            file
            for file in by_hash.get(document.content_hash, [])
            if file.path not in handled_paths
        ]

        if len(candidates) == 1:
            file = candidates[0]
            sidecar = sidecar_by_document.get(file.path)
            actions.append(
                Rename(
                    doc_id=document.id,
                    old_path=document.path,
                    path=file.path,
                    content_hash=file.content_hash,
                    sidecar_hash=sidecar.file_hash if sidecar else None,
                )
            )
            handled_paths.add(file.path)
            handled_ids.add(document.id)
            continue

        if len(candidates) > 1:
            # Prefer a candidate whose own sidecar already carries this id — that is the one piece
            # of evidence strong enough to break the tie. Otherwise do not guess: attaching an id
            # to the wrong duplicate silently redirects every inbound link.
            preferred = next(
                (
                    file
                    for file in candidates
                    if (sidecar := sidecar_by_document.get(file.path)) is not None
                    and sidecar.id == document.id
                ),
                None,
            )
            if preferred is not None:
                actions.append(
                    Rename(
                        doc_id=document.id,
                        old_path=document.path,
                        path=preferred.path,
                        content_hash=preferred.content_hash,
                        sidecar_hash=sidecar_by_document[preferred.path].file_hash,
                    )
                )
                handled_paths.add(preferred.path)
                handled_ids.add(document.id)
                continue

            ambiguities.append(
                Ambiguity(
                    old_doc_id=document.id,
                    old_path=document.path,
                    candidates=tuple(sorted(file.path for file in candidates)),
                )
            )

        actions.append(SoftDelete(doc_id=document.id, path=document.path))
        handled_ids.add(document.id)
        if document.path not in after_by_path:
            moved_without_sidecar.append(document.path)

    # --- Everything still unclaimed is new ------------------------------------------------------
    for path, file in after_by_path.items():
        if path in handled_paths:
            continue
        actions.append(Mint(path=path, content_hash=file.content_hash))

    return PairingResult(
        actions=tuple(_order_for_path_availability(actions, before_by_path)),
        ambiguities=tuple(ambiguities),
        orphaned_sidecars=_orphans(after),
        moved_without_sidecar=tuple(sorted(moved_without_sidecar)),
        paid_extraction_protected=tuple(sorted(paid_extraction_protected)),
        paid_extraction_overwritten=tuple(sorted(paid_extraction_overwritten)),
    )


#: The actions that write `documents.path`, and therefore the ones a `UNIQUE` violation can reach.
#: `Skip`, `RefreshMetadata` and `Reembed` update a row at the path it already has, so they can
#: never collide and are never reordered.
_WRITERS = (Adopt, Rename, Mint)


def _target(action: Action) -> str | None:
    """The path this action writes a row at, or `None` if it writes no path."""
    return action.path if isinstance(action, _WRITERS) else None


def _vacates(action: Action) -> str | None:
    """The path this action frees for someone else, or `None`.

    A move frees the path it came from. A `SoftDelete` frees the path it retires — not because the
    row goes away (it keeps its path, marked `deleted`) but because `sync`'s write guard deletes a
    *retired* row holding a path a different id now wants. That guard is scoped to
    `state = 'deleted'` deliberately, so the retirement genuinely has to happen first.

    **Omitting `SoftDelete` here was the first draft and it was wrong in the dangerous direction.**
    The same-path loop above emits `SoftDelete(old id)` then `Adopt(sidecar id)` at one path; with
    nothing recorded as freeing it, that pair reads as a dependency on an action that does not
    exist, and the ordering pass would have reported an already-working plan as unorderable.
    """
    match action:
        case Adopt(old_path=old) | Rename(old_path=old):
            return old
        case SoftDelete(path=path):
            return path
        case _:
            return None


def _order_for_path_availability(
    actions: list[Action], before_by_path: Mapping[str, IndexedDocument]
) -> list[Action]:
    """Reorder so no action writes a path an *active* row still holds — S16/S19.

    **`documents.path` is `UNIQUE`, and this function is the only thing that makes a rename chain
    applicable.** `pair()` builds its list by walking paths in sorted order, which is a fine order
    for deciding *what* each file is and an arbitrary one for deciding *when* to write it. Renaming
    `a → b` while `b → c` therefore emitted `Adopt(b)` before the `Adopt(c)` that frees `b`: an
    order the database rejects, for a walk where a valid order plainly exists. A chain of three
    came out in exactly reverse.

    What that cost, measured on 0.30.2 and reproduced on `main` 20260826: `pnk sync` exiting 1 on a
    raw `sqlite3.IntegrityError` traceback with no remedy and no ledger row, `pnk search` answering
    from a path that no longer exists on disk, and `pnk doctor` reporting every row `OK` — including
    `failures: none recorded`.

    **A cycle is a different class, it is deferred, and this function deliberately leaves it
    exactly as it was.** Swapping two names has no applicable order at all — whichever moves first
    writes onto a path the other still holds — and resolving it needs a temporary path this pure
    function has no way to create. So the cyclic actions keep their order **relative to each other**
    and still fail at the first write, exactly as they do on 0.30.2 — the *outcome* is untouched.
    They are appended after the actions that could be ordered rather than left where they were,
    which is the one thing about a mixed plan that does change, and is stated because an earlier
    version of this sentence claimed otherwise.

    **Refusing the cycle here was written, tested and backed out, and the reason is worth keeping.**
    Raising from `pair()` would be tidier — nothing is applied, so nothing is half-applied — but it
    deletes three committed guards that only exist while a cycle still produces a plan:
    `test_a_name_swap_never_retires_an_id_the_same_plan_adopts`,
    `test_a_three_way_rename_cycle_adopts_every_id_and_retires_none` and
    `tests/test_sync.py::test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row`. That
    last one pins the silent-loss shape S2 exists to prevent — *no live document loses its row* —
    and it can only observe that by watching the plan be applied and fail. Whether the cycle should
    refuse cleanly is a decision about behaviour, not an implementation detail of this ordering fix.

    Stable: an action moves only when something forces it to, so every plan that was already
    applicable comes out in the order `pair()` built it.
    """
    frees: dict[str, int] = {}
    for index, action in enumerate(actions):
        vacated = _vacates(action)
        if vacated is not None:
            frees.setdefault(vacated, index)

    blocked_by: dict[int, set[int]] = {}
    blocks: dict[int, set[int]] = {}
    for index, action in enumerate(actions):
        target = _target(action)
        if target is None:
            continue
        held = before_by_path.get(target)
        # `DELETED` rows impose no order: `sync`'s write guard removes a retired row holding the
        # path. Only a live row under another id has to move out of the way first.
        if held is None or held.state != ACTIVE:
            continue
        if getattr(action, "doc_id", None) == held.id:
            continue
        freed_by = frees.get(target)
        # Nothing in this plan frees the path. That is a genuine collision rather than an ordering
        # problem, and reordering cannot help — it is left to fail where it already did, because
        # inventing a refusal here would be a claim about a state no walk has been shown to produce.
        if freed_by is None or freed_by == index:
            continue
        blocked_by.setdefault(index, set()).add(freed_by)
        blocks.setdefault(freed_by, set()).add(index)

    if not blocked_by:
        return actions

    # Kahn's algorithm, always taking the lowest original index among the ready actions, so the
    # result is the input order with the minimum disturbance the constraints require.
    #
    # **A heap, because the obvious list is quadratic.** The first version kept `ready` as a list
    # and did `ready.pop(0)` plus `ready = sorted([*ready, *newly])` every iteration — both O(n) per
    # emitted action, so O(n²) over the plan, and the whole plan goes through here as soon as *one*
    # action is constrained. Measured before the change: 0.08 s for 5 000 actions, 4.9 s for 40 000,
    # 46 s for 120 000. `heapq` pops the same lowest index and yields the same order, so this is the
    # queue and not the algorithm.
    remaining = {index: set(deps) for index, deps in blocked_by.items()}
    ordered: list[Action] = []
    ready = [index for index in range(len(actions)) if index not in remaining]
    heapq.heapify(ready)
    while ready:
        index = heapq.heappop(ready)
        ordered.append(actions[index])
        for dependent in sorted(blocks.get(index, ())):
            deps = remaining.get(dependent)
            if deps is None:
                continue
            deps.discard(index)
            if not deps:
                del remaining[dependent]
                heapq.heappush(ready, dependent)

    # Whatever is left could not be emitted: every one of them is still waiting on another one of
    # them, which is a cycle. They keep their order **relative to each other** and are appended
    # after everything that could be ordered.
    #
    # **They are NOT left in place, and an earlier version of this comment said they were.** Two
    # reviewers found it separately. The distinction matters only for a plan holding a cycle *and*
    # other actions: those others now come first. It changes nothing about the outcome — a swap
    # still fails at its first write, as it does in 0.30.2 — but "unchanged behaviour" was a claim
    # about the list, and the list does change.
    ordered.extend(actions[index] for index in sorted(remaining))
    return ordered


def _orphans(after: WalkSnapshot) -> tuple[str, ...]:
    """Sidecars whose document is gone. Reported, never deleted — that needs `--prune` (§6.4)."""
    documents = {file.path for file in after.files}
    return tuple(
        sorted(sidecar.path for sidecar in after.sidecars if sidecar.document_path not in documents)
    )


def _reject_duplicate_ids(sidecars: Sequence[WalkedSidecar]) -> None:
    by_id: dict[DocId, list[str]] = {}
    for sidecar in sidecars:
        by_id.setdefault(sidecar.id, []).append(sidecar.path)
    duplicates = {str(doc_id): sorted(paths) for doc_id, paths in by_id.items() if len(paths) > 1}
    if duplicates:
        raise DuplicateIdsError(duplicates)


def describe(result: PairingResult) -> Mapping[str, int]:
    """Counts by action kind — what `pnk sync` prints, and what tests assert against."""
    counts: dict[str, int] = {}
    for action in result.actions:
        counts[type(action).__name__] = counts.get(type(action).__name__, 0) + 1
    return counts


def actions_of[T](result: PairingResult, kind: type[T]) -> list[T]:
    return [action for action in result.actions if isinstance(action, kind)]


def hash_of(files: Iterable[WalkedFile]) -> dict[str, str]:
    return {file.path: file.content_hash for file in files}


_ = field  # dataclasses.field is re-exported for callers building snapshots in tests
