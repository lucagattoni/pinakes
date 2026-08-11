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
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pytest

from pinakes.cli import CALIBRATE_REMEDY, DEEP_OFFER, NO_ANSWER_SYNTHESISED, main
from pinakes.embed import (
    ModelInfo,
    Vectors,
    register_embedding_backend,
    register_reranker,
)
from pinakes.init import init
from pinakes.manifest import load
from pinakes.sync import SyncOptions, sync

FIXTURES = Path(__file__).parent / "fixtures" / "deep"

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
    ledger line is what spending looks like on disk, so a free command must leave none.

    **It cannot fail today and that is the point.** No paid code exists in this build; the
    assertion is a tripwire for E4, which adds a loop to this very command and shares `_retrieve`
    with it. The plan's own risk table names that route — "`pnk ask` without `--deep` starts
    spending" — and a tripwire laid after the fact is one laid too late.
    """
    assert main(["ask", "sourdough", "--kb", str(confident_kb)]) == 0
    out = capsys.readouterr().out

    assert "docs/b.md" in out
    assert "Sourdough needs a patient starter" in out
    assert "confidence: high" in out
    assert NO_ANSWER_SYNTHESISED in out
    assert "one synthesis call" in out
    assert DEEP_OFFER in out
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


def test_thresholds_with_reranking_switched_off_are_uncalibrated_too(
    kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The third of `_confidence`'s three `unknown` branches, so all three are covered here.

    E1's exit criteria ask that an uncalibrated KB says *which* branch it hit. It does — through
    `confidence_reason`, which is printed verbatim — and the single remedy sentence covers all
    three without the CLI re-deciding which one applies.
    """
    _calibrate(kb, low_below=0.1, high_above=0.4, fitted_for=FINGERPRINT)
    manifest_path = kb / "pinakes.toml"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8").replace(
            'rerank                = "local"', 'rerank                = "none"'
        ),
        encoding="utf-8",
    )

    assert main(["ask", "sourdough", "--kb", str(kb)]) == 0
    out = capsys.readouterr().out

    assert "confidence: unknown" in out
    assert "reranking is off" in out
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
    assert DEEP_OFFER not in out


@pytest.mark.parametrize(
    "fixture_name",
    ["kb", "confident_kb", "unconfident_kb"],
)
def test_every_confidence_branch_offers_the_flag_that_now_exists(
    fixture_name: str, request: pytest.FixtureRequest, capsys: pytest.CaptureFixture[str]
) -> None:
    """E1's rule, at the increment that turned it around.

    Until E4 a `--deep` merely *printed* was the same lie a `--deep` that parses and apologises
    would have been — the defect `0.20.1` fixed for `vector_tier`. The rule was never *say less*,
    it was **name only what this build can do**, so the increment implementing the flag is the one
    that prints it. What is asserted is that the offer and the parser agree.
    """
    root: Path = request.getfixturevalue(fixture_name)

    assert main(["ask", "sourdough", "--kb", str(root)]) == 0
    assert DEEP_OFFER in capsys.readouterr().out

    with pytest.raises(SystemExit) as exit_info:
        main(["ask", "--help"])
    assert exit_info.value.code == 0
    assert "--deep" in capsys.readouterr().out


def test_the_free_command_prices_the_run_it_offers(
    confident_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An offer to spend with no number beside it is the half of the sentence worth doubting.

    The estimator read here is E2's, and it is the *same* call `run_deep` makes before round 0 — so
    what is printed and what a reservation is checked against come from one place. Computing it
    spends nothing: the price table is package data, and the ledger stays absent.
    """
    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["escalation"]["cost_eur"] is not None

    assert main(["ask", "sourdough", "--kb", str(confident_kb)]) == 0
    assert f"€{payload['escalation']['cost_eur']}" in capsys.readouterr().out
    assert not (confident_kb / ".pinakes" / "ledger.jsonl").exists()


def test_a_price_it_cannot_compute_leaves_the_free_command_working(
    confident_kb: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The free path degrades and `--deep` refuses — deliberately different.

    This is the half that would otherwise turn a free retrieval into a failed command over the
    price of something nobody is buying. An unpriceable `[deep] model` stands in for every way the
    estimate can refuse; a stale table and an overflowing context window take the same branch.
    """
    path = confident_kb / "pinakes.toml"
    path.write_text(
        path.read_text(encoding="utf-8") + '\n[deep]\nmodel = "a-model-nobody-priced"\n',
        encoding="utf-8",
    )

    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["escalation"]["cost_eur"] is None

    assert main(["ask", "sourdough", "--kb", str(confident_kb)]) == 0
    out = capsys.readouterr().out
    assert DEEP_OFFER in out
    assert "cannot be computed here" in out

    # And the paid path, on the same KB, refuses instead of guessing.
    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--deep", "--yes"]) == 1


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
    # A string, never a float: JSON has no decimal type, and a float here would reintroduce the
    # representation error `Decimal` is used throughout the budget to avoid (INVARIANTS).
    #
    # **0.21, not the 0.26 the shipped defaults price**, because this KB chunks at
    # `max_tokens = 60` (the fixture above). The estimate reads the widths of the KB in front of it,
    # which is the whole reason it is not a constant: a KB retrieving twenty 2,000-token passages
    # has to be priced as one.
    assert payload["escalation"]["cost_eur"] == "0.21"
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


# ---------------------------------------------------------------------------------------------
# `--deep`, through the command (E4)
# ---------------------------------------------------------------------------------------------


@pytest.fixture
def scripted(monkeypatch: pytest.MonkeyPatch) -> Callable[..., "_Script"]:
    """Replace the one place production builds a transport, and hand the test what was sent.

    `deep/client.default_transport` exists so a test can swap the whole thing without reaching
    through two layers of CLI to a constructor that needs a real key — patched here rather than
    stubbing the loop, so everything between `run_ask` and the wire is the shipped code.
    """

    def _install(*names: str) -> "_Script":
        from pinakes.deep import client as deep_client

        script = _Script(*names)
        monkeypatch.setattr(deep_client, "default_transport", lambda: script)
        return script

    return _install


class _Script:
    """A transport replaying `tests/fixtures/deep/` bodies. The loop's own suite drives every
    branch of this; here it only has to make `--deep` reach the wire and come back."""

    def __init__(self, *names: str) -> None:
        self.entries: list[dict[str, object]] = []
        for name in names:
            raw = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))["responses"]
            self.entries.extend(raw)
        self.calls = 0

    def create(self, request: object) -> dict[str, object]:
        assert self.calls < len(self.entries), "the command made more calls than the script has"
        entry = self.entries[self.calls]
        self.calls += 1
        return entry


def test_deep_on_a_confident_kb_answers_in_one_call_and_says_what_it_cost(
    confident_kb: Path, scripted: Callable[..., _Script], capsys: pytest.CaptureFixture[str]
) -> None:
    """The cheap branch, end to end — the common case under D-28 option B.

    The free evidence is still printed above the answer, because round 0 is not replaced by the
    paid path: its passages *are* what the synthesis call reasoned over.
    """
    script = scripted("answer-cited")

    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--deep", "--yes"]) == 0
    out = capsys.readouterr().out

    assert script.calls == 1
    assert "docs/b.md" in out, "round 0's evidence is still shown"
    assert "confidence: high" in out
    assert "Retrieval confidence is fitted from a golden set" in out
    assert "one synthesis call" in out
    assert "1 paid call(s)" in out
    assert NO_ANSWER_SYNTHESISED not in out, "an answer was synthesised; the line would be false"
    assert (confident_kb / ".pinakes" / "ledger.jsonl").exists()


def test_deep_on_an_uncalibrated_kb_runs_and_names_the_bound_that_ended_it(
    kb: Path, scripted: Callable[..., _Script], capsys: pytest.CaptureFixture[str]
) -> None:
    """D-22 option E through the command: a stock KB is the uncalibrated case, it runs anyway, and
    the output says it stopped at a cap rather than at sufficiency."""
    scripted("loop-two-rounds", "loop-repeats-a-subproblem")

    assert main(["ask", "sourdough", "--kb", str(kb), "--deep", "--yes"]) == 0
    out = capsys.readouterr().out

    assert "confidence: unknown" in out
    assert "no calibrated signal" in out
    assert "pinakes.calibrate" in out
    assert "round 1 asked:" in out


def test_the_json_answer_object_carries_the_blocks_the_citations_and_the_money(
    confident_kb: Path, scripted: Callable[..., _Script], capsys: pytest.CaptureFixture[str]
) -> None:
    """`answer` stops being `null` and becomes an object — the same key either way (E1)."""
    scripted("answer-cited")

    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--deep", "--yes", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    answer = payload["answer"]
    assert set(answer) == {
        "text",
        "branch",
        "rounds_used",
        "stopped_by",
        "label",
        "partial",
        "calls",
        "estimated_eur",
        "spent_eur",
        "blocks",
    }
    assert answer["branch"] == "synthesis"
    assert answer["stopped_by"] == "answered"
    assert answer["calls"] == 1
    assert answer["partial"] is False
    assert answer["text"] == answer["blocks"][0]["text"]

    cited = answer["blocks"][0]["citations"]
    assert [c["number"] for c in cited] == [1, 2]
    assert {c["path"] for c in cited} <= {p["path"] for p in payload["passages"]}
    # Money as strings, at the cent the ledger stores — never floats (INVARIANTS).
    assert all(isinstance(answer[key], str) for key in ("estimated_eur", "spent_eur"))


def test_deep_needs_a_yes_when_nothing_can_answer_the_prompt(
    confident_kb: Path, scripted: Callable[..., _Script], capsys: pytest.CaptureFixture[str]
) -> None:
    """`confirm_above_eur` defaults to 0.01, so every `--deep` run owes a prompt (D-30) — and an
    unattended one without `--yes` refuses before the first call rather than assuming consent."""
    script = scripted("answer-cited")

    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--deep"]) == 1
    assert script.calls == 0
    assert "--yes" in capsys.readouterr().err


def test_a_question_nothing_matched_is_refused_before_anything_is_sent(
    confident_kb: Path, scripted: Callable[..., _Script], capsys: pytest.CaptureFixture[str]
) -> None:
    script = scripted("answer-cited")

    code = main(
        ["ask", "sourdough", "--kb", str(confident_kb), "--source-type", "pdf", "--deep", "--yes"]
    )
    assert code == 1
    assert script.calls == 0
    assert "nothing to reason over" in capsys.readouterr().err


def test_every_filter_still_narrows_the_paid_run(
    confident_kb: Path, scripted: Callable[..., _Script], capsys: pytest.CaptureFixture[str]
) -> None:
    """D-27: the filters narrow retrieval, and narrowing retrieval is what makes answering cost
    less. `-k` is the one that changes the *price*, so it is the one asserted on."""
    scripted("answer-cited")
    narrow = ["ask", "sourdough", "--kb", str(confident_kb), "--deep", "--yes", "--json", "-k", "2"]
    assert main(narrow) == 0
    payload = json.loads(capsys.readouterr().out)

    assert len(payload["passages"]) == 2
    narrowed = payload["answer"]["estimated_eur"]

    scripted("answer-cited")
    assert main(["ask", "sourdough", "--kb", str(confident_kb), "--deep", "--yes", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["answer"]["estimated_eur"] > narrowed
