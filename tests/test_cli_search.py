"""`pnk search` end to end through the real CLI, with a registered fake backend."""

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest

from pinakes.chunk import SOURCE_TYPES
from pinakes.cli import main
from pinakes.embed import (
    ModelInfo,
    Vectors,
    register_embedding_backend,
    register_reranker,
)
from pinakes.init import init
from pinakes.manifest import load
from pinakes.sync import SyncOptions, sync

VOCABULARY = ("retrieval", "ranking", "sourdough")


class FakeBackend:
    def embed(self, texts: Sequence[str]) -> Vectors:
        rows = [
            np.array([1.0 if w in t.lower() else 0.0 for w in VOCABULARY], dtype=np.float32)
            for t in texts
        ]
        if not rows:
            return np.zeros((0, len(VOCABULARY)), dtype=np.float32)
        return np.ascontiguousarray(np.vstack(rows), dtype=np.float32)

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def info(self) -> ModelInfo:
        return ModelInfo("fake", "fake-model", None, len(VOCABULARY), 512)


class FakeReranker:
    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        return [float(len(set(query.lower().split()) & set(p.lower().split()))) for p in passages]

    def info(self) -> ModelInfo:
        return ModelInfo("fake", "fake-reranker", None, 0, 512)


@pytest.fixture
def kb(tmp_path: Path) -> Path:
    """A KB built through the real `init` + `sync`, then pointed at the fake backend."""
    register_embedding_backend("fake", lambda section, offline: FakeBackend())
    register_reranker("fake", lambda section, offline: FakeReranker())

    result = init(tmp_path / "kb", now="20260725 17:40")
    manifest_path = result.root / "pinakes.toml"
    text = manifest_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sentence-transformers"', 'provider = "fake"')
    text = text.replace('model    = "BAAI/bge-small-en-v1.5"', 'model    = "fake-model"')
    text = text.replace("dim      = 384", f"dim      = {len(VOCABULARY)}")
    text = text.replace('model    = "BAAI/bge-reranker-base"', 'model    = "fake-reranker"')
    text = text.replace("max_tokens = 510", "max_tokens = 60")
    text = text.replace("overlap    = 64", "overlap    = 8")
    manifest_path.write_text(text, encoding="utf-8")

    (result.root / "docs" / "a.md").write_text(
        "# Retrieval\n\nHybrid retrieval fuses lexical and dense candidates.\n", encoding="utf-8"
    )
    (result.root / "docs" / "b.md").write_text(
        "# Baking\n\nSourdough needs a patient starter.\n", encoding="utf-8"
    )
    sync(load(result.root), options=SyncOptions(), now="20260725 17:41")
    return result.root


def test_search_prints_cited_passages_and_a_confidence_line(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["search", "sourdough", "--kb", str(kb)]) == 0
    out = capsys.readouterr().out
    assert "docs/b.md" in out
    assert "Sourdough needs a patient starter" in out
    assert "confidence: unknown" in out


def test_an_uncalibrated_kb_says_so_without_naming_a_command_that_does_not_exist(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The escalation notice may name only what a user can actually type.

    Until E1 this line advertised `pnk ask --deep`, which was neither a command nor a flag — in the
    sentence whose test is named for not doing that. E1 made `pnk ask` real and the notice named
    it; **E4 made `--deep` real and the notice names that too.** The rule was never *say less*, it
    was *name only what this build can do* — so this asserts both spellings resolve, and asks the
    parser rather than trusting the sentence.
    """
    main(["search", "sourdough", "--kb", str(kb)])
    out = capsys.readouterr().out
    assert "`pnk ask`" in out
    assert "`pnk ask --deep`" in out
    assert "planned for the deep release" not in out

    with pytest.raises(SystemExit) as exit_info:
        main(["ask", "--help"])
    assert exit_info.value.code == 0
    assert "--deep" in capsys.readouterr().out


def test_json_output_has_a_stable_shape(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["search", "retrieval", "--kb", str(kb), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert set(payload) == {"query", "confidence", "confidence_reason", "considered", "passages"}
    assert payload["passages"]
    assert set(payload["passages"][0]) == {
        "doc_id",
        "path",
        "title",
        "heading_path",
        "char_start",
        "char_end",
        "page_start",
        "page_end",
        "citation",
        "stale_extraction",
        "text",
        "rerank_score",
        "fused_score",
    }


def test_a_non_paged_source_reports_null_pages_and_the_offset_citation(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Markdown has no pages, and its citation keeps the character offsets it always rendered —
    `path:12-480` must not start meaning page 12 to page 480 because PDFs arrived (I8)."""
    main(["search", "retrieval", "--kb", str(kb), "--json"])
    passage = json.loads(capsys.readouterr().out)["passages"][0]

    assert passage["page_start"] is None
    assert passage["page_end"] is None
    assert passage["citation"].startswith(f"{passage['path']}:{passage['char_start']}-")
    assert ":p" not in passage["citation"]


def test_filters_reach_the_pipeline(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["search", "sourdough", "--kb", str(kb), "--path-prefix", "docs/a", "--json"])
    assert json.loads(capsys.readouterr().out)["passages"] == []


def test_a_bad_date_is_a_usage_level_error(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["search", "x", "--kb", str(kb), "--modified-after", "yesterday"]) == 1
    assert "YYYYMMDD" in capsys.readouterr().err


def test_searching_outside_a_kb_says_how_to_fix_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["search", "x", "--kb", str(tmp_path)]) == 1
    assert "pnk init" in capsys.readouterr().err


def test_the_readme_quickstart_works(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The three commands the README promises, run through the real CLI in order."""
    register_embedding_backend("fake", lambda section, offline: FakeBackend())
    register_reranker("fake", lambda section, offline: FakeReranker())

    root = tmp_path / "my-kb"
    assert main(["init", str(root)]) == 0

    manifest_path = root / "pinakes.toml"
    text = manifest_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sentence-transformers"', 'provider = "fake"')
    text = text.replace('model    = "BAAI/bge-small-en-v1.5"', 'model    = "fake-model"')
    text = text.replace("dim      = 384", f"dim      = {len(VOCABULARY)}")
    text = text.replace('model    = "BAAI/bge-reranker-base"', 'model    = "fake-reranker"')
    manifest_path.write_text(text, encoding="utf-8")

    (root / "docs" / "note.md").write_text("# Note\n\nAbout retrieval.\n", encoding="utf-8")

    assert main(["sync", "--kb", str(root)]) == 0
    capsys.readouterr()
    assert main(["search", "retrieval", "--kb", str(root)]) == 0
    assert "docs/note.md" in capsys.readouterr().out


@pytest.mark.parametrize("bad", ["-1", "-100", "0"])
@pytest.mark.parametrize("command", ["search", "ask"])
def test_k_below_one_is_a_usage_error_on_both_retrieval_commands(
    kb: Path, capsys: pytest.CaptureFixture[str], command: str, bad: str
) -> None:
    """Sweep S8 and S9: one missing boundary check, and the two ends it was seen from.

    `-k` was `type=int` with nothing else, so the value flowed to whatever the command reached.
    `search` reached `passages[:final_k]` and answered *confidently and wrongly* — `-k -1` returned
    every passage but the last at exit 0, `-k -100` returned none and called it "no passages
    matched." `ask` reached `deep/estimate.py:_positive`, which rejected it as an unhandled
    `ValueError` traceback. Parametrised over both commands because the fix is one guard and the
    pair is what proves it sits at the boundary rather than on the arm that happened to crash.

    `0` is in the bad set for a reason of its own: `search.py` reads `limit or
    manifest.retrieval.final_k`, so a falsy `0` silently meant "the manifest's default". Asking for
    nothing and receiving ten passages is the same quiet wrong as the negative arm.
    """
    with pytest.raises(SystemExit) as exit_info:
        main([command, "retrieval", "--kb", str(kb), "-k", bad])
    assert exit_info.value.code == 2
    assert "must be 1 or more" in capsys.readouterr().err


def test_a_positive_k_still_bounds_the_result(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The guard rejects `< 1` and nothing else — the control for the test above.

    Without this, deleting the comparison and refusing *every* `-k` would leave the rejection
    tests green while the flag no longer worked at all.
    """
    assert main(["search", "retrieval", "--kb", str(kb), "-k", "1"]) == 0
    assert len([line for line in capsys.readouterr().out.splitlines() if line.startswith("[")]) == 1


@pytest.mark.parametrize("command", ["search", "ask"])
def test_a_mistyped_source_type_is_a_usage_error_not_an_empty_result(
    kb: Path, capsys: pytest.CaptureFixture[str], command: str
) -> None:
    """A sweep Low class: `--source-type` went straight into `d.source_type = ?`.

    A transposition matched no row, so `pnk search --source-type markdwon` printed "no passages
    matched." at exit 0 — byte for byte what an empty KB prints, and what a *correct* filter over
    a corpus holding none of that type prints. The user is in the one state of the three they can
    fix, and nothing in the output distinguishes it.

    Parametrised over both commands because they share `_retrieval_arguments`; a guard on one arm
    would leave the other silently wrong, which is exactly how S8 and S9 came to be two findings.
    """
    with pytest.raises(SystemExit) as exit_info:
        main([command, "retrieval", "--kb", str(kb), "--source-type", "markdwon"])
    assert exit_info.value.code == 2
    error = capsys.readouterr().err
    assert "not a source type" in error
    assert "markdown, code, pdf, text" in error


def test_every_valid_source_type_is_still_accepted(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The control. A guard that refused everything would leave the test above green while
    `--source-type` stopped working, and `markdown` is the value the fixture's corpus actually
    holds — so this asserts a result comes back, not merely that exit is 0."""
    for source_type in SOURCE_TYPES:
        assert main(["search", "retrieval", "--kb", str(kb), "--source-type", source_type]) == 0
    assert main(["search", "retrieval", "--kb", str(kb), "--source-type", "markdown"]) == 0
    assert "docs/a.md" in capsys.readouterr().out


def test_an_empty_kb_does_not_blame_filters_the_user_never_passed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A sweep Low class: the reason read *"nothing matched the filters"* with no filters given.

    It sends a user to widen a filter they never wrote, for a KB that holds nothing to search. The
    two states need opposite actions, and `Filters()` is what every unfiltered search passes — so
    the emptiness of the allowed set cannot tell them apart on its own.
    """
    register_embedding_backend("fake", lambda section, offline: FakeBackend())
    register_reranker("fake", lambda section, offline: FakeReranker())
    result = init(tmp_path / "empty", now="20260725 17:40")
    manifest_path = result.root / "pinakes.toml"
    text = manifest_path.read_text(encoding="utf-8")
    text = text.replace('provider = "sentence-transformers"', 'provider = "fake"')
    text = text.replace('model    = "BAAI/bge-small-en-v1.5"', 'model    = "fake-model"')
    text = text.replace("dim      = 384", f"dim      = {len(VOCABULARY)}")
    text = text.replace('model    = "BAAI/bge-reranker-base"', 'model    = "fake-reranker"')
    manifest_path.write_text(text, encoding="utf-8")
    sync(load(result.root), options=SyncOptions(), now="20260725 17:41")

    assert main(["search", "anything", "--kb", str(result.root)]) == 0
    out = capsys.readouterr().out
    assert "no active documents" in out
    assert "filters" not in out


def test_a_filter_that_excludes_everything_still_says_so(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The other arm, and the control for the test above: with a filter actually given, the
    original sentence is the right one and must survive. `pdf` is valid, so this passes the guard
    and reaches the empty-allowed-set branch — the corpus holds only markdown."""
    assert main(["search", "retrieval", "--kb", str(kb), "--source-type", "pdf"]) == 0
    assert "nothing matched the filters" in capsys.readouterr().out
