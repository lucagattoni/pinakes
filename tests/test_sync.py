"""`pnk sync` end to end, against a real index and a fake backend."""

import contextlib
import itertools
import shutil
import sqlite3
import subprocess
import time
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
import yaml
from conftest import pdf_extraction_runnable

from pinakes import search, store
from pinakes.chunk import PREFIX_SEPARATOR
from pinakes.embed import EmbeddingBackend, ModelInfo, Vectors
from pinakes.errors import DuplicateIdsError, ManifestError, SyncError
from pinakes.extract import (
    ExtractedText,
    ExtractionContext,
    ExtractorEntry,
    register_extractor,
    unregister_extractor,
)
from pinakes.ids import mint_doc_id
from pinakes.manifest import Manifest, load
from pinakes.sidecar import SIDECAR_SUFFIX, Sidecar
from pinakes.sync import (
    MAX_PROBED_PER_ROOT,
    SyncOptions,
    SyncReport,
    _is_path_still_held,  # pyright: ignore[reportPrivateUsage]
    sync,
    walk_document_paths,
)

DIM = 8


class FakeBackend:
    """Deterministic and instant: sync's behaviour is what is under test, not a model's."""

    def embed(self, texts: Sequence[str]) -> Vectors:
        listed = list(texts)
        if not listed:
            return np.zeros((0, DIM), dtype=np.float32)
        return np.ascontiguousarray(
            np.vstack([np.full(DIM, (len(text) % 7) / 7.0, dtype=np.float32) for text in listed]),
            dtype=np.float32,
        )

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def info(self) -> ModelInfo:
        return ModelInfo("fake", "fake-model", None, DIM, 512)


def fake_factory(manifest: Manifest, offline: bool) -> EmbeddingBackend:
    return FakeBackend()


@pytest.fixture
def kb(tmp_path: Path) -> Path:
    root = tmp_path / "kb"
    (root / "docs").mkdir(parents=True)
    (root / "pinakes.toml").write_text(
        "\n".join(
            [
                "[kb]",
                'name = "test"',
                'id = "01KYCJ8ZVMBJDB4FKRJRNYS5DT"',
                "",
                "[sources]",
                'roots = ["docs/"]',
                'include = ["**/*.md"]',
                "",
                "[embedding]",
                'provider = "fake"',
                'model = "fake-model"',
                f"dim = {DIM}",
                "",
                "[chunking]",
                "max_tokens = 40",
                "overlap = 4",
            ]
        ),
        encoding="utf-8",
    )
    return root


class _FakePaidExtractor:
    """A working *paid* extractor, standing in for `claude-vision` — whose own loader is a
    permanent I7b stub that always raises (`test_extract.py`'s own
    `test_claude_vision_stub_names_its_own_landing_increment`), so it cannot drive an actual
    free-to-paid re-embed end to end. Deterministic and instant, like `FakeBackend` above; the
    point under test is I5's backend bookkeeping, not a real paid call."""

    def extract(self, path: Path, ctx: ExtractionContext) -> ExtractedText:
        text = "Paid extraction output.\n"
        return ExtractedText(text=text, page_spans=((0, len(text)),))


@pytest.fixture
def fake_paid() -> Iterator[str]:
    """Registers a second, real paid backend for the duration of one test — unregistered again on
    teardown regardless of how the test exits, so it never leaks into another test's
    `registered_extractors()`/`paid_backend_names()`."""
    name = "test-paid"
    entry = ExtractorEntry(
        load=_FakePaidExtractor,
        fingerprint_inputs=lambda _model=None: {"backend": name},
        paid=True,
    )
    register_extractor(name, entry)
    try:
        yield name
    finally:
        unregister_extractor(name)


def write(kb: Path, name: str, text: str) -> Path:
    path = kb / "docs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(kb: Path, *, extract: str | None = None, **options: Any) -> SyncReport:
    """`**options` is `Any` rather than `bool` because `SyncOptions` carries non-bool fields
    (`ask`, `operation_id`); pyright checks a `**kwargs` annotation against *every* parameter."""
    return sync(
        load(kb),
        options=SyncOptions(extract=extract, **options),
        backend_factory=fake_factory,
        now="20260725 16:00",
    )


def index(kb: Path) -> list[dict[str, object]]:
    """Read every document row and close immediately.

    Deliberately not a generator: an earlier version was one, and a caller using `next()` left the
    connection open, which kept `-wal`/`-shm` alive and made a rebuild assertion fail for a reason
    that had nothing to do with the rebuild.
    """
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        return [dict(row) for row in connection.execute("SELECT * FROM documents ORDER BY path")]
    finally:
        connection.close()


def chunks_for(kb: Path, path: str) -> int:
    """How many chunks one document still has. Connection closed before returning, as `index` is."""
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        row = connection.execute(
            "SELECT count(*) FROM chunks WHERE doc_id = (SELECT id FROM documents WHERE path = ?)",
            (path,),
        ).fetchone()
        return int(row[0])
    finally:
        connection.close()


def meta_of(kb: Path) -> dict[str, str]:
    """The index's `meta` table, connection closed before returning — same reason as `index`."""
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        return store.get_meta(connection)
    finally:
        connection.close()


def test_first_sync_mints_sidecars_indexes_and_embeds(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nThe first document about retrieval.\n")
    write(kb, "b.md", "# Beta\n\nThe second document about ranking.\n")

    report = run(kb)
    assert report.embedded == 2
    assert report.ok

    documents = list(index(kb))
    assert [doc["path"] for doc in documents] == ["docs/a.md", "docs/b.md"]
    assert all(doc["state"] == "active" for doc in documents)

    for name in ("a.md", "b.md"):
        sidecar = kb / "docs" / f"{name}{SIDECAR_SUFFIX}"
        assert sidecar.is_file()
        assert yaml.safe_load(sidecar.read_text(encoding="utf-8"))["id"]

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        chunk_ids, matrix = store.load_vectors(connection, dim=DIM)
        assert len(chunk_ids) == matrix.shape[0] > 0
        hits = connection.execute(
            "SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'retrieval'"
        ).fetchone()[0]
        assert hits == 1
    finally:
        connection.close()


def test_progress_callback_is_driven_once_per_action_in_order(kb: Path) -> None:
    """Item 6: `sync()` does no I/O of its own — `ask` is the existing precedent — so a caller that
    wants to show progress on a multi-hour, CPU-only run supplies a callback rather than `sync()`
    probing `sys.stdout.isatty()` itself. `(done, total)` must count every action `pair()` produced
    (including a `Skip`, since "300 documents ran" is what a corpus this size looks like even when
    most of them are unchanged), start at 1, and never exceed `total`."""
    write(kb, "a.md", "# A\n\nSome text.\n")
    write(kb, "b.md", "# B\n\nMore text.\n")
    write(kb, "c.md", "# C\n\nYet more text.\n")

    calls: list[tuple[int, int]] = []

    def record(done: int, total: int) -> None:
        calls.append((done, total))

    report = run(kb, progress=record)
    assert report.ok

    assert calls, "a non-empty sync must drive the callback at least once"
    totals = {total for _, total in calls}
    assert totals == {3}, "total must be stable across the whole run"
    assert [done for done, _ in calls] == [1, 2, 3], "done must count up from 1 with no gaps"


def test_progress_defaults_to_none_and_is_never_called(kb: Path) -> None:
    """The default changes nothing about a run that supplies no callback — every other test in
    this file calls `run()` this way, so this is the coverage-of-intent record for that default."""
    write(kb, "a.md", "# A\n\nSome text.\n")
    report = run(kb)  # progress=None, implicitly
    assert report.ok


def test_a_second_sync_changes_nothing(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nStable text.\n")
    run(kb)
    report = run(kb)
    assert (report.skipped, report.embedded) == (1, 0)


def test_editing_a_document_re_embeds_it_and_keeps_the_id(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nOriginal.\n")
    run(kb)
    before = index(kb)[0]["id"]

    write(kb, "a.md", "# Alpha\n\nRewritten entirely.\n")
    report = run(kb)

    assert report.embedded == 1
    after = index(kb)[0]
    assert after["id"] == before
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        assert (
            connection.execute(
                "SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'Original'"
            ).fetchone()[0]
            == 0
        )
    finally:
        connection.close()


def test_a_sidecar_only_edit_refreshes_metadata_without_re_embedding(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nText.\n")
    run(kb)
    sidecar = kb / "docs" / f"a.md{SIDECAR_SUFFIX}"
    data = yaml.safe_load(sidecar.read_text(encoding="utf-8"))
    data["tags"] = ["physics"]
    sidecar.write_text(yaml.safe_dump(data), encoding="utf-8")

    report = run(kb)
    assert (report.refreshed, report.embedded) == (1, 0)
    assert "physics" in str(index(kb)[0]["metadata"])


def test_deleting_a_document_soft_deletes_it_and_removes_its_chunks(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nDisappearing text.\n")
    run(kb)
    (kb / "docs" / "a.md").unlink()

    report = run(kb)
    assert report.deleted == 1
    assert index(kb)[0]["state"] == "deleted"

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        assert (
            connection.execute(
                "SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'Disappearing'"
            ).fetchone()[0]
            == 0
        )
    finally:
        connection.close()
    assert (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").exists()  # never removed automatically


def test_a_rename_keeps_the_id_because_the_sidecar_travels(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nTravelling text.\n")
    run(kb)
    original = index(kb)[0]["id"]

    (kb / "docs" / "a.md").rename(kb / "docs" / "moved.md")
    (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").rename(kb / "docs" / f"moved.md{SIDECAR_SUFFIX}")

    run(kb)
    live = [doc for doc in index(kb) if doc["state"] == "active"]
    assert len(live) == 1
    assert live[0]["id"] == original
    assert live[0]["path"] == "docs/moved.md"


def test_one_broken_document_does_not_block_the_others(kb: Path) -> None:
    """§6.4: per-document transactions; the run continues and the exit code still says it failed."""
    write(kb, "good.md", "# Good\n\nFine text.\n")
    (kb / "docs" / "bad.md").write_bytes(b"\xff\xfe not valid utf-8 \xff")

    report = run(kb)
    assert not report.ok
    assert len(report.failures) == 1
    assert "bad.md" in report.failures[0][0]
    assert [doc["path"] for doc in index(kb)] == ["docs/good.md"]

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        assert connection.execute("SELECT count(*) FROM failures").fetchone()[0] == 1
    finally:
        connection.close()


def test_a_pdf_fails_at_extraction_but_does_not_block_the_rest(kb: Path) -> None:
    """§6.4 isolation extended to extraction: no adapter yet, and says so once, not per path."""
    manifest_path = kb / "pinakes.toml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            'include = ["**/*.md"]', 'include = ["**/*.md", "**/*.pdf"]'
        ),
        encoding="utf-8",
    )
    write(kb, "good.md", "# Good\n\nFine text.\n")
    (kb / "docs" / "a.pdf").write_bytes(b"not a real pdf, and it must not matter")
    (kb / "docs" / "b.pdf").write_bytes(b"neither is this one")

    report = run(kb)
    assert not report.ok
    assert {path for path, _, _ in report.failures} == {"docs/a.pdf", "docs/b.pdf"}
    assert [doc["path"] for doc in index(kb)] == ["docs/good.md"]

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        stages = {
            str(row["stage"]) for row in connection.execute("SELECT DISTINCT stage FROM failures")
        }
        assert stages == {"extract"}
    finally:
        connection.close()

    remedy = report.failures[0][2]
    assert remedy  # every failure here is a PinakesError; none should carry an empty remedy
    printed = report.lines()
    assert printed.count(remedy) == 1  # once, not once per failing path


def test_sidecars_are_never_ingested_as_documents(kb: Path) -> None:
    """An include pattern must not turn a document's own metadata into a document."""
    write(kb, "a.md", "# Alpha\n\nText.\n")
    run(kb)
    manifest_path = kb / "pinakes.toml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            'include = ["**/*.md"]', 'include = ["**/*.md", "**/*.yaml"]'
        ),
        encoding="utf-8",
    )
    run(kb)
    assert [doc["path"] for doc in index(kb)] == ["docs/a.md"]


def test_rebuild_replaces_the_index_and_keeps_the_ledger(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nText.\n")
    run(kb)
    ledger = kb / ".pinakes" / "ledger.jsonl"
    ledger.write_text('{"spend": 1}\n', encoding="utf-8")
    original = index(kb)[0]["id"]

    run(kb, rebuild=True)

    # Checked *before* anything reads the index: opening even a read-only connection to a WAL
    # database creates `-shm`/`-wal` itself, so a later read would mask what the swap left behind.
    state = kb / ".pinakes"
    assert not (state / "index.db.new").exists()
    assert not list(state.glob("index.db-wal"))
    assert not list(state.glob("index.db-shm"))

    assert ledger.read_text(encoding="utf-8") == '{"spend": 1}\n'
    assert index(kb)[0]["id"] == original  # the sidecar carried the id through


def test_sidecars_only_never_touches_the_index(kb: Path) -> None:
    write(kb, "a.md", "# Alpha\n\nText.\n")
    report = run(kb, sidecars_only=True)

    assert report.minted == 1
    assert (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").is_file()
    assert not (kb / ".pinakes" / "index.db").exists()


def test_index_only_never_writes_into_docs(kb: Path) -> None:
    """The post-commit half: the tree it just committed must stay clean (§6.3)."""
    write(kb, "a.md", "# Alpha\n\nText.\n")
    report = run(kb, index_only=True)

    assert report.embedded == 1
    assert not (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").exists()
    assert list(index(kb))


def recorded_failures(kb: Path) -> list[tuple[str, str]]:
    """`(path, stage)` for every row in the `failures` table, which no test read before S7."""
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        return [
            (str(row["path"]), str(row["stage"]))
            for row in connection.execute("SELECT path, stage FROM failures ORDER BY id")
        ]
    finally:
        connection.close()


def test_repairing_a_document_clears_its_failure(kb: Path) -> None:
    """Sweep S7, and the normal user path: the ledger never cleared, not even on repair.

    `pnk doctor` went on reporting "N recorded: docs/keep.md" with "These documents are not
    searchable" after the document had been repaired, re-indexed and was demonstrably searchable
    — so the remedy it printed, *fix them and re-run `pnk sync`*, was exactly what the user had
    just done, and doing it again changed nothing, forever.
    """
    write(kb, "keep.md", "# Keep\n\nText.\n")
    assert run(kb).embedded == 1
    sidecar = kb / "docs" / f"keep.md{SIDECAR_SUFFIX}"
    good = sidecar.read_text(encoding="utf-8")

    sidecar.write_text(BAD_LINK, encoding="utf-8")
    assert run(kb).failures
    assert recorded_failures(kb) == [("docs/keep.md", "index")]

    sidecar.write_text(good, encoding="utf-8")
    report = run(kb)

    assert report.ok
    assert recorded_failures(kb) == []


def test_a_document_that_keeps_failing_keeps_one_row_not_one_per_sync(kb: Path) -> None:
    """The other half of "never clears": it also never de-duplicated.

    Three syncs of one broken document left three rows, so `doctor` reported a count of *attempts*
    while calling them documents. The pre-attempt clear alone does not fix this — `_apply` rolls
    back before recording a failure, and the rollback takes the clear with it, which is why
    `store.record_failure` replaces rather than appends.
    """
    write(kb, "keep.md", "# Keep\n\nText.\n")
    (kb / "docs" / f"keep.md{SIDECAR_SUFFIX}").write_text(BAD_LINK, encoding="utf-8")

    for _ in range(3):
        run(kb)

    assert recorded_failures(kb) == [("docs/keep.md", "index")]


def test_deleting_a_failed_document_clears_its_failure(kb: Path) -> None:
    """A row naming a path that is gone can never be resolved by anything the user does.

    Left behind, `doctor` warned about `docs/keep.md` in a KB with zero active documents, and the
    only remedy it offered was to fix a file that no longer existed.
    """
    write(kb, "keep.md", "# Keep\n\nText.\n")
    run(kb)
    (kb / "docs" / f"keep.md{SIDECAR_SUFFIX}").write_text(BAD_LINK, encoding="utf-8")
    run(kb)
    assert recorded_failures(kb)

    (kb / "docs" / "keep.md").unlink()
    (kb / "docs" / f"keep.md{SIDECAR_SUFFIX}").unlink()
    run(kb)

    assert recorded_failures(kb) == []


def test_an_ordinary_deletion_prints_nothing_about_a_move(kb: Path) -> None:
    """Sweep S6, through the sentence a user actually reads.

    `test_pairing.py` pins the predicate; this pins the rendering, and the two are separable —
    the gate could be right in `pairing.py` while `SyncReport.lines()` went on printing the old
    sentence, and nothing asserted that sentence at all before this. Deleting a document properly
    means the file and its sidecar together, which is what `pnk sync` itself tells you to do.
    """
    write(kb, "a.md", "# Alpha\n\nText.\n")
    run(kb)
    (kb / "docs" / "a.md").unlink()
    (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").unlink()

    report = run(kb)

    assert report.deleted == 1
    assert report.source_gone_sidecar_kept == ()
    printed = "\n".join(report.lines())
    assert "source gone" not in printed
    assert "minted" not in printed


def test_a_source_gone_with_its_sidecar_kept_says_so_without_claiming_a_mint(kb: Path) -> None:
    """The other half of S6: the hint still fires, and no longer asserts what it cannot know.

    Only the file is deleted, so the sidecar is orphaned and D-37 option E's gate passes — but
    nothing is minted, because the other half of a move need not arrive in the same run. The old
    sentence ended "so a new id was minted", which is false here and was false on every ordinary
    deletion too.
    """
    write(kb, "a.md", "# Alpha\n\nText.\n")
    run(kb)
    (kb / "docs" / "a.md").unlink()

    report = run(kb)

    assert report.embedded == 0  # nothing was minted, and the sentence must not say otherwise
    line = next(line for line in report.lines() if line.startswith("source gone, sidecar kept:"))
    assert "docs/a.md" in line
    assert "minted" not in line
    assert "move the sidecar with it" in line


def test_sidecars_only_with_index_only_is_refused(kb: Path) -> None:
    """Sweep S5. The two flags are halves of one sync and each names what the other does.

    Unrefused, `--sidecars-only` simply won: it returns before the index is opened and
    `_write_missing_sidecars` never reads `index_only`, so the run wrote into `docs/` — the one
    thing `--index-only` exists to promise it will not do — and reported "0 indexed, 0 renamed, 0
    metadata-only, 0 unchanged, 0 removed" at exit 0. Every number in that line was truthful; the
    line was still a lie, because the count of files written into `docs/` is not one of them.

    Asserting the *tree* and not only the exception is the point: a refusal that raised after the
    sidecar was already on disk would satisfy a `pytest.raises` and leave the defect exactly where
    it was.
    """
    write(kb, "a.md", "# Alpha\n\nText.\n")

    with pytest.raises(SyncError) as caught:
        run(kb, sidecars_only=True, index_only=True)

    assert "two halves of one sync" in caught.value.message
    assert "on its own" in caught.value.remedy
    assert not (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").exists()
    assert not (kb / ".pinakes" / "index.db").exists()


def test_stage_limits_to_staged_files_and_adds_the_sidecars(kb: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=kb, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=kb, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=kb, check=True)
    write(kb, "staged.md", "# Staged\n\nText.\n")
    write(kb, "unstaged.md", "# Unstaged\n\nText.\n")
    subprocess.run(["git", "add", "docs/staged.md"], cwd=kb, check=True)

    report = run(kb, sidecars_only=True, stage=True)

    assert report.minted == 1
    assert (kb / "docs" / f"staged.md{SIDECAR_SUFFIX}").is_file()
    assert not (kb / "docs" / f"unstaged.md{SIDECAR_SUFFIX}").exists()

    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=kb,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert f"docs/staged.md{SIDECAR_SUFFIX}" in staged


def test_duplicate_ids_stop_the_sync(kb: Path) -> None:
    write(kb, "a.md", "# A\n\nText.\n")
    write(kb, "b.md", "# B\n\nOther text.\n")
    shared = mint_doc_id()
    for name in ("a.md", "b.md"):
        (kb / "docs" / f"{name}{SIDECAR_SUFFIX}").write_text(
            yaml.safe_dump({"id": shared}), encoding="utf-8"
        )

    with pytest.raises(DuplicateIdsError):
        run(kb)


def test_a_busy_lock_reports_and_exits_cleanly(kb: Path) -> None:
    import json
    import os
    import socket

    state = kb / ".pinakes"
    state.mkdir(parents=True, exist_ok=True)
    (state / "sync.lock").write_text(
        json.dumps({"pid": os.getpid(), "host": socket.gethostname(), "started": "20260725 16:00"}),
        encoding="utf-8",
    )

    report = run(kb)
    assert report.busy


def test_a_real_sync_stamps_utc_not_local_under_a_non_utc_timezone(
    monkeypatch: pytest.MonkeyPatch, kb: Path
) -> None:
    """Item 2, `sync.py:709`. `lock.py` already stamps `datetime.now(UTC)`; before this fix
    `sync.py`'s own `stamp` — written into `meta['built_at']`, every sidecar's `created`, and every
    failure's `happened` — was `datetime.now()`, local. Two timestamps in the identical
    `%Y%m%d %H:%M` format with no timezone marker, read from different clocks: in a zone ahead of
    UTC, a lock taken seconds ago would read as hours old next to a `sync.py` stamp from the same
    moment — the evidence a user weighs before `pnk sync --force-unlock`.

    `TZ` is set explicitly (never inherited): this fails under any non-UTC zone before the fix and
    passes only once the clock is UTC, which is why running CI in UTC alone could never have caught
    it. `now=None` here, deliberately — every other test in this file passes a fixed `now=` string
    specifically to bypass the real clock, which is exactly what must not happen here.
    """
    write(kb, "a.md", "# A\n\nSome text.\n")
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")  # UTC+14 — the largest UTC offset that exists
    time.tzset()
    try:
        before = datetime.now(UTC)
        # Not `run()`: its helper hardcodes `now="20260725 16:00"` for every other test in this
        # file precisely to bypass the real clock — the one thing this test must not do.
        sync(load(kb), options=SyncOptions(), backend_factory=fake_factory)
        after = datetime.now(UTC)
    finally:
        monkeypatch.delenv("TZ", raising=False)
        time.tzset()

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        built_at = store.get_meta(connection)["built_at"]
    finally:
        connection.close()

    recorded = datetime.strptime(built_at, "%Y%m%d %H:%M").replace(tzinfo=UTC)
    # Minute-granularity format: a same-run window can only be missed by whole hours, which is
    # exactly the size a local stamp under UTC+14 would be off by, and a UTC one cannot be.
    assert before.replace(second=0, microsecond=0) - timedelta(minutes=1) <= recorded
    assert recorded <= after.replace(second=0, microsecond=0) + timedelta(minutes=1)


def test_the_index_records_the_tier_that_ran(monkeypatch: pytest.MonkeyPatch, kb: Path) -> None:
    """Two parts, and only the second one discriminates.

    **Part 1** is the concrete shipped fact a reader can check without running anything: the NumPy
    tier is the only one built, so a KB on the default `auto` records `numpy`. It holds whether
    `meta` was written from the resolver or from a re-hardcoded literal — which is exactly why it
    is not the whole test.

    **Part 2** injects a resolver returning a string no tier has and asserts `meta` moved with it.
    That is the half that goes red if `sync.py` writes the literal again. It is a test against an
    **injected value, not against a second tier**: with one tier there is nothing else to compare,
    so the honest claim today is "`meta` is written from the resolver's return", not "`meta`
    records the tier that ran" — the name this test keeps for the property it will assert once a
    second tier exists to discriminate.

    Asserting `meta == resolve_tier(manifest)` instead would put one function on both sides and
    hold even when the resolver is wrong; that is the tautology this replaces.
    """
    write(kb, "a.md", "# A\n\nSome text.\n")
    run(kb)
    assert meta_of(kb)["vector_tier"] == "numpy"

    def injected(_manifest: Manifest) -> str:
        return "injected-tier"

    # Patched on the module `sync` calls *through* — which is why it calls through one rather than
    # importing the name.
    monkeypatch.setattr(search, "resolve_tier", injected)
    run(kb, rebuild=True)
    assert meta_of(kb)["vector_tier"] == "injected-tier"


@pytest.mark.skipif(not pdf_extraction_runnable(), reason="pinakes[pdf] not installed")
def test_estimate_only_stamps_utc_not_local_under_a_non_utc_timezone(
    monkeypatch: pytest.MonkeyPatch, kb: Path
) -> None:
    """Item 2, `sync.py:808` (`_estimate_only`'s own clock, used to check `prices.toml` staleness).
    Isolated from the network and from real pricing — `default_transport`/`estimate_only`
    (`extract.claude`) and `estimate_document` (`budget.estimate`) are faked — so the only thing
    under test is the timestamp `_estimate_only` computes itself; `page_count` still runs for real
    against a genuine one-page fixture (`pinakes[pdf]`, hence the skip marker), since faking it
    would leave nothing to walk.
    """
    manifest_path = kb / "pinakes.toml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            'include = ["**/*.md"]', 'include = ["**/*.md", "**/*.pdf"]'
        )
        + '\n[extraction]\nbackend = "claude-vision"\nmodel = "claude-opus-5"\n',
        encoding="utf-8",
    )
    (kb / "docs" / "report.pdf").write_bytes(
        (Path(__file__).parent / "pdf-corpus" / "baseline-1p.pdf").read_bytes()
    )

    captured: dict[str, str] = {}

    def fake_estimate_document(**kwargs: Any) -> Any:
        captured["now"] = str(kwargs["now"])
        return SimpleNamespace(total_eur=Decimal("0.0000"))

    def fake_default_transport() -> object:
        return object()

    def fake_estimate_only(*args: object, **kwargs: object) -> tuple[int, int]:
        return (100, 1)

    monkeypatch.setattr("pinakes.extract.claude.default_transport", fake_default_transport)
    monkeypatch.setattr("pinakes.extract.claude.estimate_only", fake_estimate_only)
    monkeypatch.setattr("pinakes.budget.estimate.estimate_document", fake_estimate_document)

    monkeypatch.setenv("TZ", "Pacific/Kiritimati")  # UTC+14 — the largest UTC offset that exists
    time.tzset()
    try:
        before = datetime.now(UTC)
        run(kb, estimate_only=True)
        after = datetime.now(UTC)
    finally:
        monkeypatch.delenv("TZ", raising=False)
        time.tzset()

    assert "now" in captured, "estimate_document must have been reached for a matched PDF"
    recorded = datetime.strptime(captured["now"], "%Y%m%d %H:%M").replace(tzinfo=UTC)
    assert before.replace(second=0, microsecond=0) - timedelta(minutes=1) <= recorded
    assert recorded <= after.replace(second=0, microsecond=0) + timedelta(minutes=1)


def _add_pdf_support(kb: Path) -> None:
    """`fake` needs no `pypdfium2` and ignores file content, so these tests exercise the cache's
    wiring into `_index_document` without depending on which optional extras are installed."""
    manifest_path = kb / "pinakes.toml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            'include = ["**/*.md"]', 'include = ["**/*.md", "**/*.pdf"]'
        )
        + '\n[extraction]\nbackend = "fake"\n',
        encoding="utf-8",
    )


def _cache_files(kb: Path) -> list[Path]:
    return sorted((kb / ".pinakes" / "cache" / "extract").glob("*.json"))


def test_a_pdf_sync_writes_a_cache_entry_and_a_rebuild_reuses_it(kb: Path) -> None:
    """A second *plain* sync of an unchanged PDF never reaches `_index_document` at all — pairing's
    own `Skip` (content_hash unchanged) returns before the cache is ever consulted, so it would
    prove nothing about the cache to just call `run(kb)` twice. `--rebuild` is what actually forces
    every document back through `_index_document` regardless of pairing's skip (`before` is read
    from a brand-new, empty database, so nothing looks unchanged to it) — exactly the scenario the
    cache exists for (docs/DESIGN.md §6.3): re-processing the whole KB without re-paying to
    extract a single unchanged document."""
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder - the fake backend ignores this")

    first = run(kb)
    assert first.embedded == 1 and first.skipped == 0
    entries = _cache_files(kb)
    assert len(entries) == 1
    first_mtime = entries[0].stat().st_mtime_ns

    second = run(kb, rebuild=True)
    assert second.embedded == 1 and second.skipped == 0  # really went through _index_document again
    entries_again = _cache_files(kb)
    assert len(entries_again) == 1
    assert entries_again[0] == entries[0]
    assert entries_again[0].stat().st_mtime_ns == first_mtime  # unchanged: a hit, never a re-write


def test_a_fully_successful_sync_evicts_a_deleted_documents_cache_entry(kb: Path) -> None:
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
    run(kb)
    assert len(_cache_files(kb)) == 1

    (kb / "docs" / "a.pdf").unlink()
    (kb / "docs" / f"a.pdf{SIDECAR_SUFFIX}").unlink()  # no hash match => soft delete, not a rename
    report = run(kb)
    assert report.ok
    assert _cache_files(kb) == []


def test_deleting_one_of_two_same_content_documents_keeps_the_shared_cache_entry(
    kb: Path,
) -> None:
    """Eviction keys on `content_hash`, not on any one document — as long as *some* active
    document still claims it, the shared entry must survive deleting the others."""
    _add_pdf_support(kb)
    same_bytes = b"identical content shared by two documents"
    (kb / "docs" / "a.pdf").write_bytes(same_bytes)
    (kb / "docs" / "b.pdf").write_bytes(same_bytes)
    run(kb)
    assert len(_cache_files(kb)) == 1  # one content_hash, one entry, regardless of path count

    (kb / "docs" / "b.pdf").unlink()
    (kb / "docs" / f"b.pdf{SIDECAR_SUFFIX}").unlink()
    report = run(kb)
    assert report.ok
    assert len(_cache_files(kb)) == 1  # a.pdf still claims the same content_hash


def test_clear_cache_preserves_the_ledger(kb: Path) -> None:
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
    run(kb)
    assert len(_cache_files(kb)) == 1

    ledger = kb / ".pinakes" / "ledger.jsonl"
    ledger.write_text('{"spend": 1}\n', encoding="utf-8")

    report = sync(load(kb), options=SyncOptions(clear_cache=True, yes=True))

    assert report.cache_cleared == 1
    assert _cache_files(kb) == []
    assert ledger.read_text(encoding="utf-8") == '{"spend": 1}\n'


def test_clear_cache_without_yes_and_without_a_tty_aborts(kb: Path) -> None:
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
    run(kb)
    assert len(_cache_files(kb)) == 1

    report = sync(load(kb), options=SyncOptions(clear_cache=True))

    assert report.cache_clear_aborted
    assert report.cache_pending_entries == 1
    assert len(_cache_files(kb)) == 1  # nothing removed


def test_clear_cache_on_an_empty_cache_is_a_no_op_not_a_prompt(kb: Path) -> None:
    report = sync(load(kb), options=SyncOptions(clear_cache=True))
    assert report.cache_cleared == 0
    assert not report.cache_clear_aborted
    assert report.ok


# --- I5: decision 9's six backend-drift cases, end to end ------------------------------------


def _paid_index(kb: Path, fake_paid: str) -> None:
    """Every case but `free_then_paid` starts from an already paid-indexed PDF."""
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
    first = run(kb, extract=fake_paid)
    assert first.embedded == 1
    assert index(kb)[0]["extraction_backend"] == fake_paid


@pytest.mark.parametrize(
    "case_id",
    [
        "free_then_paid",
        "protected_from_a_free_run",
        "protected_from_rebuild",
        "protected_from_an_explicit_free_extract",
        "force_overwrites",
        "changed_hash",
    ],
)
def test_backend_drift(kb: Path, fake_paid: str, case_id: str) -> None:
    """Decision 9's six named cases (plans/20260727_1543-v0.2.md), addressed as "
    "`test_backend_drift[<case_id>]`.

    `pairing.py`'s own tests already cover the decision table in isolation; this is the same six
    rules wired all the way through a real `sync()` call — the actual DB row, the actual sidecar,
    the actual report the CLI would print.
    """
    if case_id == "free_then_paid":
        _add_pdf_support(kb)
        (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
        first = run(kb)
        assert first.embedded == 1
        assert index(kb)[0]["extraction_backend"] == "fake"

        report = run(kb, extract=fake_paid)
        assert report.embedded == 1
        assert index(kb)[0]["extraction_backend"] == fake_paid
        return

    _paid_index(kb, fake_paid)

    if case_id == "protected_from_a_free_run":
        report = run(kb)  # the manifest's own [extraction] backend = "fake" — a hook-style run
        assert (report.skipped, report.embedded) == (1, 0)
        assert report.paid_extraction_protected == ("docs/a.pdf",)
    elif case_id == "protected_from_rebuild":
        report = run(kb, rebuild=True)
        assert report.ok
        assert report.paid_extraction_protected == ("docs/a.pdf",)
    elif case_id == "protected_from_an_explicit_free_extract":
        report = run(kb, extract="pypdfium2")  # explicit free backend, no --force
        assert (report.skipped, report.embedded) == (1, 0)
        assert report.paid_extraction_protected == ("docs/a.pdf",)
    elif case_id == "force_overwrites":
        report = run(kb, extract="fake", force=True)
        assert report.embedded == 1
        assert report.paid_extraction_overwritten == ("docs/a.pdf",)
        printed = report.lines()
        assert any("docs/a.pdf" in line and "discarded" in line for line in printed)
        assert index(kb)[0]["extraction_backend"] == "fake"
        return
    elif case_id == "changed_hash":
        (kb / "docs" / "a.pdf").write_bytes(b"changed, invalidating the paid extraction")
        report = run(kb)  # free effective backend
        assert not report.ok
        assert len(report.failures) == 1
        path, _error, remedy = report.failures[0]
        assert path == "docs/a.pdf"
        assert fake_paid in remedy
        assert index(kb)[0]["extraction_backend"] == fake_paid  # untouched, not silently downgraded
        return

    after = index(kb)[0]
    assert after["extraction_backend"] == fake_paid  # in every remaining case, still untouched


def test_force_alone_without_an_explicit_extract_does_not_override(
    kb: Path, fake_paid: str
) -> None:
    """`--force` protects nothing by itself — this is the manifest-default-backend counterpart to
    `pairing.py`'s own unit test of the same rule."""
    _paid_index(kb, fake_paid)

    report = run(kb, force=True)  # no explicit --extract
    assert (report.skipped, report.embedded) == (1, 0)
    assert report.paid_extraction_protected == ("docs/a.pdf",)
    assert index(kb)[0]["extraction_backend"] == fake_paid


def test_force_overwrite_clears_the_stale_sidecar_provenance(kb: Path, fake_paid: str) -> None:
    """After `--force` downgrades a paid extraction to free, the sidecar must stop claiming a paid
    extraction it no longer describes — otherwise a later sync (or a different clone reading the
    same committed sidecar) would wrongly believe the file is still protected."""
    _paid_index(kb, fake_paid)
    sidecar_file = kb / "docs" / f"a.pdf{SIDECAR_SUFFIX}"
    before = yaml.safe_load(sidecar_file.read_text(encoding="utf-8"))
    assert before["provenance"]["extraction"]["backend"] == fake_paid

    run(kb, extract="fake", force=True)

    after = yaml.safe_load(sidecar_file.read_text(encoding="utf-8"))
    assert "extraction" not in after.get("provenance", {})


# --- I5: rebuild-provenance -------------------------------------------------------------------


def test_a_rebuild_preserves_paid_provenance(kb: Path, fake_paid: str) -> None:
    """`--rebuild` under a free manifest must leave a paid-extracted document untouched: the same
    id, the same backend/fingerprint, and its chunks and vectors carried over rather than
    re-embedded — the sidecar's `provenance.extraction` is what makes this possible even though
    `--rebuild`'s own `before` snapshot is read from a brand-new, empty database (decision 11)."""
    _paid_index(kb, fake_paid)
    before = index(kb)[0]

    report = run(kb, rebuild=True)

    assert report.ok
    after = index(kb)[0]
    assert after["id"] == before["id"]
    assert after["extraction_backend"] == fake_paid
    assert after["extraction_fingerprint"] == before["extraction_fingerprint"]

    sidecar = yaml.safe_load((kb / "docs" / f"a.pdf{SIDECAR_SUFFIX}").read_text(encoding="utf-8"))
    assert sidecar["provenance"]["extraction"]["backend"] == fake_paid

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        chunk_ids, matrix = store.load_vectors(connection, dim=DIM)
        assert len(chunk_ids) == matrix.shape[0] > 0  # the embeddings really did carry over
        hits = connection.execute(
            "SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH 'Paid'"
        ).fetchone()[0]
        assert hits == 1  # the FTS index was rebuilt from the copied-forward chunk, not skipped
    finally:
        connection.close()


class _FakePaidLongExtractor:
    """A paid extractor whose output is long enough that `max_tokens` changes the chunk count.

    `_FakePaidExtractor` returns one short line, which chunks to exactly one chunk under every
    setting — so a re-chunk and a copy-forward are indistinguishable through it. D-15 is a claim
    about chunk *boundaries* moving, and it needs a document that has some."""

    def extract(self, path: Path, ctx: ExtractionContext) -> ExtractedText:
        text = "".join(f"Paid extraction sentence number {n} of the document.\n" for n in range(60))
        return ExtractedText(text=text, page_spans=((0, len(text)),))


@pytest.fixture
def fake_paid_long() -> Iterator[str]:
    name = "test-paid-long"
    entry = ExtractorEntry(
        load=_FakePaidLongExtractor,
        fingerprint_inputs=lambda _model=None: {"backend": name},
        paid=True,
    )
    register_extractor(name, entry)
    try:
        yield name
    finally:
        unregister_extractor(name)


def _chunk_count(kb: Path) -> int:
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        return int(connection.execute("SELECT count(*) FROM chunks").fetchone()[0])
    finally:
        connection.close()


def test_a_rebuild_rechunks_a_protected_paid_document_from_the_cache(
    kb: Path, fake_paid_long: str
) -> None:
    """D-15, the warm half. A `[chunking]` edit reaches a paid document on `--rebuild`, for free.

    The chunks used to be copied verbatim, so `headings`, `max_tokens` and `overlap` never reached
    a paid-extracted document while `set_meta` stamped the current settings over the whole index —
    an index claiming a chunking it did not have. The item stood open believing the fix needed the
    extracted text and so cost money to obtain.

    **It does not: the extraction cache lives under `.pinakes/` and `--rebuild` does not clear it**
    — rebuild builds `index.db.new` beside the old one and swaps. So the text is read back with
    `cache.peek`, which never calls an extractor, and the document is re-chunked like any other.

    Asserted on the chunk *count*, which is what `max_tokens` actually moves; asserting the meta
    key alone would pass against code that recorded the settings without applying them, which is
    the exact defect being closed."""
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
    assert run(kb, extract=fake_paid_long).embedded == 1
    before = _chunk_count(kb)
    assert before > 1, "the fixture must produce a document with boundaries to move"
    assert _cache_files(kb), "the cache must be warm for this half of the decision"

    _set_chunking(kb, max_tokens="20")
    report = run(kb, rebuild=True)

    assert report.ok, report.failures
    assert _chunk_count(kb) > before, "a smaller max_tokens must produce more chunks"
    assert report.chunking_not_applied == (), "nothing was carried forward unchunked"
    assert index(kb)[0]["extraction_backend"] == fake_paid_long, "the extraction is still paid"

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        meta = store.get_meta(connection)
    finally:
        connection.close()
    assert "chunking_exceptions" not in meta, "a fully re-chunked index has no exceptions"


def test_a_rebuild_with_a_cold_cache_keeps_the_chunks_and_says_the_index_is_inhomogeneous(
    kb: Path, fake_paid_long: str
) -> None:
    """D-15, the cold half — and the one that decides what honesty costs.

    With no cache entry the extracted text is gone, and getting it back means paying. `--rebuild`
    is the remedy `pnk doctor` prints, so a rebuild that can spend is not a remedy: the document
    keeps its previous chunks, and **the index records that the settings stamped over it are not
    true of every document in it**. That is the half the old code got wrong silently.

    Three assertions because three things could each be dropped independently: the chunks survive,
    the run names the document, and the *index itself* carries the exception — a report line is
    gone the moment the terminal scrolls, and `pnk doctor` reads the index."""
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
    assert run(kb, extract=fake_paid_long).embedded == 1
    before = _chunk_count(kb)

    cleared = sync(load(kb), options=SyncOptions(clear_cache=True, clear_cache_paid=True, yes=True))
    assert cleared.cache_cleared == 1
    assert _cache_files(kb) == []

    _set_chunking(kb, max_tokens="20")
    report = run(kb, rebuild=True)

    assert report.ok, report.failures
    assert _chunk_count(kb) == before, "with no cached text the chunks must be carried forward"
    assert report.chunking_not_applied == ("docs/a.pdf",)
    assert "kept their previous chunking" in "\n".join(report.lines())

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        meta = store.get_meta(connection)
    finally:
        connection.close()
    assert meta["chunking_exceptions"] == "1"


def test_neither_rebuild_path_ever_calls_the_paid_extractor(kb: Path) -> None:
    """**The promise the whole decision rests on: a rebuild never spends.**

    Both halves of D-15 are defensible only because neither pays. The warm half reads the text back
    with `cache.peek`, which never calls an extractor; the cold half keeps the old chunks rather
    than re-extracting. Nothing above asserts that — the sibling tests check chunk counts and meta
    keys, and a re-chunk that quietly re-extracted would satisfy every one of them while charging
    the user.

    Counted rather than reasoned about, because `--rebuild` is the remedy `pnk doctor` prints: a
    remedy that can spend is not a remedy, and that is a property of the code rather than of the
    docstring claiming it."""
    calls: list[Path] = []

    class _Counting:
        def extract(self, path: Path, ctx: ExtractionContext) -> ExtractedText:
            calls.append(path)
            text = "".join(f"Paid line {n}.\n" for n in range(60))
            return ExtractedText(text=text, page_spans=((0, len(text)),))

    name = "test-paid-counting"
    register_extractor(
        name,
        ExtractorEntry(
            load=_Counting, fingerprint_inputs=lambda _model=None: {"backend": name}, paid=True
        ),
    )
    try:
        _add_pdf_support(kb)
        (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
        assert run(kb, extract=name).embedded == 1
        assert len(calls) == 1, "the first extraction is the one the user paid for"

        _set_chunking(kb, max_tokens="20")
        assert run(kb, rebuild=True).ok
        assert len(calls) == 1, "the warm rebuild re-extracted instead of reading its cache"

        cleared = sync(
            load(kb), options=SyncOptions(clear_cache=True, clear_cache_paid=True, yes=True)
        )
        assert cleared.cache_cleared == 1
        _set_chunking(kb, max_tokens="30")
        assert run(kb, rebuild=True).ok
        assert len(calls) == 1, "the cold rebuild paid to extract rather than carrying forward"
    finally:
        unregister_extractor(name)


def test_a_rebuild_after_clear_cache_still_preserves_it(kb: Path, fake_paid: str) -> None:
    """The sequence a cache-based answer would have failed (plan text): if paid-extraction
    protection depended on `extract/cache.py` still holding the entry, `--clear-cache` immediately
    before `--rebuild` would empty it first, and the rebuild would either wrongly demand paying
    again or — worse — silently fall back to a free re-extraction. `_paid_rebuild_survivors` reads
    the *old index* being replaced instead, which `--clear-cache` never touches, so this sequence
    must come out identical to a rebuild with a warm cache."""
    _paid_index(kb, fake_paid)
    before = index(kb)[0]
    assert _cache_files(kb)  # confirm there is something for --clear-cache to actually remove

    # `--yes` alone is not enough now that the entry really is paid: I7b makes sync record an
    # `operation_id` on paid cache entries, so I6b's guard finally has real data to fire on.
    refused = sync(load(kb), options=SyncOptions(clear_cache=True, yes=True))
    assert refused.cache_clear_aborted
    assert refused.cache_pending_paid_entries == 1

    cleared = sync(load(kb), options=SyncOptions(clear_cache=True, clear_cache_paid=True, yes=True))
    assert cleared.cache_cleared == 1
    assert _cache_files(kb) == []

    report = run(kb, rebuild=True)

    assert report.ok
    assert not report.failures
    after = index(kb)[0]
    assert after["id"] == before["id"]
    assert after["extraction_backend"] == fake_paid
    assert after["extraction_fingerprint"] == before["extraction_fingerprint"]

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        chunk_ids, matrix = store.load_vectors(connection, dim=DIM)
        assert len(chunk_ids) == matrix.shape[0] > 0
    finally:
        connection.close()


def test_a_rebuild_never_lets_a_free_twin_inherit_the_paid_ones_backend(
    kb: Path, fake_paid: str
) -> None:
    """Two different documents can share one content_hash with only one of them paid: `b.pdf` is
    minted later, under a free effective backend, and its own fresh sidecar carries no recorded
    provenance yet — so it gets a normal free extraction of its own, same as any first-time PDF,
    even though `a.pdf` (identical bytes) already has a paid one. `_paid_rebuild_survivors` must
    key on (content_hash, path), not content_hash alone, or `b.pdf`'s rebuild would incorrectly
    match `a.pdf`'s entry and inherit its chunks, embeddings and paid backend label."""
    _add_pdf_support(kb)
    same_bytes = b"identical content, only one of the two copies ever paid to extract"
    (kb / "docs" / "a.pdf").write_bytes(same_bytes)
    run(kb, extract=fake_paid)

    (kb / "docs" / "b.pdf").write_bytes(same_bytes)
    second = run(kb)  # manifest's own backend stays "fake" (free) — b.pdf is a brand-new Mint
    assert second.ok
    rows_by_path = {row["path"]: row for row in index(kb)}
    assert rows_by_path["docs/a.pdf"]["extraction_backend"] == fake_paid
    assert rows_by_path["docs/b.pdf"]["extraction_backend"] == "fake"
    b_id_before = rows_by_path["docs/b.pdf"]["id"]

    report = run(kb, rebuild=True)

    assert report.ok
    assert report.paid_extraction_protected == ("docs/a.pdf",)  # b.pdf must not appear here
    after_by_path = {row["path"]: row for row in index(kb)}
    assert after_by_path["docs/a.pdf"]["extraction_backend"] == fake_paid
    assert after_by_path["docs/b.pdf"]["extraction_backend"] == "fake"  # not silently upgraded
    assert after_by_path["docs/b.pdf"]["id"] == b_id_before


# --- I5 retrospective: protection must not depend on the extraction cache existing at all -----
#
# The original design only protected a paid extraction via `pairing.py`'s "same path" comparison
# (a normal sync) or `--rebuild`'s own copy-forward. Any *other* pairing outcome — a rename, or a
# document adopted some other way — fell through to `_extract_for_index`'s cache lookup alone,
# which cannot tell "just renamed" or "just cloned" apart from "content actually changed": all
# three look identical to it as a cache miss. These four tests each construct one specific gap
# an adversarial review caught, and were confirmed to fail without their corresponding fix.


def test_a_rename_after_clear_cache_does_not_falsely_claim_content_changed(
    kb: Path, fake_paid: str
) -> None:
    """A rename (sidecar travels) reaches pairing's `Adopt`/`Rename` branch, never the same-path
    comparison a normal unchanged sync uses — so protection has to survive `--clear-cache` here
    too, not only during `--rebuild`."""
    _paid_index(kb, fake_paid)
    sync(load(kb), options=SyncOptions(clear_cache=True, yes=True))

    (kb / "docs" / "a.pdf").rename(kb / "docs" / "b.pdf")
    (kb / "docs" / f"a.pdf{SIDECAR_SUFFIX}").rename(kb / "docs" / f"b.pdf{SIDECAR_SUFFIX}")

    report = run(kb)  # manifest's own backend stays "fake" (free)
    assert report.ok
    rows = {row["path"]: row for row in index(kb)}
    assert rows["docs/b.pdf"]["extraction_backend"] == fake_paid


def test_a_fresh_clone_with_no_local_cache_or_index_fails_honestly_not_falsely(
    kb: Path, fake_paid: str
) -> None:
    """Simulates cloning a KB whose paid PDFs were extracted on a different machine: `docs/` (with
    its committed sidecar) survives, `.pinakes/` (index and cache both, per DESIGN.md's own "a
    freshly cloned KB has no index at all") does not. The file is byte-identical; the failure must
    say so, never claim the content changed."""
    _paid_index(kb, fake_paid)
    shutil.rmtree(kb / ".pinakes")

    report = run(kb)
    assert not report.ok
    assert len(report.failures) == 1
    path, error, remedy = report.failures[0]
    assert path == "docs/a.pdf"
    assert "PaidExtractionUnavailableError" in error
    assert "PaidExtractionRequiredError" not in error
    assert "unchanged" in error
    assert fake_paid in remedy


def test_a_retired_paid_document_restored_unchanged_is_not_told_its_content_changed(
    kb: Path, fake_paid: str
) -> None:
    """S18, and the sibling of the fresh-clone case above: the file is byte-identical, so the
    failure must not say it changed.

    Deleting a document retires its row and **drops its chunks with it**, so restoring the file
    genuinely does need a paid re-extraction — the refusal is right and only its reason was wrong.
    It said "but its content changed" and the content had not moved a byte, so the remedy asked the
    user to pay for a change that never happened.

    Both files go and both come back, which is what restoring from a backup looks like: deleting
    only the PDF strands its sidecar and takes a different branch entirely.
    """
    _paid_index(kb, fake_paid)
    pdf = kb / "docs" / "a.pdf"
    side = kb / "docs" / f"a.pdf{SIDECAR_SUFFIX}"
    kept, kept_side = pdf.read_bytes(), side.read_bytes()

    pdf.unlink()
    side.unlink()
    assert run(kb).ok, "the retirement itself is not a failure"

    pdf.write_bytes(kept)
    side.write_bytes(kept_side)
    report = run(kb)  # the manifest's own backend is free

    assert not report.ok
    assert len(report.failures) == 1
    path, error, remedy = report.failures[0]
    assert path == "docs/a.pdf"
    assert "content changed" not in error, "the file came back byte-identical"
    assert "unchanged" in error
    assert "retired" in error
    assert fake_paid in remedy


def test_a_rebuild_keeps_a_changed_paid_document_searchable_but_flagged(
    kb: Path, fake_paid: str
) -> None:
    """A paid-recorded document whose content changed must not simply vanish from a rebuilt
    index — a normal sync leaves its old text searchable in the identical situation (decision 14),
    and `--rebuild` must match that rather than silently dropping it the moment the whole index
    happens to be under reconstruction."""
    _paid_index(kb, fake_paid)
    before = index(kb)[0]

    (kb / "docs" / "a.pdf").write_bytes(b"changed, invalidating the paid extraction")
    report = run(kb, rebuild=True)

    assert not report.ok
    assert len(report.failures) == 1
    path, error, remedy = report.failures[0]
    assert path == "docs/a.pdf"
    assert "kept at its last paid extraction" in error
    assert fake_paid in remedy

    after = index(kb)[0]
    assert after["id"] == before["id"]
    assert after["extraction_backend"] == fake_paid
    assert after["content_hash"] == before["content_hash"]  # the OLD hash, not the changed one

    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        chunk_ids, matrix = store.load_vectors(connection, dim=DIM)
        assert len(chunk_ids) == matrix.shape[0] > 0  # still searchable, not dropped
    finally:
        connection.close()


def test_three_consecutive_paid_syncs_settle_after_the_first(kb: Path, fake_paid: str) -> None:
    """A fresh paid-provenance write must recompute `sidecar_hash` from the file it just wrote —
    otherwise the very next sync sees a sidecar hash it did not expect and spends a whole extra
    cycle on a spurious `RefreshMetadata` before settling."""
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")

    first = run(kb, extract=fake_paid)
    second = run(kb, extract=fake_paid)
    third = run(kb, extract=fake_paid)

    assert (first.embedded, first.refreshed, first.skipped) == (1, 0, 0)
    assert (second.embedded, second.refreshed, second.skipped) == (0, 0, 1)
    assert (third.embedded, third.refreshed, third.skipped) == (0, 0, 1)


# --- unmatched files: a file skipped for want of a glob must say so (0.2.2) -------------------


def test_a_pdf_with_no_matching_glob_is_named_not_silently_skipped(kb: Path) -> None:
    """The defect this fixes: `pnk init` stamps no `**/*.pdf`, so a PDF dropped into a fresh KB
    matched nothing and sync reported `0 indexed` explaining nothing — v0.2's headline feature
    silently off, with the output giving no hint why."""
    (kb / "docs" / "report.pdf").write_bytes(b"%PDF-1.4\nnot really a pdf\n")

    report = run(kb)

    assert report.embedded == 0
    assert report.unmatched == ("docs/report.pdf",)
    line = next(line for line in report.lines() if "matched no `include` pattern" in line)
    assert '"**/*.pdf"' in line  # the exact glob to add, not a vague pointer
    assert "`exclude`" in line  # and the way to silence it instead


def test_unmatched_files_are_reported_even_when_others_indexed_fine(kb: Path) -> None:
    """The mixed case is the dangerous one: a sync that indexes the Markdown and drops the PDFs
    reports success, so nothing prompts the user to look. Silence here is worse than silence on an
    empty KB, which at least invites investigation."""
    write(kb, "notes.md", "# Notes\n\nIndexed fine.\n")
    (kb / "docs" / "report.pdf").write_bytes(b"%PDF-1.4\n")

    report = run(kb)

    assert report.embedded == 1
    assert report.ok  # not a failure — the run succeeded, it just was not complete
    assert report.unmatched == ("docs/report.pdf",)


def test_binaries_are_never_reported_because_the_remedy_would_not_work(kb: Path) -> None:
    """A file pinakes could not read however the manifest is configured must stay silent: every
    non-PDF source goes through `read_text(encoding="utf-8")`, so telling the user to add
    `"**/*.png"` would hand them a remedy that produces a `UnicodeDecodeError` failure row when
    followed. A wrong hint is worse than none."""
    (kb / "docs" / "diagram.png").write_bytes(bytes.fromhex("89504e470d0a1a0a") + b"\x00" * 64)
    (kb / "docs" / "utf16.txt").write_text("hello", encoding="utf-16")

    report = run(kb)

    assert report.unmatched == ()
    assert not any("matched no `include` pattern" in line for line in report.lines())


def test_an_unknown_text_format_is_reported_since_it_indexes_as_text(kb: Path) -> None:
    """`chunk.source_type` falls back to `"text"` for any unrecognised suffix, so `.rst`/`.org`/
    `.tex` genuinely index once a glob matches them. A fixed extension allowlist would have stayed
    silent here; deciding by decodability does not."""
    (kb / "docs" / "guide.rst").write_text("Title\n=====\n\nBody.\n", encoding="utf-8")

    report = run(kb)

    assert report.unmatched == ("docs/guide.rst",)


def test_excluded_and_hidden_files_are_never_reported(kb: Path) -> None:
    """`exclude` is the user having already said "not this" — repeating it back as a suggestion
    would be noise. Dotted segments (`.git/`, `.DS_Store`) are never the corpus."""
    manifest = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "pinakes.toml").write_text(
        manifest.replace(
            'include = ["**/*.md"]', 'include = ["**/*.md"]\nexclude = ["**/vendor/**"]'
        ),
        encoding="utf-8",
    )
    (kb / "docs" / "vendor").mkdir()
    (kb / "docs" / "vendor" / "third-party.rst").write_text("Vendored.\n", encoding="utf-8")
    (kb / "docs" / ".hidden").mkdir()
    (kb / "docs" / ".hidden" / "secret.rst").write_text("Hidden.\n", encoding="utf-8")
    (kb / "docs" / ".DS_Store").write_bytes(b"\x00\x01")

    report = run(kb)

    assert report.unmatched == ()


def test_a_matched_file_is_not_also_reported_as_unmatched(kb: Path) -> None:
    """The two sets must be disjoint — a document that indexed fine appearing in the "you have no
    glob for this" line would be a plain contradiction."""
    write(kb, "notes.md", "# Notes\n\nBody.\n")

    report = run(kb)

    assert report.embedded == 1
    assert report.unmatched == ()


def test_the_unmatched_line_groups_by_extension_and_caps_the_list(kb: Path) -> None:
    """By extension, not by path: twelve unindexed PDFs are one missing glob, and printing twelve
    paths would obscure that. Capped so a KB with many stray formats still prints one readable
    line."""
    for index_ in range(4):
        (kb / "docs" / f"doc{index_}.rst").write_text("Body.\n", encoding="utf-8")
    (kb / "docs" / "a.org").write_text("Body.\n", encoding="utf-8")
    (kb / "docs" / "b.tex").write_text("Body.\n", encoding="utf-8")
    (kb / "docs" / "c.adoc").write_text("Body.\n", encoding="utf-8")

    report = run(kb)

    line = next(line for line in report.lines() if "matched no `include` pattern" in line)
    assert "7 file(s)" in line
    assert ".rst (4)" in line  # commonest first
    assert '"**/*.rst"' in line  # and it is the one the remedy names
    assert "and 1 more" in line  # 4 distinct extensions, 3 shown


def test_a_cjk_document_is_reported_not_judged_unreadable(kb: Path) -> None:
    """The probe reads a fixed 8 KB prefix, and a fixed byte cut lands mid-character in any script
    whose codepoints are multi-byte — roughly two times in three for CJK. Decoded non-incrementally,
    the split trailing character raised `UnicodeDecodeError`, `_indexable` returned False, and every
    non-English corpus got this feature's silence handed straight back."""
    (kb / "docs" / "notes.rst").write_text(
        "中" * 5000, encoding="utf-8"
    )  # ~15 KB, valid throughout

    report = run(kb)

    assert report.unmatched == ("docs/notes.rst",)


@pytest.mark.parametrize("pad", [8189, 8190, 8191, 8192])
def test_the_probe_boundary_never_rejects_valid_utf8(kb: Path, pad: int) -> None:
    """Every offset where a multi-byte character can straddle the probe's last byte."""
    (kb / "docs" / "notes.rst").write_text("a" * pad + "中" * 20, encoding="utf-8")

    assert run(kb).unmatched == ("docs/notes.rst",)


def test_two_roots_never_report_a_file_the_other_root_indexed(kb: Path) -> None:
    """`matched` must be complete before anything is tested against it. Collecting unmatched files
    inside the per-root loop tested each file against a `files` the later roots had not contributed
    to yet — so a document indexed via root B was *also* reported as having no pattern, and swapping
    the two roots in the manifest made it disappear. An ordering artefact, in output whose entire
    job is to be trusted."""
    manifest = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "pinakes.toml").write_text(
        manifest.replace('roots = ["docs/"]', 'roots = ["docs/", "docs/sub/"]'), encoding="utf-8"
    )
    (kb / "docs" / "sub").mkdir()
    write(kb, "a.md", "# A\n\nBody.\n")
    (kb / "docs" / "sub" / "b.md").write_text("# B\n\nBody.\n", encoding="utf-8")

    report = run(kb)

    assert report.embedded == 2
    assert set(report.unmatched) & {doc["path"] for doc in index(kb)} == set()
    assert report.unmatched == ()


def test_root_order_does_not_change_what_is_reported(kb: Path) -> None:
    """The same KB, the same two roots, listed the other way round — identical output or the
    reporting is an artefact of manifest ordering rather than a fact about the KB."""
    manifest = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "docs" / "sub").mkdir()
    write(kb, "a.md", "# A\n\nBody.\n")
    (kb / "docs" / "sub" / "b.md").write_text("# B\n\nBody.\n", encoding="utf-8")
    (kb / "docs" / "sub" / "c.rst").write_text("Body.\n", encoding="utf-8")

    (kb / "pinakes.toml").write_text(
        manifest.replace('roots = ["docs/"]', 'roots = ["docs/", "docs/sub/"]'), encoding="utf-8"
    )
    forwards = run(kb, rebuild=True).unmatched
    (kb / "pinakes.toml").write_text(
        manifest.replace('roots = ["docs/"]', 'roots = ["docs/sub/", "docs/"]'), encoding="utf-8"
    )
    backwards = run(kb, rebuild=True).unmatched

    assert forwards == backwards == ("docs/sub/c.rst",)


def test_an_uppercase_extension_gets_a_glob_that_actually_matches_it(kb: Path) -> None:
    """`pathlib` glob is case-sensitive on POSIX whatever the filesystem does, so `"**/*.pdf"` does
    not match `Report.PDF`. Lowercasing the suffix for the hint produced a remedy that fails to fix
    the file it was printed for."""
    (kb / "docs" / "Report.PDF").write_bytes(b"%PDF-1.4\n")

    report = run(kb)

    line = next(line for line in report.lines() if "matched no `include` pattern" in line)
    assert '"**/*.PDF"' in line
    assert '"**/*.pdf"' not in line


def test_an_unmatched_pdf_names_the_extra_it_will_still_need(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Adding the glob on a core-only install turns every PDF from silently skipped into loudly
    failed — the same trap `_indexable` refuses to set for images, so the hint carries both halves.

    The extractor is forced *missing* rather than left to the environment: this repo's CI runs a
    three-leg extras matrix, so whether `pypdfium2` imports differs per leg, and a test that only
    asserts "the line agrees with the flag" agrees with itself under every leg while proving
    nothing. Verified: that earlier shape survived deleting the whole feature.

    Forced through `is_backend_installed`, which is what `_missing_pdf_extra` probes since I7a —
    it asks the registry whether the backend's module is importable rather than loading it, so a
    paid backend cannot import its client here (gate 4)."""
    import pinakes.sync as sync_module

    def not_installed(_backend: str) -> bool:
        return False

    monkeypatch.setattr(sync_module, "is_backend_installed", not_installed)
    (kb / "docs" / "report.pdf").write_bytes(b"%PDF-1.4\n")

    report = run(kb)

    assert report.unmatched_pdf_extra == "pdf"
    line = next(line for line in report.lines() if "matched no `include` pattern" in line)
    assert 'uv add "pinakes[pdf]"' in line


def test_no_pdf_means_no_extra_hint(kb: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Telling someone to install a PDF extractor when nothing they own is a PDF is noise in a line
    competing for the attention of a person who was just told something got skipped. Forced missing
    for the same reason as above, so the assertion holds under every extras leg."""
    import pinakes.sync as sync_module

    def not_installed(_backend: str) -> bool:
        return False

    monkeypatch.setattr(sync_module, "is_backend_installed", not_installed)
    (kb / "docs" / "guide.rst").write_text("Body.\n", encoding="utf-8")

    report = run(kb)

    assert report.unmatched_pdf_extra is None
    assert "pinakes[pdf]" not in next(
        line for line in report.lines() if "matched no `include` pattern" in line
    )


def test_a_sidecar_is_never_reported_as_an_unindexed_document(kb: Path) -> None:
    """Load-bearing and previously untested: sidecars are `.pnk.yaml`, which no include glob
    matches, so without the guard every document's own metadata would be reported back as a file
    needing a pattern — on every sync after the first."""
    write(kb, "a.md", "# A\n\nBody.\n")
    run(kb)  # mints docs/a.md.pnk.yaml

    second = run(kb)

    assert (kb / "docs" / "a.md.pnk.yaml").exists()
    assert second.unmatched == ()


def test_a_dotted_root_is_walked_normally(kb: Path) -> None:
    """The dotted-segment test is relative to the *source root*, not the KB root — otherwise a KB
    whose root is itself dotted (`~/.config/mykb/`) or a root named `.notes/` would suppress its own
    entire corpus."""
    manifest = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "pinakes.toml").write_text(
        manifest.replace('roots = ["docs/"]', 'roots = [".notes/"]'), encoding="utf-8"
    )
    (kb / ".notes").mkdir()
    (kb / ".notes" / "guide.rst").write_text("Body.\n", encoding="utf-8")

    assert run(kb).unmatched == (".notes/guide.rst",)


def test_probing_stops_at_the_cap_and_says_the_count_is_partial(kb: Path) -> None:
    """A `node_modules/` under a root is thousands of `open()` calls per sync — a network round trip
    each on an SMB or NFS mount — to produce advice nobody wants. Bounded, and the truncation is
    stated rather than silently capping the number."""
    for index_ in range(MAX_PROBED_PER_ROOT + 50):
        (kb / "docs" / f"f{index_}.rst").write_text("Body.\n", encoding="utf-8")

    report = run(kb)

    assert report.unmatched_truncated
    assert len(report.unmatched) == MAX_PROBED_PER_ROOT
    assert f"{MAX_PROBED_PER_ROOT}+ file(s)" in next(
        line for line in report.lines() if "matched no `include` pattern" in line
    )


def test_and_n_more_counts_extensions_not_files(kb: Path) -> None:
    """The cap shows three extensions; the residue is a count of *extensions*, and the wording has
    to say so. With 40 files across 5 extensions, "and 2 more" read as files makes the numbers in
    one line contradict each other."""
    for suffix, count in (("aa", 10), ("bb", 9), ("cc", 8), ("dd", 7), ("ee", 6)):
        for index_ in range(count):
            (kb / "docs" / f"{suffix}{index_}.{suffix}").write_text("Body.\n", encoding="utf-8")

    line = next(line for line in run(kb).lines() if "matched no `include` pattern" in line)

    assert "40 file(s)" in line
    assert "and 2 more extension(s)" in line


def test_quiet_still_prints_the_unmatched_line(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`-q` prints only problems, and a file skipped for want of a glob is one. The git hooks
    `docs/GUIDE.md` recommends run `pnk sync --quiet`, so suppressing it under `-q` would leave the
    project's own documented workflow as the single place this fix never reaches."""
    from pinakes.cli import print_sync_report

    (kb / "docs" / "report.pdf").write_bytes(b"%PDF-1.4\n")
    report = run(kb)
    capsys.readouterr()

    print_sync_report(report, quiet=True)

    captured = capsys.readouterr()
    assert "matched no `include` pattern" in captured.err
    assert "0 indexed" not in (captured.out + captured.err)  # the counts stay suppressed


# --- A sidecar that will not parse is never replaced by a freshly minted one -------------------
#
# Found 20260729 by hand-authoring a corpus with one malformed link URI. `walk_sources` drops an
# unreadable sidecar so the walk continues, which is right — but the document then looks like one
# that was never ingested, and the mint path wrote a fresh sidecar *over* the file still holding
# its permanent ULID. `pnk sync` reported success with no failures, and `pnk doctor` afterwards
# reported every sidecar readable and no duplicate ids, because the evidence had been destroyed by
# the thing that destroyed the id.
#
# Parametrised over two unrelated parse failures on purpose: the defect is "any PinakesError from
# read_sidecar reaches the mint path", and a test written only against a bad link would pass again
# the moment link parsing moved.

BAD_LINK = """\
id: 01KYCPXAJWWAK83Z0KBK6Y3NHR
title: kept
created: 20260725 15:19
links:
- to: pnk://01KYCPTN72ZXC1DDWS6054MGZV/01KYD000000000000ABSENTDOC
  rel: related
"""

BAD_ID = """\
id: not-a-ulid
title: kept
created: 20260725 15:19
"""

UNREADABLE = pytest.mark.parametrize(
    ("shape", "content"), [("a malformed link URI", BAD_LINK), ("a malformed id", BAD_ID)]
)


@UNREADABLE
def test_an_unreadable_sidecar_is_never_overwritten(kb: Path, shape: str, content: str) -> None:
    write(kb, "keep.md", "# Keep\n\nThis document already has an id on disk.\n")
    sidecar = kb / "docs" / f"keep.md{SIDECAR_SUFFIX}"
    sidecar.write_text(content, encoding="utf-8")

    report = run(kb)

    assert sidecar.read_text(encoding="utf-8") == content, f"{shape}: the sidecar was rewritten"
    assert not report.ok
    assert [path for path, _, _ in report.failures] == ["docs/keep.md"]
    _, error, remedy = report.failures[0]
    assert "will not parse" in error
    assert "not indexed" in remedy
    # Documents the outcome rather than guarding it: the index stays empty under a mutated guard
    # too, because `_read_sidecar_for` on the indexing path refuses independently. Kept because it
    # is the user-visible consequence, not because it can detect the defect.
    assert [document["path"] for document in index(kb)] == []


@UNREADABLE
def test_an_unreadable_sidecar_does_not_stop_the_other_documents(
    kb: Path, shape: str, content: str
) -> None:
    """The walk-continues property the original `except PinakesError: continue` was protecting.
    Preserving the file must not cost it."""
    write(kb, "keep.md", "# Keep\n\nBroken sidecar.\n")
    (kb / "docs" / f"keep.md{SIDECAR_SUFFIX}").write_text(content, encoding="utf-8")
    write(kb, "fine.md", "# Fine\n\nNo sidecar yet.\n")

    report = run(kb)

    assert report.embedded == 1, shape
    assert [document["path"] for document in index(kb)] == ["docs/fine.md"]
    assert (kb / "docs" / f"fine.md{SIDECAR_SUFFIX}").is_file()


@UNREADABLE
def test_sidecars_only_refuses_the_unreadable_one_and_mints_the_rest(
    kb: Path, shape: str, content: str
) -> None:
    """The pre-commit path has no per-document transaction to roll back, so it records the refusal
    itself. One unparseable file must not deny every other new document an id."""
    write(kb, "keep.md", "# Keep\n\nBroken sidecar.\n")
    sidecar = kb / "docs" / f"keep.md{SIDECAR_SUFFIX}"
    sidecar.write_text(content, encoding="utf-8")
    write(kb, "fine.md", "# Fine\n\nNo sidecar yet.\n")

    report = run(kb, sidecars_only=True)

    assert sidecar.read_text(encoding="utf-8") == content, f"{shape}: the sidecar was rewritten"
    assert report.minted == 1
    assert report.sidecars_written == [f"docs/fine.md{SIDECAR_SUFFIX}"]
    assert [path for path, _, _ in report.failures] == ["docs/keep.md"]
    assert not report.ok


@UNREADABLE
def test_index_only_neither_writes_nor_indexes_a_divergent_id(
    kb: Path, shape: str, content: str
) -> None:
    """`--index-only` (the post-commit and post-merge hooks) writes no sidecar, so it can destroy
    nothing — and it does not index the document under a freshly minted id either, because the
    indexing path re-reads the same sidecar for its metadata and that read refuses.

    Deliberately asserts the *outcome* and not which guard produced it: a duplicate check inside
    `_mint` was tried here and proved undetectable by mutation, so the assertion that would have
    pinned it would have been an assertion about redundant code."""
    write(kb, "keep.md", "# Keep\n\nBroken sidecar.\n")
    sidecar = kb / "docs" / f"keep.md{SIDECAR_SUFFIX}"
    sidecar.write_text(content, encoding="utf-8")

    report = run(kb, index_only=True)

    assert sidecar.read_text(encoding="utf-8") == content, shape
    assert [path for path, _, _ in report.failures] == ["docs/keep.md"]
    assert [document["path"] for document in index(kb)] == []


@UNREADABLE
def test_breaking_a_sidecar_after_indexing_does_not_abort_the_whole_sync(
    kb: Path, shape: str, content: str
) -> None:
    """The likeliest way a user meets this: sync, hand-edit a link, sync again.

    The document's *content* is unchanged, so pairing yields `RefreshMetadata` — not `Reembed`
    (which was always inside `_apply`'s try) and not `Mint` (which the overwrite guard covers).
    That branch sits outside the try and `_refresh_metadata` re-reads the sidecar, so the error
    escaped `_apply`, the action loop and `sync()` itself: one hand-broken file aborted the whole
    corpus with no failures row, no `set_meta` and no commit.
    """
    write(kb, "keep.md", "# Keep\n\nText.\n")
    write(kb, "other.md", "# Other\n\nMore text.\n")
    assert run(kb).embedded == 2

    (kb / "docs" / f"keep.md{SIDECAR_SUFFIX}").write_text(content, encoding="utf-8")
    report = run(kb)

    assert [path for path, _, _ in report.failures] == ["docs/keep.md"], shape
    assert not report.ok
    assert [document["path"] for document in index(kb)] == ["docs/keep.md", "docs/other.md"]


@UNREADABLE
def test_a_rebuild_does_not_overwrite_an_unreadable_sidecar(
    kb: Path, shape: str, content: str
) -> None:
    """`--rebuild` starts from an empty index, so every document goes through Mint/Adopt — the most
    likely production route into the original overwrite."""
    write(kb, "keep.md", "# Keep\n\nText.\n")
    run(kb)
    sidecar = kb / "docs" / f"keep.md{SIDECAR_SUFFIX}"
    sidecar.write_text(content, encoding="utf-8")

    report = run(kb, rebuild=True)

    assert sidecar.read_text(encoding="utf-8") == content, shape
    assert [path for path, _, _ in report.failures] == ["docs/keep.md"]


def test_the_refusal_names_the_parse_error_not_merely_the_existence(kb: Path) -> None:
    """ "already exists, so a freshly minted sidecar cannot be written over it" reads like a pinakes
    bug and says nothing about the character the user mistyped. The walk had the real reason and
    had to swallow it to keep walking, so it is recovered by re-reading the one file."""
    write(kb, "keep.md", "# Keep\n\nText.\n")
    (kb / "docs" / f"keep.md{SIDECAR_SUFFIX}").write_text(BAD_LINK, encoding="utf-8")

    _, error, remedy = run(kb).failures[0]

    assert "will not parse" in error
    assert "01KYD000000000000ABSENTDOC" in error, "the offending value is not named"
    assert "not indexed" in remedy


def test_a_sidecar_that_appears_after_the_walk_asks_for_a_rerun(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A *readable* sidecar at mint time means the file arrived between the walk and now. Minting
    over it would destroy a live id, so the honest answer is "run again", not a guess — and not the
    "will not parse" message, which would be a lie about a file that parses.

    Driven by hiding the sidecars from the walk while leaving them on disk, which is what a race
    looks like from the mint path. `--rebuild` so the index starts empty and every document goes
    through Mint.
    """
    import pinakes.sync as sync_module

    write(kb, "keep.md", "# Keep\n\nText.\n")
    run(kb)  # mints a perfectly good sidecar
    real_walk = sync_module.walk_sources

    def walk_as_if_the_sidecar_arrived_late(
        manifest: Manifest,
    ) -> tuple[list[Any], list[Any], Any, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        files, _sidecars, unmatched, escaping, unreadable, unresolvable = real_walk(manifest)
        return files, [], unmatched, escaping, unreadable, unresolvable

    monkeypatch.setattr(sync_module, "walk_sources", walk_as_if_the_sidecar_arrived_late)
    report = run(kb, rebuild=True)

    _, error, remedy = report.failures[0]
    assert "appeared after the walk" in error
    assert "will not parse" not in error, "a readable file must not be reported as unparseable"
    assert "again" in remedy


def test_a_write_failure_on_the_pre_commit_path_is_recorded_not_raised(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`create` re-raises the atomic rename's own `OSError` — a read-only `docs/`, a full disk,
    EACCES — and `cli.main` handles only `PinakesError`, so a clause catching `SidecarError` alone
    surfaced a Python traceback *and* denied every remaining new document its id. That is the
    property this try exists to protect, failing in the one case it was too narrow to see."""
    import pinakes.sync as sync_module

    write(kb, "a.md", "# Alpha\n\nFirst.\n")
    write(kb, "b.md", "# Beta\n\nSecond.\n")

    real = sync_module.create_sidecar
    seen: list[Path] = []

    def flaky(path: Path, sidecar: Sidecar) -> None:
        seen.append(path)
        if len(seen) == 1:
            raise PermissionError(13, "Permission denied", str(path))
        real(path, sidecar)

    monkeypatch.setattr(sync_module, "create_sidecar", flaky)
    report = run(kb, sidecars_only=True)

    assert report.minted == 1, "the second document was denied its id by the first one's failure"
    assert [path for path, _, _ in report.failures] == ["docs/a.md"]
    assert "PermissionError" in report.failures[0][1]
    assert not report.ok


def test_an_anchored_boolean_is_indexed_as_true_not_one(kb: Path) -> None:
    """`ScalarBoolean` subclasses `int` — Python forbids subclassing `bool` — and ruamel returns
    one for any boolean carrying an **anchor or an alias**. It is JSON-encodable, so the sidecar's
    own check passes it, and it lands in the index as `1` where PyYAML wrote `true`.

    Asserted at every depth the coercion has to reach: `_metadata()` is a shallow spread, so a
    boolean nested in a mapping or a list is not touched by coercing the top level — and both the
    one-level implementation and its mutation target passed against a top-level-only fixture.
    """
    write(kb, "a.md", "# Alpha\n\nThe first document about retrieval.\n")
    run(kb)

    sidecar = kb / "docs" / f"a.md{SIDECAR_SUFFIX}"
    body = sidecar.read_text(encoding="utf-8")
    sidecar.write_text(
        body + "anchored: &flag true\naliased: *flag\nnested:\n  deep: *flag\nlisted:\n- *flag\n",
        encoding="utf-8",
    )
    run(kb)

    metadata = store.loads_metadata(str(next(iter(index(kb)))["metadata"]))

    assert metadata["anchored"] is True, "an anchored boolean must not index as 1"
    assert metadata["aliased"] is True, "...nor an alias of one"
    assert metadata["nested"] == {"deep": True}, "...nor one nested in a mapping"
    assert metadata["listed"] == [True], "...nor one inside a list"


# --- the source walk stays inside the KB (containment, both layers) ---------------------------
#
# One rule, two layers, and neither covers the other: `manifest._check_include_containment` bounds
# the walk *before* `glob` runs, and `sync.walk_sources` re-tests each candidate because a
# symlinked directory is invisible to any static check. All three defects below were measured on
# 0.7.0 before the fix, and each writes files outside the KB — a sidecar minted in a directory
# pinakes was never pointed at.


def _set_include(kb: Path, *patterns: str) -> None:
    """Rewrite whatever `include` line is there — callers set it more than once."""
    import re

    text = (kb / "pinakes.toml").read_text(encoding="utf-8")
    listed = ", ".join(f'"{pattern}"' for pattern in patterns)
    replaced, count = re.subn(r"include = \[[^\]]*\]", f"include = [{listed}]", text)
    assert count == 1, "the fixture manifest no longer has exactly one `include`"
    (kb / "pinakes.toml").write_text(replaced, encoding="utf-8")


def test_an_include_pattern_that_climbs_out_of_the_kb_is_refused_at_load(kb: Path) -> None:
    """Defect 1, layer 1. Measured on 0.7.0: `2 indexed`, and a sidecar written outside the KB.

    A hard error at load, matching the `roots` precedent, because this manifest is the user's own —
    and because `pinakes.toml` is committed and shared, so cloning a KB and running `pnk sync`
    ran *their* `include` against *your* tree.
    """
    outside = kb.parent / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("# Secret\n\nNot ours.\n", encoding="utf-8")
    _set_include(kb, "**/*.md", "../../outside/*.md")

    with pytest.raises(ManifestError) as exc_info:
        load(kb)
    assert "reaches outside the KB" in str(exc_info.value)
    assert "../../outside/*.md" in str(exc_info.value)
    assert not (outside / f"secret.md{SIDECAR_SUFFIX}").exists(), "nothing may be written outside"


def test_an_absolute_include_pattern_is_a_manifest_error_not_a_traceback(kb: Path) -> None:
    """Defect 2. `glob` raises `NotImplementedError` on any absolute pattern, wherever it points.

    On 0.7.0 that went out through `cli.main` as a stack trace with no `error:` line and no remedy.
    Its own message, because "reaches outside the KB" is false for an absolute path naming this
    KB's own `docs/` — which `glob` still cannot walk.
    """
    _set_include(kb, str(kb / "docs" / "*.md"))

    with pytest.raises(ManifestError) as exc_info:
        load(kb)
    assert "is an absolute path" in str(exc_info.value)
    assert "cannot walk an absolute pattern" in (exc_info.value.remedy or "")
    assert "reaches outside" not in str(exc_info.value), "an absolute path here is inside the KB"


def test_a_symlinked_directory_cannot_carry_the_walk_out_of_the_kb(kb: Path) -> None:
    """Defect 3, layer 2 — no `..` and no absolute path anywhere, so layer 1 cannot see it.

    Measured on 0.7.0: `1 indexed`, and a sidecar minted in the outside directory.
    """
    outside = kb.parent / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("# Secret\n\nNot ours.\n", encoding="utf-8")
    (kb / "docs" / "escape").symlink_to(outside, target_is_directory=True)
    _set_include(kb, "*/*.md")

    report = run(kb)

    assert report.embedded == 0, "nothing outside the KB may be indexed"
    assert not (outside / f"secret.md{SIDECAR_SUFFIX}").exists()
    assert report.escaping_patterns == ("*/*.md",)
    assert any("left the KB through a symlinked directory" in line for line in report.lines())


def test_a_symlinked_document_inside_the_kb_is_still_ingested(kb: Path) -> None:
    """The asymmetry, and the over-tightening regression it guards.

    Parent resolved, final component left alone. Resolving the whole path would follow a final
    symlink and refuse a symlinked *document*, which is a legitimate thing to have in a KB.
    """
    real = kb / "docs" / "real.md"
    real.write_text("# Real\n\nA document about retrieval.\n", encoding="utf-8")
    (kb / "docs" / "alias.md").symlink_to(real)

    report = run(kb)

    assert report.escaping_patterns == ()
    assert {row["path"] for row in index(kb)} == {"docs/real.md", "docs/alias.md"}


def test_the_same_document_is_ingested_by_a_fixed_and_a_globbed_pattern_alike(kb: Path) -> None:
    """Two spellings of one include must not give opposite answers (linkscan review 13).

    `include = ["alpha.md"]` and `include = ["*.md"]` name the same file. Resolving the joined path
    whole accepts the second and refuses the first, because only the fixed spelling ends in a real
    name that `resolve()` will follow.
    """
    real = kb.parent / "outside-target.md"
    real.write_text("# Alpha\n\nA document about retrieval.\n", encoding="utf-8")
    (kb / "docs" / "alpha.md").symlink_to(real)

    _set_include(kb, "alpha.md")
    load(kb)  # must not raise
    _set_include(kb, "*.md")
    load(kb)


def test_a_dot_dot_pattern_that_stays_inside_the_kb_is_accepted(kb: Path) -> None:
    """Review 12: what matters is where the path *lands*, never whether `..` occurs in it.

    `../notes/*.md` from `docs/` lands inside the KB and is a legitimate manifest. Refusing it is
    the same defect as accepting an escape.
    """
    notes = kb / "notes"
    notes.mkdir()
    (notes / "n.md").write_text("# Note\n\nA note about retrieval.\n", encoding="utf-8")
    _set_include(kb, "../notes/*.md")

    report = run(kb)

    assert report.escaping_patterns == ()
    assert {row["path"] for row in index(kb)} == {"notes/n.md"}


def test_a_leading_glob_does_not_defeat_the_static_refusal(kb: Path) -> None:
    """Review 13: `*/../../../outside/**` has an empty fixed prefix.

    A check that resolves only the prefix before the first glob component passes it
    unconditionally, and the `..` then runs inside `glob` — the unbounded walk, reachable again.
    """
    _set_include(kb, "*/../../../outside/*.md")

    with pytest.raises(ManifestError) as exc_info:
        load(kb)
    assert "reaches outside the KB" in str(exc_info.value)


def test_a_double_star_before_a_dot_dot_does_not_defeat_the_refusal(kb: Path) -> None:
    """Review 14: `**` matches *zero* components while `Path.parts` counts it as one.

    Keeping `**` in the probe lets a following `..` cancel it, so the probe lands one level below
    where the walk actually goes — `**/../../**/*.md` probed inside the KB and then walked the
    directory containing it, recursively. Review 13's ten measured patterns were all correct and
    none of them combined `**` with `..`, which is how a table of cases reads like proof of a rule.
    """
    _set_include(kb, "**/../../**/*.md")

    with pytest.raises(ManifestError) as exc_info:
        load(kb)
    assert "reaches outside the KB" in str(exc_info.value)


def test_an_escaping_pattern_is_refused_without_enumerating_the_tree(kb: Path) -> None:
    """Layer 1's whole purpose: refuse *before* globbing, which is what bounds the walk.

    Checking each candidate afterwards refuses the results while still paying for the enumeration.
    Counted as entries pulled from the generator, not as `resolve()` calls — the cost being avoided
    is the walk itself.

    The count is a **design** assertion rather than a trap for a specific mutation: containment now
    lives at load, where nothing globs at all, so the only way `pulled` rises is a future version
    that moves the check back into the walk. That is exactly the regression worth naming, and the
    `raises` above is what catches the guard simply going missing.
    """
    outside = kb.parent / "outside"
    outside.mkdir()
    for number in range(200):
        (outside / f"f{number}.md").write_text("x\n", encoding="utf-8")

    pulled = 0
    real_glob = Path.glob

    def counting_glob(self: Path, pattern: str, **kwargs: Any) -> Iterator[Path]:
        nonlocal pulled
        for entry in real_glob(self, pattern, **kwargs):
            pulled += 1
            yield entry

    _set_include(kb, "../../outside/*.md")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, "glob", counting_glob)
        with pytest.raises(ManifestError):
            load(kb)

    assert pulled == 0, f"the tree was enumerated before the refusal ({pulled} entries)"


def test_a_root_that_does_not_exist_yet_still_loads(kb: Path) -> None:
    """Layer 1 runs on every manifest load, including before the directories exist.

    `resolve()` is non-strict, so a probe under a missing root is collapsed lexically rather than
    raising — and a KB whose `docs/` has not been created must still be openable, which is the
    state `pnk init` leaves behind for a root the user adds by hand.
    """
    import shutil

    shutil.rmtree(kb / "docs")
    _set_include(kb, "**/*.md", "../notes/*.md")

    assert load(kb).sources.include == ("**/*.md", "../notes/*.md")


def test_the_escape_is_reported_once_per_pattern_not_once_per_file(kb: Path) -> None:
    """A hostile pattern matches thousands, and two roots reported the same escape twice."""
    outside = kb.parent / "outside"
    outside.mkdir()
    for number in range(5):
        (outside / f"f{number}.md").write_text("# F\n\nText.\n", encoding="utf-8")
    (kb / "docs" / "escape").symlink_to(outside, target_is_directory=True)
    (kb / "docs" / "sub").mkdir()
    text = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "pinakes.toml").write_text(
        text.replace('roots = ["docs/"]', 'roots = ["docs/", "docs/sub/"]'), encoding="utf-8"
    )
    _set_include(kb, "*/*.md")

    report = run(kb)

    assert report.escaping_patterns == ("*/*.md",), "one entry per pattern, not per file or root"
    assert len(report.escape_lines()) == 1


def test_an_excluded_pattern_may_contain_dot_dot(kb: Path) -> None:
    """The stated asymmetry, pinned so a later pass does not "fix" it.

    An `..` in `exclude` can only fail to match, never widen the walk, so it is not validated.
    """
    write(kb, "keep.md", "# Keep\n\nA document about retrieval.\n")
    text = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "pinakes.toml").write_text(
        text.replace('include = ["**/*.md"]', 'include = ["**/*.md"]\nexclude = ["../../*.md"]'),
        encoding="utf-8",
    )

    report = run(kb)

    assert report.embedded == 1
    assert report.escaping_patterns == ()


def test_one_file_reached_by_two_legal_spellings_is_one_document(kb: Path) -> None:
    """The key must collapse `..`, or one file becomes two identities.

    `[sources]` legitimately allows a pattern containing `..` that lands inside the KB, and
    `relative_to` is lexical — so it hands back the `..` it was given. Measured on 0.7.0 with the
    manifest below: the file was indexed once as `docs/../notes/n.md` and then **failed twice**
    with *"appeared after the walk had already read this directory"*, because the sidecar found
    under one key was invisible under the other.
    """
    notes = kb / "notes"
    notes.mkdir()
    (notes / "n.md").write_text("# Note\n\nA note about retrieval.\n", encoding="utf-8")
    text = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "pinakes.toml").write_text(
        text.replace('roots = ["docs/"]', 'roots = ["docs/", "notes/"]'), encoding="utf-8"
    )
    _set_include(kb, "../notes/*.md", "*.md")

    report = run(kb)

    assert report.failures == [], (
        f"one file must not fail under a second spelling: {report.failures}"
    )
    assert {row["path"] for row in index(kb)} == {"notes/n.md"}
    assert report.embedded == 1
    # The unmatched sweep compares against these same keys, so a `..` in one made an *indexed*
    # document look like a file no pattern had picked up.
    assert report.unmatched == ()


def test_an_escaping_pattern_that_matches_only_a_directory_is_still_caught(kb: Path) -> None:
    """Containment runs *before* the `is_file()` skip, and this is the case that proves it.

    A pattern reaching outside that matches only directories — or only sidecars — hits one of the
    `continue`s below the check first, so with the order reversed the walk leaves the KB and reports
    nothing at all. Every other symlink test here matches a file, where the ordering is invisible.
    """
    outside = kb.parent / "outside"
    (outside / "sub").mkdir(parents=True)
    (kb / "docs" / "escape").symlink_to(outside, target_is_directory=True)
    _set_include(kb, "*/*")  # matches `docs/escape/sub`, a directory, and nothing else

    report = run(kb)

    assert report.escaping_patterns == ("*/*",), "an escape matching no file is still an escape"


def test_an_escape_under_one_root_does_not_drop_documents_under_another(kb: Path) -> None:
    """A symlink is a property of one directory, never of the pattern — so it may not drop files.

    `linkscan.sidecars_under` skips a known-escaping pattern under every later root, and copying
    that here would be data loss rather than caution: a dropped document is a deleted index row and
    an orphaned sidecar, where a dropped partner candidate is one missing inbound link.
    """
    outside = kb.parent / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("# Secret\n\nNot ours.\n", encoding="utf-8")
    (kb / "docs" / "escape").symlink_to(outside, target_is_directory=True)
    other = kb / "other" / "sub"
    other.mkdir(parents=True)
    (other / "keep.md").write_text("# Keep\n\nA document about retrieval.\n", encoding="utf-8")
    text = (kb / "pinakes.toml").read_text(encoding="utf-8")
    (kb / "pinakes.toml").write_text(
        text.replace('roots = ["docs/"]', 'roots = ["docs/", "other/"]'), encoding="utf-8"
    )
    _set_include(kb, "*/*.md")

    report = run(kb)

    assert report.escaping_patterns == ("*/*.md",)
    assert {row["path"] for row in index(kb)} == {"other/sub/keep.md"}, (
        "an escape under one root must not stop the same pattern collecting under another"
    )


def test_a_symlinked_escape_stops_the_walk_rather_than_enumerating_the_tree(kb: Path) -> None:
    """The `break`'s only justification — and it has one only because the loop is lazy.

    Layer 1 cannot pre-empt a symlinked escape (it exists on disk, not in the manifest), so this
    loop is the only thing bounding it. Written as `sorted(root.glob(pattern))` the generator is
    drained before the first candidate is inspected, and the `break` then saves nothing at all:
    the enumeration it exists to stop has already run.
    """
    outside = kb.parent / "outside"
    outside.mkdir()
    for number in range(300):
        (outside / f"f{number:03d}.md").write_text("# F\n\nText.\n", encoding="utf-8")
    (kb / "docs" / "escape").symlink_to(outside, target_is_directory=True)
    _set_include(kb, "*/*.md")

    pulled = 0
    real_glob = Path.glob

    def counting_glob(self: Path, pattern: str, **kwargs: Any) -> Iterator[Path]:
        nonlocal pulled
        for entry in real_glob(self, pattern, **kwargs):
            pulled += 1
            yield entry

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, "glob", counting_glob)
        report = run(kb)

    assert report.escaping_patterns == ("*/*.md",)
    assert pulled < 50, f"the escape enumerated {pulled} of 300 entries before stopping"


# --- `[chunking]` drift: a manifest-only edit is a no-op, and must say so -----------------------


def _set_chunking(kb: Path, **keys: str) -> None:
    """Set `[chunking]` keys in the KB's manifest, **leaving the others alone**.

    The first version replaced the whole table, which silently reset the fixture's `max_tokens = 40`
    to the default and produced drift on keys the test never touched. A helper that edits more than
    it says is how a test comes to assert something other than what it names.
    """
    import re

    manifest = kb / "pinakes.toml"
    text = manifest.read_text(encoding="utf-8")
    if "[chunking]" not in text:
        text += "\n[chunking]\n"
    for key, value in keys.items():
        line = f"{key} = {value}"
        text, count = re.subn(rf"^{key}\s*=.*$", line, text, count=1, flags=re.MULTILINE)
        if not count:
            text = text.replace("[chunking]\n", f"[chunking]\n{line}\n", 1)
    manifest.write_text(text, encoding="utf-8")


def test_a_chunking_edit_is_reported_rather_than_silently_ignored(kb: Path) -> None:
    """The defect this exists for: an incremental sync re-chunks a document only when *the
    document* changed, so a manifest-only edit reports every file `unchanged` and does nothing.
    Measured 20260805 before the fix — the user's next move was `pnk doctor`, which then reported
    exactly the condition they had just tried to fix."""
    run(kb)
    _set_chunking(kb, headings='"numbered"')
    report = run(kb)

    assert report.embedded == 0, "precondition: nothing re-chunked, which is the whole problem"
    assert report.chunking_drift == (("chunking_headings", "none", "numbered"),)
    assert any("--rebuild" in line for line in report.lines())


def test_the_chunking_warning_persists_until_the_rebuild_actually_happens(kb: Path) -> None:
    """**Found by running it, after the first draft passed every test.** `set_meta` wrote the
    current settings at the end of *every* sync, so the warning fired once and the index then
    claimed a coherence it did not have — `pnk doctor` reported OK over chunks built under the old
    settings. A warning that clears itself without the fix being applied is worse than none."""
    run(kb)
    _set_chunking(kb, headings='"numbered"')
    run(kb)
    again = run(kb)
    assert again.chunking_drift == (("chunking_headings", "none", "numbered"),)


def test_a_rebuild_clears_the_drift_because_it_actually_re_chunks(kb: Path) -> None:
    run(kb)
    _set_chunking(kb, headings='"numbered"')
    run(kb, rebuild=True)
    assert run(kb).chunking_drift == ()


def test_an_index_with_no_recorded_chunking_identity_is_never_reported_as_drifted(
    kb: Path,
) -> None:
    """Every KB indexed before this existed. Absence is *unknown*, not *different* — a check that
    fired on all of them would demand a full rebuild of every KB on first upgrade."""
    run(kb)
    index = kb / ".pinakes" / "index.db"
    connection = sqlite3.connect(index)
    connection.execute("DELETE FROM meta WHERE key LIKE 'chunking_%'")
    connection.commit()
    connection.close()

    _set_chunking(kb, headings='"numbered"')
    assert run(kb).chunking_drift == ()


def test_drift_is_reported_for_max_tokens_and_overlap_too(kb: Path) -> None:
    """Not a `headings` feature. Both have behaved this way since v0.1; `headings` is only the
    first `[chunking]` key a user has had reason to flip on an already-indexed KB."""
    before = load(kb).chunking  # the fixture's own values, not the documented defaults
    run(kb)
    _set_chunking(kb, max_tokens="256", overlap="32")
    assert dict((key, (was, now)) for key, was, now in run(kb).chunking_drift) == {
        "chunking_max_tokens": (str(before.max_tokens), "256"),
        "chunking_overlap": (str(before.overlap), "32"),
    }


# --- A Markdown document titles itself from its own `# ` heading -------------------------------


def _title_of(kb: Path, name: str) -> str:
    import yaml

    text = (kb / "docs" / f"{name}{SIDECAR_SUFFIX}").read_text(encoding="utf-8")
    return str(yaml.safe_load(text)["title"])


def test_a_markdown_h1_becomes_the_title(kb: Path) -> None:
    """Until now `sync` never read a document's content for its title, and it was easy to miss:
    `# Access restrictions` sat beside `title: access restrictions`, which looks like the H1 *was*
    used when the value is the filename stem with hyphens swapped for spaces. The capital letter is
    the tell."""
    (kb / "docs" / "rfc9110-notes.md").write_text("# HTTP Semantics\n\nBody.\n", encoding="utf-8")
    run(kb)
    assert _title_of(kb, "rfc9110-notes.md") == "HTTP Semantics"


def test_a_document_with_no_h1_keeps_the_filename_fallback(kb: Path) -> None:
    """The fallback was kept deliberately — a title that is visibly a filename is honest about
    being one."""
    (kb / "docs" / "plain-notes.md").write_text("No heading here.\n", encoding="utf-8")
    run(kb)
    assert _title_of(kb, "plain-notes.md") == "plain notes"


def test_a_hash_inside_a_code_fence_is_not_a_title(kb: Path) -> None:
    """`#` opens a comment in half the languages there are, so a fenced one would title a document
    after whatever its first code sample happens to say."""
    (kb / "docs" / "fenced.md").write_text(
        "```\n# not a heading\n```\n\n# Real Title\n\nBody.\n", encoding="utf-8"
    )
    run(kb)
    assert _title_of(kb, "fenced.md") == "Real Title"


def test_only_a_level_one_heading_titles_the_document(kb: Path) -> None:
    """`##` is a section, not the document's name. A file that opens on a subsection would
    otherwise be titled after it."""
    (kb / "docs" / "subsection-first.md").write_text("## A Section\n\nBody.\n", encoding="utf-8")
    run(kb)
    assert _title_of(kb, "subsection-first.md") == "subsection first"


def test_a_plain_text_file_is_not_titled_from_a_hash_line(kb: Path) -> None:
    """Markdown only. A `#` in a `.txt` is a comment character, not a heading — and reading a PDF
    here would be a second extraction outside the cache."""
    manifest = kb / "pinakes.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'include = ["**/*.md"]', 'include = ["**/*.md", "**/*.txt"]', 1
        ),
        encoding="utf-8",
    )
    (kb / "docs" / "notes.txt").write_text("# Looks Like A Heading\n\nBody.\n", encoding="utf-8")
    run(kb)
    assert _title_of(kb, "notes.txt") == "notes"


def test_an_existing_sidecars_title_is_never_rewritten(kb: Path) -> None:
    """**The invariant that makes this safe to ship without a migration.** `skeleton()` runs only
    when a sidecar is minted, so every KB already indexed keeps the titles it has — and `title` is
    the user's field, which a sync must never overwrite."""
    document = kb / "docs" / "rfc9110-notes.md"
    document.write_text("# HTTP Semantics\n\nBody.\n", encoding="utf-8")
    run(kb)

    sidecar = kb / "docs" / f"rfc9110-notes.md{SIDECAR_SUFFIX}"
    sidecar.write_text(
        sidecar.read_text(encoding="utf-8").replace(
            "title: HTTP Semantics", "title: What I Actually Call It"
        ),
        encoding="utf-8",
    )
    document.write_text("# A Completely Different H1\n\nBody, edited.\n", encoding="utf-8")
    run(kb)

    assert _title_of(kb, "rfc9110-notes.md") == "What I Actually Call It"


class _RecordingBackend(FakeBackend):
    """`FakeBackend` that keeps every string it was asked to embed.

    What is *embedded* is the one thing injection changes and the one thing no artifact records:
    the index stores `chunk.text` either way, so a test reading the database alone cannot tell an
    injected run from an uninjected one — which is precisely the failure mode the option is
    designed around."""

    def __init__(self) -> None:
        self.embedded: list[str] = []

    def embed(self, texts: Sequence[str]) -> Vectors:
        self.embedded.extend(texts)
        return super().embed(texts)


def run_recording(kb: Path, **options: Any) -> tuple[SyncReport, _RecordingBackend]:
    backend = _RecordingBackend()
    report = sync(
        load(kb),
        options=SyncOptions(**options),
        backend_factory=lambda manifest, offline: backend,
        now="20260725 16:00",
    )
    return report, backend


def _chunk_rows(kb: Path) -> list[tuple[str, int, int, str | None]]:
    connection = sqlite3.connect(kb / ".pinakes" / "index.db")
    try:
        return [
            (str(text), int(start), int(end), None if path is None else str(path))
            for text, start, end, path in connection.execute(
                "SELECT text, char_start, char_end, heading_path FROM chunks ORDER BY id"
            )
        ]
    finally:
        connection.close()


SECTIONED = """# HTTP Semantics

## Message Forwarding

A first paragraph, long enough that the fixture's forty-token budget cannot hold
the whole section in one chunk and a continuation chunk has to exist.

A second paragraph under the same heading, which is the chunk the hypothesis is
about: it carries none of the section's own heading text.
"""


def test_metadata_injection_is_off_by_default_and_embeds_the_chunk_text(kb: Path) -> None:
    """The default is the whole compatibility story: every KB that predates the key embeds exactly
    what it embedded before, so no existing index's vectors change meaning under an upgrade."""
    write(kb, "rfc.md", SECTIONED)
    report, backend = run_recording(kb)

    # Both sides are derived from the same run, so `[] == []` would satisfy this assertion while
    # asserting nothing at all — a regression that chunked nothing would read as green.
    assert report.embedded == 1 and len(backend.embedded) > 1, "precondition: it indexed something"
    assert backend.embedded == [text for text, _start, _end, _path in _chunk_rows(kb)]


def test_metadata_injection_embeds_the_prefix_and_stores_the_text_unchanged(kb: Path) -> None:
    """The two halves of §2 step 1: the prefix reaches the **embedded** text, and `chunks.text`,
    `char_start` and `char_end` do not move — a chunk's text stays exactly
    `source[char_start:char_end]`, which is what `search` returns and what citations index into.
    Mutating the stored text would reach both channels for free and is refused for that reason."""
    source = write(kb, "rfc.md", SECTIONED)
    _set_chunking(kb, metadata='"prefix"')
    _report, backend = run_recording(kb)

    rows = _chunk_rows(kb)
    assert len(rows) > 1, "precondition: a section spanning more than one chunk"
    text_of_source = source.read_text(encoding="utf-8")
    for (text, start, end, _path), embedded in zip(rows, backend.embedded, strict=True):
        assert text == text_of_source[start:end], "the byte-identity bound, unchanged"
        assert embedded.endswith(PREFIX_SEPARATOR + text)
        assert embedded != text, "something was actually prepended"
    assert any("Message Forwarding" in embedded for embedded in backend.embedded)


def test_the_injected_title_is_the_one_the_index_records(kb: Path) -> None:
    """One read of `title`, used for both the document row and the prefix. Two reads are two
    chances to inject a string the user cannot see — and `title` is the user's field, so the
    hand-edited value is the one that must travel into the vectors.

    Re-synced with `--rebuild` deliberately: a sidecar-only edit is a `RefreshMetadata`, which
    updates the row without re-embedding, so the assertions below would hold over an empty list
    and prove nothing. The non-empty check is there to keep them from going vacuous again.
    """
    write(kb, "rfc.md", SECTIONED)
    _set_chunking(kb, metadata='"prefix"')
    run_recording(kb)

    sidecar = kb / "docs" / f"rfc.md{SIDECAR_SUFFIX}"
    sidecar.write_text(
        sidecar.read_text(encoding="utf-8").replace(
            "title: HTTP Semantics", "title: What I Actually Call It"
        ),
        encoding="utf-8",
    )
    _report, backend = run_recording(kb, rebuild=True)

    assert index(kb)[0]["title"] == "What I Actually Call It"
    assert backend.embedded, "precondition: this run actually re-embedded"
    assert all(embedded.startswith("What I Actually Call It > ") for embedded in backend.embedded)


def test_injection_refuses_a_prefix_that_does_not_fit_the_reserve(kb: Path) -> None:
    """`assert_prefix_fits`, wired in here and dormant until now. Without it the embedder silently
    truncates — measured 20260806, a 512-token string embedded with an empty `warnings` list — and
    what it cuts is the tail of the *longest* chunks, exactly the ones a prefix is meant to help.
    The loss then reads as "the change did nothing", a false negative that looks like a clean
    result.

    **A per-document failure, not an aborted run** — what every `PinakesError` out of the indexing
    path already becomes: the transaction rolls back, the document is named in the report and
    recorded in the index for `pnk doctor`, and one pathological heading path does not cost a
    195-document corpus its other 194. What the refusal has to guarantee is the narrower thing
    asserted below: a document whose prefix does not fit is **not indexed truncated**.
    """
    write(kb, "rfc.md", SECTIONED)
    _set_chunking(kb, metadata='"prefix"', max_tokens="508")  # 510 encodable, so 2 left over

    report, backend = run_recording(kb)

    assert [path for path, _error, _remedy in report.failures] == ["docs/rfc.md"]
    error = report.failures[0][1]
    assert "prefix" in error and "max_tokens" in error
    assert backend.embedded == [], "nothing was embedded, so nothing could be truncated"
    assert _chunk_rows(kb) == []


def test_the_refusal_does_not_fire_when_injection_is_off(kb: Path) -> None:
    """The reserve is only needed by a corpus that is actually prefixed. Refusing one that is not
    at risk would turn an opt-in feature into a breaking change for every existing KB — the same
    manifest, the same documents, and a sync that used to work."""
    write(kb, "rfc.md", SECTIONED)
    _set_chunking(kb, max_tokens="508")

    report, backend = run_recording(kb)
    assert report.embedded == 1
    assert backend.embedded == [text for text, _start, _end, _path in _chunk_rows(kb)]


def test_turning_injection_on_is_reported_as_drift_rather_than_silently_ignored(kb: Path) -> None:
    """The sharpest case of the defect `chunking_identity` exists for. Flipping `metadata` changes
    no chunk's text, hash or span, so an incremental sync finds every document unchanged and
    re-embeds nothing: without the recorded key the user would search uninjected vectors with
    every command reporting success."""
    write(kb, "rfc.md", SECTIONED)
    run(kb)
    _set_chunking(kb, metadata='"prefix"')
    report = run(kb)

    assert report.embedded == 0, "precondition: nothing re-embedded, which is the whole problem"
    assert report.chunking_drift == (("chunking_metadata", "off", "prefix"),)
    assert any("--rebuild" in line for line in report.lines())


def test_a_rebuild_applies_the_injection_and_clears_the_drift(kb: Path) -> None:
    write(kb, "rfc.md", SECTIONED)
    run(kb)
    _set_chunking(kb, metadata='"prefix"')
    _report, backend = run_recording(kb, rebuild=True)

    # `set_meta` writes the chunking identity whenever the run chunked from empty, whether or not
    # any document survived — so the drift assertion below does not rescue an `all(...)` over an
    # empty list, and a rebuild that indexed nothing would pass both.
    assert backend.embedded, "precondition: this rebuild actually re-embedded"
    assert all(PREFIX_SEPARATOR in embedded for embedded in backend.embedded)
    assert run(kb).chunking_drift == ()


def test_a_document_with_no_headings_is_still_prefixed_with_its_title(kb: Path) -> None:
    """Either part of the prefix alone is a legitimate prefix — and through `sync` the title part
    is always there. `skeleton()` falls back to the filename stem, so a document can reach the
    embedder with no `heading_path` but never with no title, and with injection on **every**
    document is prefixed.

    **Which makes this the plan's finding 5, measured at the sync boundary** (§2 of
    `plans/20260805_1721-metadata-as-retrieval-context.md`): on an uncurated corpus the injected
    string is a *filename*, so `rfc9110` enters every chunk of that document — able to lift any
    question naming it and to dilute every other. It is why the RFC corpus mints published titles
    before its first sync rather than relying on the fallback, and why `pnk doctor`'s title check
    (0.14.0) exists to find the corpora that do not.
    """
    write(kb, "plain.md", "Body text with no heading at all.\n")
    _set_chunking(kb, metadata='"prefix"')
    _report, backend = run_recording(kb)

    rows = _chunk_rows(kb)
    assert [path for _text, _start, _end, path in rows] == [None], "nothing but the title to say"
    assert index(kb)[0]["title"] == "plain", "the filename stem, not content"
    assert backend.embedded == [f"plain{PREFIX_SEPARATOR}{text}" for text, *_rest in rows]


def test_a_rebuild_injects_a_protected_paid_document_too(kb: Path, fake_paid: str) -> None:
    """**The half-injected index.** `--rebuild` carries a paid-extracted document forward instead
    of re-extracting it, and it used to carry its *vectors* forward with it — while `set_meta`
    stamped the current `[chunking]` over the whole index. Turning injection on therefore produced
    a KB whose paid documents held uninjected vectors, whose `meta` said `prefix`, and whose next
    `pnk sync` and `pnk doctor` both reported no drift: every command succeeded over an index that
    was injected in one half and not the other.

    Extraction is what costs money; embedding is free, and the chunk texts are carried forward, so
    the vectors are recomputed here rather than copied. The paid extraction itself is still
    untouched — `test_a_rebuild_preserves_paid_provenance` owns that half.
    """
    _paid_index(kb, fake_paid)
    _set_chunking(kb, metadata='"prefix"')

    report, backend = run_recording(kb, rebuild=True)

    assert report.paid_extraction_protected == ("docs/a.pdf",), "precondition: it was protected"
    assert index(kb)[0]["extraction_backend"] == fake_paid, "and never re-extracted"
    assert backend.embedded, "precondition: the copied-forward chunks were embedded at all"
    assert all(embedded.startswith(f"a{PREFIX_SEPARATOR}") for embedded in backend.embedded), (
        "a PDF carries no heading path, so the prefix is the title alone"
    )
    assert run(kb).chunking_drift == (), "and the index may now honestly claim the setting"


def test_turning_injection_off_re_embeds_a_protected_document_as_well(
    kb: Path, fake_paid: str
) -> None:
    """The mirror image, which a one-directional fix would leave open: an index built *with*
    injection, rebuilt after turning it off, must not keep prefixed vectors for the one class of
    document that is carried forward."""
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"placeholder")
    _set_chunking(kb, metadata='"prefix"')
    assert run(kb, extract=fake_paid).embedded == 1

    _set_chunking(kb, metadata='"off"')
    _report, backend = run_recording(kb, rebuild=True)

    assert backend.embedded, "precondition: the copied-forward chunks were embedded at all"
    assert not any(PREFIX_SEPARATOR in embedded for embedded in backend.embedded)


def test_turning_injection_on_is_reported_on_an_index_that_predates_the_key(kb: Path) -> None:
    """**Every KB in existence on the day this ships.** `chunking_drift` treats an absent key as
    unknown — the compatibility rule that stops an upgrade demanding a rebuild of every index — and
    `chunking_metadata` is absent from every index built by 0.13.0-0.15.1, since only a `--rebuild`
    ever stamps the identity. So without `store.ABSENT_MEANS` the flip was silent on exactly the
    indexes that exist: no drift, nothing re-embedded, and `pnk doctor` affirming coherence.

    Absence is *known* for this key, unlike `max_tokens` and `overlap`: no release that could have
    written such an index was able to inject, so absence proves `off`. It therefore fires only for
    a user who opted in — never for anyone left on the default, which is the compatibility
    guarantee it must not break.
    """
    write(kb, "rfc.md", SECTIONED)
    run(kb)
    connection = sqlite3.connect(kb / ".pinakes" / "index.db")
    connection.execute("DELETE FROM meta WHERE key = 'chunking_metadata'")  # the 0.15.1 shape
    connection.commit()
    connection.close()

    _set_chunking(kb, metadata='"prefix"')
    report = run(kb)

    assert report.chunking_drift == (("chunking_metadata", "off", "prefix"),)
    assert any("--rebuild" in line for line in report.lines())


def test_an_index_predating_the_key_is_still_not_drifted_while_injection_stays_off(
    kb: Path,
) -> None:
    """The other half, and the one that keeps the compatibility promise: reading absence as `off`
    must not fire on a KB whose owner never turned injection on. Every upgraded index is in exactly
    this state, and a warning here would be one nobody could clear."""
    write(kb, "rfc.md", SECTIONED)
    run(kb)
    connection = sqlite3.connect(kb / ".pinakes" / "index.db")
    connection.execute("DELETE FROM meta WHERE key = 'chunking_metadata'")
    connection.commit()
    connection.close()

    assert run(kb).chunking_drift == ()


def test_a_carried_forward_document_is_refused_when_its_prefix_would_be_truncated(
    kb: Path, fake_paid: str
) -> None:
    """The path that re-embeds **without re-chunking** needs the fit check more than the indexing
    path does, and it was the one path without it. These chunks were sized by whatever `max_tokens`
    built the *old* index and are never re-chunked, so the current reserve does not bound them even
    in principle — and the remedy the manifest docstring prescribes (lower `max_tokens`) cannot
    help a document this run never chunks."""
    _paid_index(kb, fake_paid)
    # The default: a 512-token window, 2 special tokens, so `max_tokens = 510` reserves **zero**
    # for a prefix. That is finding 1 of the plan, and the condition every hand-written manifest
    # reintroduces.
    _set_chunking(kb, metadata='"prefix"', max_tokens="510")

    report, backend = run_recording(kb, rebuild=True)

    assert [path for path, _error, _remedy in report.failures] == ["docs/a.pdf"]
    assert "prefix" in report.failures[0][1]
    assert backend.embedded == [], "nothing embedded, so nothing truncated"


def test_a_failed_carry_forward_leaves_no_half_written_document_behind(
    kb: Path, fake_paid: str
) -> None:
    """`--rebuild` swaps its new index in unconditionally, so anything committed before a failure
    is published. The copy-forward path has to commit before `DETACH`, and while the writes sat
    inside that transaction a document whose embedding failed survived as `active` with chunks and
    **zero vectors** — a state `_apply`'s `rollback()` could no longer undo, and one no later sync
    repairs, because the file's content hash is unchanged and every future run reports `Skip`."""
    _paid_index(kb, fake_paid)
    _set_chunking(kb, metadata='"prefix"', max_tokens="510")

    run_recording(kb, rebuild=True)  # the refusal above, mid-way through the copy-forward

    connection = sqlite3.connect(kb / ".pinakes" / "index.db")
    try:
        rows = connection.execute(
            "SELECT count(*) FROM documents d JOIN chunks c ON c.doc_id = d.id "
            "LEFT JOIN embeddings e ON e.chunk_id = c.id "
            "WHERE d.state = 'active' AND e.chunk_id IS NULL"
        ).fetchone()[0]
    finally:
        connection.close()
    assert rows == 0, "no active document may hold a chunk with no vector"


def test_a_title_edit_under_injection_is_reported_rather_than_left_silent(kb: Path) -> None:
    """With injection on, `title` stops being display metadata: it is part of the text the vectors
    were built from. A title edit is still a sidecar-only change, which pairing routes as
    `RefreshMetadata` — the row is updated, nothing is re-embedded — and nothing repairs it later
    either, because the file's content hash is unchanged so every future sync yields `Skip`.

    Reported, not repaired: repairing means re-running `_index_document`, which re-*extracts*, and
    on a paid-extracted PDF that would spend money in response to a typo fix.
    """
    write(kb, "rfc.md", SECTIONED)
    _set_chunking(kb, metadata='"prefix"')
    run(kb)

    sidecar = kb / "docs" / f"rfc.md{SIDECAR_SUFFIX}"
    sidecar.write_text(
        sidecar.read_text(encoding="utf-8").replace(
            "title: HTTP Semantics", "title: What I Actually Call It"
        ),
        encoding="utf-8",
    )
    report, backend = run_recording(kb)

    assert report.refreshed == 1 and backend.embedded == [], "precondition: nothing re-embedded"
    assert report.stale_prefixes == ["docs/rfc.md"]
    line = next(line for line in report.lines() if "title changed" in line)
    assert "docs/rfc.md" in line and "--rebuild" in line


def test_a_title_edit_with_injection_off_reports_nothing(kb: Path) -> None:
    """The default, and it must stay quiet: with no injection the vectors never carried the title,
    so a refreshed row is the whole of the change and there is nothing stale to report."""
    write(kb, "rfc.md", SECTIONED)
    run(kb)

    sidecar = kb / "docs" / f"rfc.md{SIDECAR_SUFFIX}"
    sidecar.write_text(
        sidecar.read_text(encoding="utf-8").replace(
            "title: HTTP Semantics", "title: What I Actually Call It"
        ),
        encoding="utf-8",
    )
    report = run(kb)

    assert report.refreshed == 1
    assert report.stale_prefixes == []
    assert not any("title changed" in line for line in report.lines())


def test_a_retired_row_no_longer_blocks_a_new_id_at_its_own_path(kb: Path) -> None:
    """A sidecar whose id no longer matches the row at its path — a merge conflict, a
    `git checkout <sha> -- <file>.pnk.yaml`, a sidecar copied between KBs.

    `pairing` retires the stale row and adopts the sidecar's id, because the sidecar is committed
    truth for identity. A retired row keeps its `path` and `documents.path` is UNIQUE, so the
    adoption collided with the corpse: `sqlite3.IntegrityError` escaped as a raw traceback, the
    retired row survived it, and every later sync hit the same wall while `pnk doctor` called the
    KB healthy at exit 0.
    """
    write(kb, "a.md", "# Alpha\n\nAlpha body here.\n")
    run(kb)
    fresh = mint_doc_id()
    (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").write_text(f"id: {fresh}\n", encoding="utf-8")

    run(kb)

    rows = index(kb)
    assert [(row["path"], row["state"], str(row["id"])) for row in rows] == [
        ("docs/a.md", "active", str(fresh))
    ]


def test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row(kb: Path) -> None:
    """Why the retiring DELETE is scoped to `state = 'deleted'`, with the reachable case named.

    Renaming two documents past each other makes `pairing` emit two `Adopt`s whose paths cross, so
    at the moment the first is applied an **active** row holds the path it wants. That is a genuine
    collision and must be reported. Widening the DELETE to retire whatever holds the path lets the
    first adoption proceed by destroying the live row instead — and every action commits on its
    own, so when the second half then fails to index (here, a file that is not UTF-8) the row it
    would have restored is simply gone. Measured with the scope removed: `pnk sync` exits **0**,
    `docs/b.md` sits on disk with its sidecar and **no row at all**, and because there is no
    retired row to find, `pnk doctor`'s own check for this cannot see it either.

    **The sync's own outcome is deliberately not asserted here.** The collision it raises on
    belonged to a separate defect, settled 20260831 by catching it narrowly in `_apply` — so the
    `contextlib.suppress` below now has nothing to suppress, and
    `test_a_rename_cycle_is_a_recorded_failure_with_a_remedy_rather_than_a_traceback` is what pins
    that. What this test pins is the older and wider claim: no live document loses its row, which
    had to hold however that defect was settled, and still has to.
    """
    write(kb, "a.md", "# Alpha\n\nAlpha body here.\n")
    write(kb, "b.md", "# Beta\n\nBeta body here.\n")
    run(kb)
    docs = kb / "docs"
    for one, two in (("a.md", "b.md"), (f"a.md{SIDECAR_SUFFIX}", f"b.md{SIDECAR_SUFFIX}")):
        (docs / one).rename(docs / "_swap")
        (docs / two).rename(docs / one)
        (docs / "_swap").rename(docs / two)
    (docs / "b.md").write_bytes(b"# Alpha\n\n\xff\xfe is not utf-8\n")

    with contextlib.suppress(sqlite3.IntegrityError):
        run(kb)

    # `index()` returns every row whatever its state, so asserting membership alone would be
    # satisfied by a soft-deleted row — a document that has left `pnk search`, which is the loss
    # this whole increment is about. The state is the assertion.
    surviving = {Path(str(row["path"])).name for row in index(kb) if row["state"] == "active"}
    assert surviving == {"a.md", "b.md"}


def test_a_rename_chain_syncs_and_every_document_keeps_its_id(kb: Path) -> None:
    """S16/S19, end to end: a rename chain now applies, and nothing is re-minted.

    `a → b`, `b → c`, `c → d` — **not** a cycle, and an applicable order plainly exists: move the
    last one first. `pairing` used to emit them in path order, so the first write landed on a path
    the next document still held, and `documents.path` being `UNIQUE` turned an ordinary `git mv`
    of three notes into `pnk sync` exiting 1 on a raw `sqlite3.IntegrityError` — after which
    `pnk search` answered from a path no longer on disk and `pnk doctor` reported every row `OK`,
    including `failures: none recorded`.

    **Ids are the assertion, not just the exit code.** A plan that dropped the rows and re-minted
    them would also sync cleanly and would destroy every inbound `pnk://` link — ULID permanence is
    the invariant here, and the counts `pnk sync` prints — `renamed`, with `minted` and
    `deleted` both zero — are what say
    which happened.
    """
    for name, body in (("a.md", "Alpha"), ("b.md", "Beta"), ("c.md", "Gamma")):
        write(kb, name, f"# {body}\n\n{body} body here.\n")
    run(kb)
    before = {Path(str(row["path"])).name: row["id"] for row in index(kb)}
    assert set(before) == {"a.md", "b.md", "c.md"}

    docs = kb / "docs"
    # Applied last-first on disk, which is the only way a person can do it without a temporary
    # name — and leaves exactly the walk `pairing` used to mis-order.
    for source, target in (("c.md", "d.md"), ("b.md", "c.md"), ("a.md", "b.md")):
        (docs / source).rename(docs / target)
        (docs / f"{source}{SIDECAR_SUFFIX}").rename(docs / f"{target}{SIDECAR_SUFFIX}")

    report = run(kb)

    assert report.renamed == 3, f"expected three renames, got {report}"
    assert report.minted == 0, "a re-mint would look like a clean sync and destroy every link"
    assert report.deleted == 0, "a retire-and-re-adopt would pass the id check by luck otherwise"
    after = {
        Path(str(row["path"])).name: row["id"] for row in index(kb) if row["state"] == "active"
    }
    assert after == {
        "b.md": before["a.md"],
        "c.md": before["b.md"],
        "d.md": before["c.md"],
    }


def failures(kb: Path) -> list[dict[str, object]]:
    """The `failures` table, which is what `pnk doctor` reads to decide whether to say `OK`."""
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        return [dict(row) for row in connection.execute("SELECT * FROM failures ORDER BY id")]
    finally:
        connection.close()


def test_a_rename_chain_whose_middle_document_fails_records_the_collision_instead_of_crashing(
    kb: Path,
) -> None:
    """S16's residue: ordering a chain only helps while every action in it succeeds.

    `_order_for_path_availability` makes action N+1 depend on action N having vacated a path, and
    the executor has no notion of that dependency. `_apply` catches a per-document failure and
    continues -- deliberately, so one broken file cannot block a thousand good ones -- but a caught
    failure **rolls back**, so the failed document keeps its old path and the next action in the
    chain writes straight onto it. `documents.path` is `UNIQUE`, so that raised a raw
    `sqlite3.IntegrityError` which escaped `_apply`, `_run`, `sync()` and `cli.main`'s
    `except PinakesError` alike: S16's whole symptom set again, now reached through the module's
    own first-class "failures are recorded, the run continues" path, and now landing *after*
    partial commits rather than before any.

    The chain here is the review's exact failing input: `a -> b`, `b -> c`, `c -> d` renamed
    last-first, with `d.md` saved in a non-UTF-8 encoding so the first ordered action fails at
    index time. Any caught class reaches this -- `OSError` from a file replaced between the walk
    and the write, a missing extractor, a budget refusal.

    **What this pins is the outcome, not the repair.** Rows are still left at paths that no longer
    exist on disk; the user has to act. The change is that `pnk sync` says so -- a `failures` row,
    a remedy, and a `pnk doctor` that no longer answers `failures: none recorded` -- instead of
    dying on a traceback that named nothing.
    """
    for name, body in (("a.md", "Alpha"), ("b.md", "Beta"), ("c.md", "Gamma")):
        write(kb, name, f"# {body}\n\n{body} body here.\n")
    run(kb)

    docs = kb / "docs"
    for source, target in (("c.md", "d.md"), ("b.md", "c.md"), ("a.md", "b.md")):
        (docs / source).rename(docs / target)
        (docs / f"{source}{SIDECAR_SUFFIX}").rename(docs / f"{target}{SIDECAR_SUFFIX}")
    (docs / "d.md").write_bytes(b"# Gamma\n\n\xff\xfe legacy encoding\n")

    report = run(kb)

    collisions = [
        (path, error, remedy)
        for path, error, remedy in report.failures
        if "PathStillHeldError" in error
    ]
    assert collisions, f"the collision was not recorded as a failure: {report.failures}"
    assert all("temporary name" in remedy for _, _, remedy in collisions), (
        "a recorded collision without a remedy is the traceback again, one layer up"
    )
    recorded = {str(row["path"]) for row in failures(kb)}
    assert recorded, "nothing in the failures table means `pnk doctor` still reports OK"
    assert "docs/d.md" in recorded, "the document that actually broke must be named too"
    # `cli` returns EXIT_FAILURE on `not report.ok`, and `ok` is `not self.failures`. Asserted
    # because the danger in catching an exception is trading a loud crash for a quiet success:
    # `pnk sync` must still exit non-zero here, and nothing else pins that it does.
    assert not report.ok, "a recorded collision that still exits 0 is worse than the traceback"


def test_a_rename_cycle_is_a_recorded_failure_with_a_remedy_rather_than_a_traceback(
    kb: Path,
) -> None:
    """The deferred half of S16/S19: two documents exchanging names, which no order can apply.

    `_order_for_path_availability` resolves a chain and cannot resolve a cycle -- correctly, since
    none of its orders is applicable. What changes here is only what the user is told when it
    happens: the collision is the database stating a fact about their tree, so it becomes a
    recorded failure naming the temporary-name remedy, where before it was
    `sqlite3.IntegrityError: UNIQUE constraint failed: documents.path` on stderr with no remedy and
    no `failures` row.

    **The cycle itself is still not applied, and that is deliberate** -- see
    `pairing._order_for_path_availability`. This is containment, not a fix for cycles.
    """
    write(kb, "a.md", "# Alpha\n\nAlpha body here.\n")
    write(kb, "b.md", "# Beta\n\nBeta body here.\n")
    run(kb)
    docs = kb / "docs"
    for one, two in (("a.md", "b.md"), (f"a.md{SIDECAR_SUFFIX}", f"b.md{SIDECAR_SUFFIX}")):
        (docs / one).rename(docs / "_swap")
        (docs / two).rename(docs / one)
        (docs / "_swap").rename(docs / two)

    report = run(kb)

    assert any("PathStillHeldError" in error for _, error, _ in report.failures), (
        f"the cycle still surfaced as something other than a recorded failure: {report.failures}"
    )
    assert failures(kb), "a cycle `pnk doctor` cannot see is the symptom this closes"
    assert not report.ok, "the cycle is contained, not resolved — `pnk sync` still exits non-zero"
    surviving = {Path(str(row["path"])).name for row in index(kb) if row["state"] == "active"}
    assert surviving == {"a.md", "b.md"}, "no live document may lose its row to a refused cycle"


def test_only_the_documents_path_collision_is_caught_and_every_other_constraint_escapes(
    kb: Path,
) -> None:
    """The narrow half of the decision, tested where the contract lives.

    `_apply` records a failure and continues. That is right for a broken *document* and wrong for a
    broken *invariant*, so exactly one integrity error may be caught. `store.py` carries several
    others -- `chunks(doc_id, ordinal)` and `nodes(kind, key)` UNIQUEs, the `links`/`edges` primary
    keys, CHECKs on `documents.state`, `links.origin` and `nodes.kind` -- and each of those fires
    only when Pinakes itself is wrong. Swallowing one would file a bug as a document's failure and
    let the run report success around it, which is the silent shape `docs/INVARIANTS.md` exists to
    prevent.

    Every exception here is raised by sqlite rather than constructed, because the discriminator
    reads `sqlite_errorname` and a hand-built `IntegrityError` carries none.
    """
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE documents (id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE, "
        "state TEXT NOT NULL CHECK (state IN ('active', 'deleted')))"
    )
    connection.execute("CREATE TABLE chunks (doc_id TEXT, ordinal INT, UNIQUE (doc_id, ordinal))")
    connection.execute("INSERT INTO documents VALUES ('one', 'docs/a.md', 'active')")
    connection.execute("INSERT INTO chunks VALUES ('one', 0)")

    def raised(sql: str) -> sqlite3.IntegrityError:
        with pytest.raises(sqlite3.IntegrityError) as caught:
            connection.execute(sql)
        return caught.value

    collision = raised("INSERT INTO documents VALUES ('two', 'docs/a.md', 'active')")
    assert _is_path_still_held(collision), "the one case a rename can legitimately produce"

    # The NOT NULL case earns its place: its message *does* contain `documents.path`, so it is the
    # only one of the four that the column substring alone lets through, and therefore the only one
    # that actually exercises the `sqlite_errorname` clause. Written after noticing that the other
    # three all fail on the column and would stay green with that clause deleted. `store.py`
    # declares `path TEXT NOT NULL UNIQUE`, so it is reachable on the real table, not a contrivance.
    for sql, why in (
        ("INSERT INTO documents VALUES ('one', 'docs/z.md', 'active')", "a duplicate primary key"),
        ("INSERT INTO documents VALUES ('three', 'docs/z.md', 'bogus')", "a CHECK breach"),
        ("INSERT INTO chunks VALUES ('one', 0)", "a chunks(doc_id, ordinal) collision"),
        (
            "INSERT INTO documents VALUES ('four', NULL, 'active')",
            "a NOT NULL breach on that very column",
        ),
    ):
        assert not _is_path_still_held(raised(sql)), (
            f"{why} means Pinakes is wrong; recording it as one document's failure hides a bug"
        )
    connection.close()


def test_an_integrity_error_from_another_constraint_still_escapes_apply(
    kb: Path, monkeypatch: Any
) -> None:
    """The same narrowing, witnessed through `_apply` rather than through the discriminator alone.

    `_is_path_still_held` returning False is only half the claim; the other half is that `_apply`
    re-raises on it instead of recording it. No fixture can reach a CHECK breach from a KB on disk
    -- that is the point of an invariant -- so the error is injected at `_index_document`.

    **The seam and what it leaves uncovered, named:** injecting the exception means this test never
    exercises the sqlite call that would really raise it, so it proves the *handler's* behaviour
    and not that any particular constraint is reachable. The exception is nonetheless a genuine one
    raised by sqlite, so its `sqlite_errorname` is real rather than asserted; and the reachable
    half -- the collision that a rename does produce -- is covered end to end by the two tests
    above.
    """
    probe = sqlite3.connect(":memory:")
    probe.execute("CREATE TABLE t (state TEXT CHECK (state IN ('active')))")
    with pytest.raises(sqlite3.IntegrityError) as caught:
        probe.execute("INSERT INTO t VALUES ('bogus')")
    breach = caught.value
    probe.close()
    assert breach.sqlite_errorname == "SQLITE_CONSTRAINT_CHECK"

    def explode(**_: Any) -> None:
        raise breach

    write(kb, "a.md", "# Alpha\n\nAlpha body here.\n")
    monkeypatch.setattr("pinakes.sync._index_document", explode)

    with pytest.raises(sqlite3.IntegrityError) as escaped:
        run(kb)

    assert escaped.value is breach, "an invariant breach must reach the top, not a failures row"
    assert not failures(kb), "recording it would let the run report success around a bug"


def test_the_population_walk_never_opens_a_document(kb: Path, monkeypatch: Any) -> None:
    """`walk_document_paths` answers *which* documents this KB collects, and `pnk doctor` is its
    only caller — the command you run when the KB is already broken. Opening files there would
    import the walk's own unreadable-file failure into the diagnostic.

    **All three of the skips are asserted, because two of them were not.** `_documents_only` skips
    the document hash, the sidecar pass and the unmatched-file probe, and the first version of this
    test could only see the first: its KB had never been synced, so there were no sidecars for the
    second pass to read, and no unmatched file for the third to open. Two clauses could be deleted
    with the whole suite green. The KB is synced here so sidecars exist, and it carries a file no
    `include` pattern matches so the probe has something to reach for.
    """
    write(kb, "a.md", "# Alpha\n\nAlpha body here.\n")
    write(kb, "b.md", "# Beta\n\nBeta body here.\n")
    run(kb)
    (kb / "docs" / "notes.rst").write_text(
        "Not matched by any include pattern.\n", encoding="utf-8"
    )
    assert list((kb / "docs").glob(f"*{SIDECAR_SUFFIX}")), (
        "the sidecar pass needs something to read"
    )

    def hashed(path: Path) -> str:
        raise AssertionError(f"the population walk hashed {path}")

    def probed(path: Path) -> bool:
        raise AssertionError(f"the population walk probed {path}")

    monkeypatch.setattr("pinakes.sync.hash_file", hashed)
    monkeypatch.setattr("pinakes.sync._indexable", probed)

    assert walk_document_paths(load(kb)) == {"docs/a.md", "docs/b.md"}


def test_a_paid_document_renamed_onto_a_retired_path_is_indexed(kb: Path, fake_paid: str) -> None:
    """The same collision on the *other* writer, which the first version of this fix missed.

    A paid-extracted, content-unchanged PDF that moves is not re-extracted: its chunks and vectors
    are already correct, so `_reindex_paid_document_in_place` moves the row's bookkeeping and
    nothing else. That writer sets `documents.path` too, and it had no retiring DELETE of its own —
    so renaming a paid document onto a path a retired row still held raised
    `sqlite3.IntegrityError` exactly as the free path used to, on a KB whose only distinguishing
    feature was that someone had paid for the extraction.

    Found by an adversarial probe that wrote the free case as its own control: the control passed
    and this did not, which is what made it a finding rather than a guess.
    """
    _add_pdf_support(kb)
    (kb / "docs" / "a.pdf").write_bytes(b"alpha bytes")
    (kb / "docs" / "b.pdf").write_bytes(b"beta bytes")
    assert run(kb, extract=fake_paid).embedded == 2

    # b.pdf goes away, so its row is retired while still holding `docs/b.pdf`.
    (kb / "docs" / "b.pdf").unlink()
    (kb / "docs" / f"b.pdf{SIDECAR_SUFFIX}").unlink()
    run(kb)

    # a.pdf is renamed onto that very path, its sidecar travelling with it.
    (kb / "docs" / "a.pdf").rename(kb / "docs" / "b.pdf")
    (kb / "docs" / f"a.pdf{SIDECAR_SUFFIX}").rename(kb / "docs" / f"b.pdf{SIDECAR_SUFFIX}")

    run(kb)  # free effective backend, so the paid in-place writer is what runs

    rows = [(row["path"], row["state"]) for row in index(kb)]
    assert rows == [("docs/b.pdf", "active")]


def test_a_moved_sidecar_never_leaves_a_document_without_a_row(kb: Path) -> None:
    """End to end, because this one exited 0 while losing a document and only a real sync shows it.

    `a.md`'s sidecar is moved onto `b.md`. `pair()` used to emit `RefreshMetadata` for that id at
    `a.md` and `Adopt` for the same id at `b.md`; applying both moved the row to `b.md` and left
    `a.md` on disk with no row — no failure recorded, exit 0, gone from `pnk search`. `origin/main`
    raised `IntegrityError` on the same input instead, so this was a loud failure turned silent,
    which is the exact regression that condemned the previous attempt at this fix.
    """
    write(kb, "a.md", "# Alpha\n\nAlpha body here.\n")
    write(kb, "b.md", "# Beta\n\nBeta body here.\n")
    run(kb)
    travelling = (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").read_text(encoding="utf-8")
    (kb / "docs" / f"b.md{SIDECAR_SUFFIX}").unlink()
    (kb / "docs" / f"a.md{SIDECAR_SUFFIX}").unlink()
    (kb / "docs" / f"b.md{SIDECAR_SUFFIX}").write_text(travelling, encoding="utf-8")

    run(kb)

    active = {Path(str(row["path"])).name for row in index(kb) if row["state"] == "active"}
    assert active == {"a.md", "b.md"}, "a document on disk lost its row"


def test_no_pure_rename_ever_leaves_the_index_half_written(kb: Path) -> None:
    """Every way three documents' names can be permuted, end to end.

    Five of the six permutations still raise — `documents.path` is UNIQUE and the adoptions cross,
    which is the collision this increment leaves to its own fix. What it does guarantee is that the
    raise costs nothing: the plan is no longer self-contradictory, so nothing has been applied by
    the time it fails. On `origin/main` the same swap commits a `SoftDelete` first and leaves a
    document retired, which is a KB that has silently lost something to a command that crashed.

    Scoped to a **pure** rename deliberately — no document added or deleted in the same sync. Mix a
    deletion in and its `SoftDelete` commits before the collision is reached, on both sides.
    """
    names = ("a.md", "b.md", "c.md")
    bodies = {name: f"# {name}\n\nBody of {name} with enough words.\n" for name in names}
    for permutation in itertools.permutations(names):
        if permutation == names:
            continue
        for name in names:
            write(kb, name, bodies[name])
        run(kb, rebuild=True)
        before = {str(r["path"]): (str(r["id"]), str(r["state"])) for r in index(kb)}

        docs = kb / "docs"
        staging = docs / "_perm"
        staging.mkdir()
        for name in names:
            (docs / name).rename(staging / name)
            (docs / f"{name}{SIDECAR_SUFFIX}").rename(staging / f"{name}{SIDECAR_SUFFIX}")
        for source, target in zip(names, permutation, strict=True):
            (staging / source).rename(docs / target)
            (staging / f"{source}{SIDECAR_SUFFIX}").rename(docs / f"{target}{SIDECAR_SUFFIX}")
        staging.rmdir()

        with contextlib.suppress(sqlite3.IntegrityError):
            run(kb)

        after = {str(r["path"]): (str(r["id"]), str(r["state"])) for r in index(kb)}
        assert after == before, f"{permutation}: the index was written before the sync failed"


def test_a_rename_that_frees_a_path_a_new_document_then_takes(kb: Path) -> None:
    """`git mv b.md c.md` with the sidecar, and an unrelated new `b.md` arrives at the freed name.

    Before this increment `pnk sync` recorded `SidecarError: c.md.pnk.yaml appeared after the walk
    had already read this directory`, told the user to *"run `pnk sync` again"*, and never indexed
    `c.md` — on that run or any later one. The document was on disk carrying a published id and
    unreachable from every query, and only `--rebuild` recovered it.

    It is the same shape as a moved sidecar, which is why the pairing guard fixes it: the index
    still called `b.md` that id while the sidecar had walked to `c.md`, so the plan asserted one id
    at two paths. Pinned here rather than left as a line in a plan, because a claim that something
    is fixed goes stale in silence and a test does not.
    """
    write(kb, "b.md", "# Beta\n\nBeta body here.\n")
    write(kb, "keep.md", "# Keep\n\nKeep body here.\n")
    run(kb)
    docs = kb / "docs"
    (docs / "b.md").rename(docs / "c.md")
    (docs / f"b.md{SIDECAR_SUFFIX}").rename(docs / f"c.md{SIDECAR_SUFFIX}")
    write(kb, "b.md", "# Brand new\n\nNothing to do with Beta at all.\n")

    report = run(kb)

    assert not report.failures, f"the walk recorded a failure: {report.failures}"
    active = {Path(str(row["path"])).name for row in index(kb) if row["state"] == "active"}
    assert active == {"b.md", "c.md", "keep.md"}


# --- S1: one unreadable document must not take the whole index with it -------------------------


def deny_reads_of(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """Make one document unreadable the way this repository requires: **injected, not chmod'd**.

    `chmod(0o000)` is ignored by root and produced a stat on CI's runner that neither succeeded nor
    raised, so fixtures went red for being unable to build their own precondition
    (`test_doctor.py`'s unreadable-partner test records it). `hash_file` reads a source with
    `read_bytes`, so that is the call to deny — and denying it by *name* leaves the sidecar beside
    it readable, which is the real shape: a `chmod` on a document does not touch its sidecar.
    """
    real = Path.read_bytes

    def denied(self: Path) -> bytes:
        if self.name == name:
            raise PermissionError(13, "Permission denied", str(self))
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", denied)


def test_one_unreadable_document_does_not_abort_the_sync_of_every_other(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S1, and the reason it was ranked as more than a cosmetic traceback.

    `hash_file` let the `PermissionError` escape `walk_sources`, so the walk died before anything
    was indexed: `pnk sync` exited 1 with a raw traceback and **no index database existed at all**.
    One file the process could not open made every other document in the KB unreachable.
    """
    write(kb, "a.md", "# Alpha\n\nFirst body.\n")
    write(kb, "b.md", "# Beta\n\nSecond body.\n")
    write(kb, "c.md", "# Gamma\n\nThird body.\n")
    deny_reads_of(monkeypatch, "c.md")

    report = run(kb)

    assert (kb / ".pinakes" / "index.db").exists(), "the walk died before the index was created"
    assert {Path(str(row["path"])).name for row in index(kb)} == {"a.md", "b.md"}
    assert [path for path, _error, _remedy in report.failures] == ["docs/c.md"]
    assert not report.ok, "an unreadable document must not let the run read as clean"


def test_a_held_unreadable_document_keeps_its_recorded_failure(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one exclusion from S7's clearing, and the reason `Skip` had to grow a `held` flag.

    An unchanged document is indexed and searchable, so a row still calling it failed is stale and
    goes. An unreadable one is *held* — nothing about it was attempted or verified this run, and
    its recorded failure is the last honest thing anyone knew about it. Both arrive as `Skip`, and
    clearing on `Skip` alone would have thrown the second away with the first.
    """
    write(kb, "keep.md", "# Keep\n\nText.\n")
    run(kb)
    (kb / "docs" / f"keep.md{SIDECAR_SUFFIX}").write_text(BAD_LINK, encoding="utf-8")
    run(kb)
    assert recorded_failures(kb) == [("docs/keep.md", "index")]

    deny_reads_of(monkeypatch, "keep.md")
    run(kb)

    assert recorded_failures(kb) == [("docs/keep.md", "index")]


def test_the_unreadable_failure_carries_a_remedy_that_names_both_ways_out(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure with an empty remedy is how this channel reports a bare `OSError`, and that is
    exactly what this used to be. The user can restore the permission or stop collecting the file;
    both belong in the message, because only one of them is available to someone syncing a tree
    they do not own."""
    write(kb, "a.md", "# Alpha\n\nFirst body.\n")
    write(kb, "c.md", "# Gamma\n\nThird body.\n")
    deny_reads_of(monkeypatch, "c.md")

    [(path, error, remedy)] = run(kb).failures

    assert path == "docs/c.md"
    assert "Permission denied" in error
    assert "chmod +r" in remedy
    assert "exclude" in remedy


def test_an_indexed_document_that_becomes_unreadable_is_held_not_deleted(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The half that makes skipping safe, and the reason a skip alone would have been a worse bug.

    `pair()` retires a row whose path the walk stops reporting, so without the hold a `chmod` would
    soft-delete the document and drop its chunks — the KB losing a file it still has, reported as
    `1 removed` on a run that exits about something else.
    """
    write(kb, "a.md", "# Alpha\n\nFirst body.\n")
    write(kb, "c.md", "# Gamma\n\nThird body.\n")
    run(kb)
    before = {str(row["path"]): dict(row) for row in index(kb)}
    assert before["docs/c.md"]["state"] == "active"

    deny_reads_of(monkeypatch, "c.md")
    report = run(kb)

    after = {str(row["path"]): dict(row) for row in index(kb)}
    assert after["docs/c.md"]["state"] == "active", "a permission change became a deletion"
    assert after["docs/c.md"]["content_hash"] == before["docs/c.md"]["content_hash"]
    assert report.deleted == 0
    assert chunks_for(kb, "docs/c.md") > 0

    # **A search, not a chunk count** — chunks can sit in the index while the document is
    # unreachable through the thing a user actually types.
    #
    # **`lexical_rank`, not mere presence, and that distinction was measured.** `FakeBackend`
    # returns an identical vector for every chunk, so the vector half of the fusion returns the
    # whole corpus and `docs/c.md` appears in `passages` for *any* query at all — the first version
    # of this assertion passed for the term "Zebrafish", which appears in no document. A non-`None`
    # `lexical_rank` is the part that requires the query to have matched this document's own
    # indexed text, and it is the part that goes silent when a held row is retired.
    connection = store.connect_ro(kb / ".pinakes" / "index.db")
    try:
        answered = search.search(connection, load(kb), "Gamma", backend=FakeBackend())
    finally:
        connection.close()

    held = [passage for passage in answered.passages if passage.path == "docs/c.md"]
    assert held, "a held document must still answer `pnk search` from the chunks it kept"
    assert any(passage.lexical_rank is not None for passage in held), (
        "matched only by the uniform fake vector, so this asserts nothing about the held chunks"
    )


def test_an_unreadable_documents_sidecar_is_never_offered_to_prune(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`orphaned_sidecars` prints `pnk doctor --prune` beside it, and pruning a live document's
    sidecar destroys a permanent id. The first version of this fix printed exactly that line for a
    document sitting on disk — found by running it, not by reading it."""
    write(kb, "c.md", "# Gamma\n\nThird body.\n")
    run(kb)
    deny_reads_of(monkeypatch, "c.md")

    assert run(kb).orphaned_sidecars == ()


def test_restoring_the_permission_returns_the_sync_to_clean(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The failure is a state of the tree, not a mark on the index: nothing is recorded that a
    later run has to undo."""
    write(kb, "a.md", "# Alpha\n\nFirst body.\n")
    write(kb, "c.md", "# Gamma\n\nThird body.\n")
    deny_reads_of(monkeypatch, "c.md")
    assert not run(kb).ok

    monkeypatch.undo()
    report = run(kb)

    assert report.ok
    assert {Path(str(row["path"])).name for row in index(kb)} == {"a.md", "c.md"}


def test_the_pre_commit_half_also_reports_an_unreadable_document(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--sidecars-only` returns before the index is touched at all, so the failure is recorded
    above that return. It is the half that runs in a pre-commit hook, which is the last place an
    unreadable document should pass in silence."""
    write(kb, "a.md", "# Alpha\n\nFirst body.\n")
    write(kb, "c.md", "# Gamma\n\nThird body.\n")
    deny_reads_of(monkeypatch, "c.md")

    report = run(kb, sidecars_only=True)

    assert [path for path, _error, _remedy in report.failures] == ["docs/c.md"]
    assert not report.ok


def test_a_rebuild_cannot_index_an_unreadable_document_and_does_not_invent_it_a_new_id(
    kb: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one place the fix is *worse* than the crash, measured rather than assumed — and the
    reason it is still the right trade.

    `--rebuild` starts from an empty database, so there is no row to hold: the unreadable document
    is simply not in the rebuilt index, where the old crash would have aborted before the swap and
    left the previous index intact. That loss is real. What makes it acceptable is that it is
    reported, non-zero, and **recoverable without cost**: the sidecar is committed truth for
    identity, it is untouched on disk, and the next readable sync re-adopts the *same* ULID rather
    than minting a fresh one. A rebuild that renamed the document's permanent id would be an
    invariant breach, and that is the assertion at the end.
    """
    write(kb, "a.md", "# Alpha\n\nFirst body.\n")
    write(kb, "c.md", "# Gamma\n\nThird body.\n")
    run(kb)
    original = {str(row["path"]): str(row["id"]) for row in index(kb)}["docs/c.md"]

    deny_reads_of(monkeypatch, "c.md")
    rebuilt = run(kb, rebuild=True)

    assert [path for path, _error, _remedy in rebuilt.failures] == ["docs/c.md"]
    assert {Path(str(row["path"])).name for row in index(kb)} == {"a.md"}
    assert rebuilt.orphaned_sidecars == (), "a document on disk is not an orphan to prune"

    monkeypatch.undo()
    recovered = run(kb)

    assert recovered.ok
    assert {str(row["path"]): str(row["id"]) for row in index(kb)}["docs/c.md"] == original


def test_a_symlink_that_resolves_to_nothing_is_reported_rather_than_skipped(kb: Path) -> None:
    """A sweep Low class: *invisible to both `sync` and `doctor`*.

    A dangling link and a loop both fail `is_file()`, so they took the same `continue` a directory
    takes and left no trace at all. `ls` shows the entry, which is what makes the silence
    expensive: the user cannot tell an ignored symlink from a file no include pattern matched, and
    both look like "the tool did not see my document".
    """
    (kb / "docs" / "real.md").write_text("# Real\n\nreal content\n", encoding="utf-8")
    (kb / "docs" / "dangling.md").symlink_to(kb / "docs" / "nowhere.md")
    (kb / "docs" / "loop_a.md").symlink_to(kb / "docs" / "loop_b.md")
    (kb / "docs" / "loop_b.md").symlink_to(kb / "docs" / "loop_a.md")

    report = run(kb)

    assert report.unresolvable_symlinks == (
        "docs/dangling.md",
        "docs/loop_a.md",
        "docs/loop_b.md",
    )
    said = "\n".join(report.lines())
    assert "symlink resolves to nothing" in said
    assert "docs/dangling.md" in said
    assert "docs/loop_a.md" in said


def test_a_symlink_to_a_real_directory_is_not_reported_as_unresolvable(kb: Path) -> None:
    """The control that actually reaches the branch, and it was red before `exists()` landed.

    `is_file()` is False for a symlink to a *directory* just as it is for a dangling one, so the
    first guard — `is_symlink()` under `not is_file()` — reported every healthy directory alias as
    *"resolves to nothing … its target is missing or the link loops"*, which is false on both
    counts. `exists()` follows the link: False for a missing target and False for a loop, True
    here, so this link takes the same `continue` a plain directory takes.

    Found by an adversarial review of the fix, not by writing it — the shape is the one the
    control above had named in prose and never built.
    """
    (kb / "docs" / "real").mkdir()
    (kb / "docs" / "real" / "page.md").write_text("# Real\n\nreal content\n", encoding="utf-8")
    (kb / "docs" / "alias.md").symlink_to(kb / "docs" / "real")

    report = run(kb)

    assert report.unresolvable_symlinks == ()
    assert "symlink resolves to nothing" not in "\n".join(report.lines())


def test_a_healthy_tree_says_nothing_about_symlinks(kb: Path) -> None:
    """The control. A report line that fired on every sync would be worse than the silence it
    replaced, and an assertion on the broken case alone cannot see that."""
    (kb / "docs" / "real.md").write_text("# Real\n\nreal content\n", encoding="utf-8")
    report = run(kb)
    assert report.unresolvable_symlinks == ()
    assert "symlink resolves to nothing" not in "\n".join(report.lines())


def test_a_symlink_to_a_real_document_is_indexed_not_reported(kb: Path) -> None:
    """A *working* file symlink is an ordinary document.

    **This control could not fail, and saying so is the point.** It was written against the risk
    that `unresolvable` might be populated by `is_symlink()` alone — but a symlink to a real file
    passes `is_file()`, so it never reaches the `is_symlink()` branch at all, and the assertion
    below held for both the correct guard and the broken one. The shape its first docstring named,
    `docs/alias -> docs/real`, is a *directory* link, which is the case that does reach the branch
    and is now tested by the function underneath. Kept, because it does pin that an aliased
    document is indexed rather than skipped; renamed in its reasoning, because a control that
    names one shape and builds another is worse than no control — it reports coverage that is not
    there.
    """
    real = kb / "elsewhere.md"
    real.write_text("# Real\n\nreal content\n", encoding="utf-8")
    (kb / "docs" / "alias.md").symlink_to(real)

    report = run(kb)

    assert report.unresolvable_symlinks == ()
    assert report.embedded == 1
