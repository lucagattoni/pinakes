"""`pnk ask` end to end through the real CLI, with a registered fake backend.

**E1 of `plans/20260811_1358-deep-release.md`: the free half only.** There is no paid code in this
build, so every promise here is about what the command *says* — the evidence, the confidence, and
how much work answering the question would take. Two of them are the increment's whole point:

* the output never prints a flag nobody can type (`--deep` lands in E4), and
* it never lets a reader mistake evidence for a conclusion.

The fake reranker returns a **constant** score, so which confidence branch a KB takes is decided by
the thresholds this file writes into the manifest rather than by anything the retrieval does. That
is deliberate: the property under test is how `ask` renders a confidence value, and a test that had
to steer a real score into a band would be testing the reranker instead.
"""

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest

from pinakes.cli import CALIBRATE_REMEDY, DEEP_RELEASE_NOTICE, NO_ANSWER_SYNTHESISED, main
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

RERANK_SCORE = 0.5
"""What the fake reranker gives every passage. The thresholds below are placed around it."""

FINGERPRINT = "fake-reranker@e1"
"""`ModelInfo.fingerprint()` for the reranker registered here — what `fitted_for` must name.

Spelled out rather than computed from `info()`: a test that derives the expected value from the
same object it checks would still pass if `fingerprint()` started returning the empty string, and
the whole point of `fitted_for` is that a mismatch is caught.
"""


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
        return [RERANK_SCORE] * len(passages)

    def info(self) -> ModelInfo:
        return ModelInfo("fake", "fake-reranker", "e1", 0, 512)


@pytest.fixture
def kb(tmp_path: Path) -> Path:
    """Built through the real `init` + `sync`, uncalibrated — the stock template's state (M6)."""
    register_embedding_backend("fake", lambda section, offline: FakeBackend())
    register_reranker("fake", lambda section, offline: FakeReranker())

    result = init(tmp_path / "kb", now="20260811 15:00")
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
        "# Baking\n\nSourdough needs a patient starter, and sourdough rewards ranking it.\n",
        encoding="utf-8",
    )
    (result.root / "docs" / "c.txt").write_text(
        "Sourdough notes: retrieval of a starter from the fridge.\n", encoding="utf-8"
    )
    sync(load(result.root), options=SyncOptions(), now="20260811 15:01")
    return result.root


def _calibrate(kb: Path, *, low_below: float, high_above: float, fitted_for: str) -> None:
    """Append fitted `[retrieval.confidence]` thresholds. The template ships them commented out."""
    manifest_path = kb / "pinakes.toml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8")
        + f'\n[retrieval.confidence]\nfitted_for = "{fitted_for}"\n'
        + f"low_below  = {low_below}\nhigh_above = {high_above}\n",
        encoding="utf-8",
    )


@pytest.fixture
def confident_kb(kb: Path) -> Path:
    """Thresholds placed *below* the constant score, so every question comes back `high`."""
    _calibrate(kb, low_below=0.1, high_above=0.4, fitted_for=FINGERPRINT)
    return kb


@pytest.fixture
def unconfident_kb(kb: Path) -> Path:
    """Thresholds placed *above* the constant score, so every question comes back `low`."""
    _calibrate(kb, low_below=0.8, high_above=0.9, fitted_for=FINGERPRINT)
    return kb


# ---------------------------------------------------------------------------------------------
# What the command says
# ---------------------------------------------------------------------------------------------


def test_a_confident_kb_gets_cited_evidence_and_the_price_of_one_call(
    confident_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The cheap branch (§5): confident retrieval needs one synthesis call, and nothing was spent.

    "Spends nothing" is asserted as a fact about the KB, not only as a sentence in the output: a
    free command must leave no ledger behind, because a ledger line is what spending looks like on
    disk.
    """
    assert main(["ask", "sourdough", "--kb", str(confident_kb)]) == 0
    out = capsys.readouterr().out

    assert "docs/b.md" in out
    assert "Sourdough needs a patient starter" in out
    assert "confidence: high" in out
    assert NO_ANSWER_SYNTHESISED in out
    assert "one synthesis call" in out
    assert DEEP_RELEASE_NOTICE in out
    assert CALIBRATE_REMEDY not in out

    assert not (confident_kb / ".pinakes" / "ledger.jsonl").exists()


def test_a_low_confidence_kb_is_told_it_would_take_decomposition_not_one_call(
    unconfident_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["ask", "sourdough", "--kb", str(unconfident_kb)]) == 0
    out = capsys.readouterr().out

    assert "confidence: low" in out
    assert "decomposition into subquestions" in out
    assert "one synthesis call" not in out
    assert CALIBRATE_REMEDY not in out


def test_an_uncalibrated_kb_names_the_calibration_module_in_one_sentence(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """D-22 option E: it runs and says the signal is missing, rather than refusing.

    The remedy covers all three ways `_confidence` returns `unknown` at once — the printed
    *reason* is what says which one applies, and a second copy of that logic in the CLI could
    disagree with the first.
    """
    assert main(["ask", "sourdough", "--kb", str(kb)]) == 0
    out = capsys.readouterr().out

    assert "confidence: unknown" in out
    assert "no calibrated thresholds in the manifest" in out
    assert CALIBRATE_REMEDY in out
    assert out.count("python -m pinakes.calibrate") == 1
    assert "cannot be told from here" in out


def test_a_reranker_the_thresholds_were_not_fitted_for_is_uncalibrated_too(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The sub-question under D-22: a fingerprint mismatch behaves exactly like no thresholds."""
    _calibrate(kb, low_below=0.1, high_above=0.4, fitted_for="some-other-reranker@v9")
    assert main(["ask", "sourdough", "--kb", str(kb)]) == 0
    out = capsys.readouterr().out

    assert "confidence: unknown" in out
    assert "some-other-reranker@v9" in out
    assert CALIBRATE_REMEDY in out


def test_a_question_nothing_matches_is_not_told_to_calibrate(
    confident_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No passages is not an `unknown` to fix — it is a question the corpus does not cover.

    A KB with fitted thresholds still reports `unknown` here (`_confidence` returns it for an empty
    result), so without its own branch this output would tell a correctly-calibrated user to go and
    calibrate.
    """
    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--source-type", "pdf"]) == 0
    out = capsys.readouterr().out

    assert "no passages matched." in out
    assert NO_ANSWER_SYNTHESISED in out
    assert "nothing to answer from" in out
    assert CALIBRATE_REMEDY not in out
    assert DEEP_RELEASE_NOTICE not in out


@pytest.mark.parametrize(
    "fixture_name",
    ["kb", "confident_kb", "unconfident_kb"],
)
def test_no_confidence_branch_ever_prints_a_flag_that_does_not_exist(
    fixture_name: str, request: pytest.FixtureRequest, capsys: pytest.CaptureFixture[str]
) -> None:
    """E1's rule, checked on every branch and on both surfaces.

    A `--deep` that parses and then apologises is the defect `0.20.1` fixed for `vector_tier`, and
    a `--deep` merely *printed* is the same lie one layer out. It appears for the first time in E4,
    the increment that implements it.
    """
    root: Path = request.getfixturevalue(fixture_name)

    assert main(["ask", "sourdough", "--kb", str(root)]) == 0
    assert "--deep" not in capsys.readouterr().out

    assert main(["ask", "sourdough", "--kb", str(root), "--json"]) == 0
    assert "--deep" not in capsys.readouterr().out

    with pytest.raises(SystemExit):
        main(["ask", "--help"])
    assert "--deep" not in capsys.readouterr().out


def test_the_deep_flag_is_a_usage_error_rather_than_an_apology(kb: Path) -> None:
    """Nothing accepts `--deep` yet. Argparse refusing it *is* the honest surface."""
    with pytest.raises(SystemExit) as exit_info:
        main(["ask", "sourdough", "--kb", str(kb), "--deep"])
    assert exit_info.value.code == 2


# ---------------------------------------------------------------------------------------------
# The `--json` surface
# ---------------------------------------------------------------------------------------------


def test_json_carries_a_null_answer_and_an_escalation_block(
    confident_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """One schema whether or not the loop ran: `search`'s payload plus `answer` and `escalation`."""
    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert set(payload) == {
        "query",
        "confidence",
        "confidence_reason",
        "considered",
        "passages",
        "answer",
        "escalation",
    }
    assert payload["answer"] is None
    assert set(payload["escalation"]) == {"branch", "work", "cost_eur", "remedy"}
    assert payload["escalation"]["branch"] == "synthesis"
    assert payload["escalation"]["cost_eur"] is None
    assert payload["escalation"]["remedy"] is None


@pytest.mark.parametrize(
    ("fixture_name", "branch"),
    [("kb", "unknown"), ("confident_kb", "synthesis"), ("unconfident_kb", "decomposition")],
)
def test_the_escalation_branch_discriminates_the_confidence_value(
    fixture_name: str,
    branch: str,
    request: pytest.FixtureRequest,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A consumer reads `branch`, never the sentence — so `branch` must actually vary."""
    root: Path = request.getfixturevalue(fixture_name)
    assert main(["ask", "sourdough", "--kb", str(root), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["escalation"]["branch"] == branch


def test_json_and_the_human_output_agree_on_confidence_and_citations(
    unconfident_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both surfaces render one retrieval. If they can disagree, one of them is lying."""
    assert main(["ask", "sourdough", "--kb", str(unconfident_kb), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert main(["ask", "sourdough", "--kb", str(unconfident_kb)]) == 0
    human = capsys.readouterr().out

    assert f"confidence: {payload['confidence']} — {payload['confidence_reason']}" in human
    assert payload["passages"]
    for passage in payload["passages"]:
        assert f"({passage['citation']})" in human
    assert payload["escalation"]["work"] in human


# ---------------------------------------------------------------------------------------------
# D-27 — every filter `pnk search` takes, `pnk ask` takes
# ---------------------------------------------------------------------------------------------


def _passages(capsys: pytest.CaptureFixture[str]) -> list[dict[str, object]]:
    return json.loads(capsys.readouterr().out)["passages"]


@pytest.mark.parametrize(
    ("narrowing", "widening"),
    [
        (["--path-prefix", "docs/zzz"], ["--path-prefix", "docs/"]),
        (["--source-type", "pdf"], ["--source-type", "markdown"]),
        (["--modified-after", "21000101"], ["--modified-after", "20200101"]),
        (["--modified-before", "20200101"], ["--modified-before", "21000101"]),
        (["--tag", "physics"], []),
    ],
)
def test_every_filter_reaches_the_pipeline(
    kb: Path,
    narrowing: list[str],
    widening: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both directions, because a filter wired to *nothing* narrows everything to nothing.

    D-27: a user who can narrow a search expects to narrow a question, and narrowing retrieval is
    what makes answering it cost less.
    """
    assert main(["ask", "sourdough", "--kb", str(kb), "--json", *widening]) == 0
    assert _passages(capsys)

    assert main(["ask", "sourdough", "--kb", str(kb), "--json", *narrowing]) == 0
    assert _passages(capsys) == []


def test_the_tag_filter_keeps_a_document_that_carries_the_tag(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The positive half of `--tag`, which needs a tag authored into a sidecar to exist at all."""
    from dataclasses import replace

    from pinakes import sidecar as sidecar_module

    path = kb / "docs" / "b.md.pnk.yaml"
    owner = load(kb).kb.id
    sidecar_module.write(path, replace(sidecar_module.read(path, owner=owner), tags=("cooking",)))
    sync(load(kb), options=SyncOptions(), now="20260811 15:02")
    capsys.readouterr()

    assert main(["ask", "sourdough", "--kb", str(kb), "--json", "--tag", "cooking"]) == 0
    assert [p["path"] for p in _passages(capsys)] == ["docs/b.md"]


def test_k_bounds_how_many_passages_come_back(kb: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["ask", "sourdough", "--kb", str(kb), "--json"]) == 0
    assert len(_passages(capsys)) > 1

    assert main(["ask", "sourdough", "--kb", str(kb), "--json", "-k", "1"]) == 0
    assert len(_passages(capsys)) == 1


def test_a_bad_date_is_refused_with_the_format_it_wanted(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["ask", "x", "--kb", str(kb), "--modified-after", "yesterday"]) == 1
    assert "YYYYMMDD" in capsys.readouterr().err


def test_asking_outside_a_kb_says_how_to_fix_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["ask", "x", "--kb", str(tmp_path)]) == 1
    assert "pnk init" in capsys.readouterr().err
