"""Backends: the registry is open, missing extras fail helpfully, and dims must agree.

Unit tests use a deterministic fake. The `model`-marked tests below exercise real weights and skip
unless they are already cached — a clean checkout must never be blocked on a 1GB download, while CI
(which caches `HF_HOME`) runs them for real.
"""

import json
import socket
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, NoReturn
from unittest.mock import Mock

import numpy as np
import pytest

from pinakes.embed import (
    FASTEMBED,
    SENTENCE_TRANSFORMERS,
    ModelInfo,
    Vectors,
    hf_cache_dir,
    load_backend,
    load_reranker,
    register_embedding_backend,
    registered_embedding_providers,
)
from pinakes.errors import BackendMissingError, BackendUnknownError, EmbeddingError
from pinakes.manifest import EmbeddingSection, RerankSection

DIM = 8


class FakeBackend:
    """Deterministic embeddings: a hash of the text, so tests can assert exact rankings."""

    def __init__(self, dim: int = DIM) -> None:
        self._dim = dim

    def embed(self, texts: Sequence[str]) -> Vectors:
        rows = [
            np.array(
                [((hash(text) >> (bit * 3)) % 17) / 17 for bit in range(self._dim)],
                dtype=np.float32,
            )
            for text in texts
        ]
        if not rows:
            return np.zeros((0, self._dim), dtype=np.float32)
        return np.ascontiguousarray(np.vstack(rows), dtype=np.float32)

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    def info(self) -> ModelInfo:
        return ModelInfo("fake", "fake-model", "rev1", self._dim, 512)


def _section(provider: str = "fake", dim: int = DIM) -> EmbeddingSection:
    return EmbeddingSection(provider=provider, model="fake-model", dim=dim, revision=None)


@pytest.fixture(autouse=True)
def fake_provider() -> None:
    # Fixed width, deliberately *not* `section.dim`: a fake that adopts whatever the manifest
    # claims can never disagree with it, so the dim-mismatch check would be untestable.
    register_embedding_backend("fake", lambda section, offline: FakeBackend())


def test_the_registry_is_open_so_tests_can_supply_a_backend() -> None:
    assert "fake" in registered_embedding_providers()
    assert SENTENCE_TRANSFORMERS in registered_embedding_providers()
    assert FASTEMBED in registered_embedding_providers()

    backend = load_backend(_section())
    assert backend.embed(["a", "b"]).shape == (2, DIM)
    assert backend.embed([]).shape == (0, DIM)


def test_a_dim_disagreement_is_a_hard_error() -> None:
    """Vectors of different widths cannot be compared; storing them would poison the index."""
    with pytest.raises(EmbeddingError) as exc_info:
        load_backend(_section(dim=DIM + 1))
    assert "--rebuild" in exc_info.value.remedy


def test_an_unknown_provider_lists_the_known_ones() -> None:
    with pytest.raises(BackendUnknownError) as exc_info:
        load_backend(_section(provider="telepathy"))
    assert SENTENCE_TRANSFORMERS in exc_info.value.remedy


def _no_module_installed(name: str) -> ModuleSpec | None:
    """A `find_spec` replacement reporting nothing installed — no sibling to recommend."""
    return None


def _only_fastembed_installed(name: str) -> ModuleSpec | None:
    """A `find_spec` replacement reporting `fastembed` installed and nothing else — the `[light]`
    machine item 2 describes."""
    return Mock(spec=ModuleSpec) if name == "fastembed" else None


def _refuse_import(*names: str) -> Callable[..., ModuleType]:
    """A `builtins.__import__` replacement that fails only for modules starting with `names`."""
    import builtins

    real_import = builtins.__import__

    def refuse(
        name: str,
        # Parameter names mirror `__import__` exactly, shadowing the builtins on purpose.
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> ModuleType:
        if any(name.startswith(refused) for refused in names):
            raise ImportError(f"no module named {name}")
        return real_import(name, globals, locals, fromlist, level)

    return refuse


def test_a_missing_extra_names_the_install_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """A core-only install is a supported state — it just has to say so precisely (§4.5).

    No sibling provider is importable here (`find_spec` is forced to `None` for everything), so
    there is nothing to recommend switching to — the message falls back to the plain install line.
    """
    import builtins

    monkeypatch.setattr(builtins, "__import__", _refuse_import("sentence_transformers"))
    monkeypatch.setattr("importlib.util.find_spec", _no_module_installed)
    with pytest.raises(BackendMissingError) as exc_info:
        load_backend(_section(provider=SENTENCE_TRANSFORMERS))
    assert exc_info.value.extra == "st"
    assert exc_info.value.alternative is None
    assert 'uv add "pinakes[st]"' in exc_info.value.remedy


def test_a_missing_extra_with_an_installed_alternative_names_it_instead(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The item 2 case: `[light]` is present (`fastembed` importable), `sentence-transformers` is
    not. The message must name the free fix — flip `provider` in `pinakes.toml` — and must not
    also recommend the 2 GB install it exists to avoid: naming `fastembed` while still saying
    `uv add "pinakes[st]"` would pass a naive contains-check on the positive half alone and still
    be the defect.
    """
    import builtins

    monkeypatch.setattr(builtins, "__import__", _refuse_import("sentence_transformers"))
    monkeypatch.setattr("importlib.util.find_spec", _only_fastembed_installed)
    with pytest.raises(BackendMissingError) as exc_info:
        load_backend(_section(provider=SENTENCE_TRANSFORMERS))
    remedy = exc_info.value.remedy

    # Positive half: names the alternative and where to change it.
    assert exc_info.value.alternative == FASTEMBED
    assert "fastembed" in remedy
    assert "[embedding]" in remedy

    # Negative half: never also points at the install it exists to avoid.
    assert "torch" not in remedy.lower()
    assert "pinakes[st]" not in remedy
    assert "uv add" not in remedy


def test_a_missing_reranker_extra_gets_the_same_alternative_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`[rerank]` carries its own `provider` and defaults to `sentence-transformers` too — the same
    `[light]` install fails the same way loading the reranker, and the fix is symmetric: one
    message names both `[embedding]` and `[rerank]`, since a `[light]` install needs both flipped.
    """
    import builtins

    monkeypatch.setattr(builtins, "__import__", _refuse_import("sentence_transformers"))
    monkeypatch.setattr("importlib.util.find_spec", _only_fastembed_installed)
    with pytest.raises(BackendMissingError) as exc_info:
        load_reranker(RerankSection(provider=SENTENCE_TRANSFORMERS, model="m", revision=None))
    remedy = exc_info.value.remedy
    assert exc_info.value.alternative == FASTEMBED
    assert "[embedding]" in remedy
    assert "[rerank]" in remedy
    assert "torch" not in remedy.lower()
    assert "pinakes[st]" not in remedy


def test_reranker_registry_rejects_unknown_providers() -> None:
    with pytest.raises(BackendUnknownError):
        load_reranker(RerankSection(provider="telepathy", model="m", revision=None))


def test_model_fingerprint_matches_what_fitted_for_records() -> None:
    assert ModelInfo("p", "m", "abc", 4, 512).fingerprint() == "m@abc"
    assert ModelInfo("p", "m", None, 4, 512).fingerprint() == "m"


def test_weights_resolve_under_the_shared_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One copy of the weights per machine, not per KB — and never fastembed's $TMPDIR default."""
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    assert hf_cache_dir() == tmp_path / "hf" / "hub"

    monkeypatch.delenv("HF_HOME", raising=False)
    assert hf_cache_dir() == Path.home() / ".cache" / "huggingface" / "hub"
    assert "fastembed_cache" not in str(hf_cache_dir())


def _runnable(fragment: str) -> bool:
    """Both halves must hold: the backend importable *and* its weights already cached.

    Checking only the cache was wrong — the weights live in a shared, machine-wide directory, so
    they can be present in an environment that has no fastembed installed at all. The test then ran
    and failed with `BackendMissingError` instead of skipping.
    """
    from importlib.util import find_spec

    if find_spec("fastembed") is None:
        return False
    cache = hf_cache_dir()
    return cache.exists() and any(fragment in entry.name for entry in cache.iterdir())


@pytest.mark.model
@pytest.mark.skipif(not _runnable("bge-small"), reason="fastembed or its weights absent")
def test_real_embedding_backend_agrees_with_the_manifest() -> None:
    section = EmbeddingSection(
        provider=FASTEMBED, model="BAAI/bge-small-en-v1.5", dim=384, revision=None
    )
    backend = load_backend(section)
    info = backend.info()

    assert info.dim == 384
    assert 0 < info.max_seq_length <= 512
    # Assert the relationship, not a magic number: the real BPE count for that phrase is 3, and
    # an earlier ">" here was a guess that the real model promptly falsified.
    short = backend.count_tokens("retrieval augmented generation")
    assert short >= 3
    assert backend.count_tokens("retrieval augmented generation " * 10) > short

    vectors = backend.embed(["a passage about retrieval", "an unrelated passage"])
    assert vectors.shape == (2, 384)
    assert vectors.dtype == np.float32


@pytest.mark.model
@pytest.mark.skipif(not _runnable("bge-reranker"), reason="fastembed or its weights absent")
def test_real_reranker_orders_by_relevance() -> None:
    reranker = load_reranker(
        RerankSection(provider=FASTEMBED, model="BAAI/bge-reranker-base", revision=None)
    )
    scores = reranker.score(
        "how does hybrid retrieval work?",
        ["Hybrid retrieval fuses BM25 and vector search.", "A recipe for sourdough bread."],
    )
    assert len(scores) == 2
    assert scores[0] > scores[1]
    assert reranker.score("q", []) == []


# ── `--offline` with fastembed: the cache must hold *this* model, or the load fails typed ─────────
#
# F2 (measured 20261019 against 0.32.7): `pnk doctor` is meant to be offline, yet with the embedder
# cached and the reranker not it fetched 1.1 GB — the old guard only asked whether the cache
# *directory* existed — and with HF_HUB_OFFLINE=1 it crashed with a bare `ValueError`.
#
# Two kinds of test, and the difference matters. The "sealed" ones run the real fastembed against
# a temporary cache and forbid every way out of the process, so "nothing was fetched" is measured,
# not inferred. The stub ones swap only the fastembed *class* for a recorder, to pin exactly what
# the loader passes it. Neither touches the real Hugging Face cache: `HF_HOME` is a `tmp_path`.

_FASTEMBED_MODEL = {"embedding": "BAAI/bge-small-en-v1.5", "reranker": "BAAI/bge-reranker-base"}
_OFFLINE_REMEDY = "Run once without --offline to populate the cache."
# For everything that is not "fastembed could not find a usable local copy (usually: absent)".
# Going online fetches an absent model but does not repair a truncated one (fastembed tries the
# local snapshot first online too), and the class cannot tell them apart (transformers raises a
# plain OSError for a miss and for other failures), so the remedy names both readings.
_UNLOADABLE_REMEDY = (
    "Fix the cause named above. If the model is not in the cache, run once without --offline to "
    "populate it; if its files are damaged, delete its folder under {cache} first."
)


def _load_fastembed_kind(kind: str, *, offline: bool) -> Any:
    if kind == "embedding":
        return load_backend(
            EmbeddingSection(
                provider=FASTEMBED, model=_FASTEMBED_MODEL[kind], dim=384, revision=None
            ),
            offline=offline,
        )
    return load_reranker(
        RerankSection(provider=FASTEMBED, model=_FASTEMBED_MODEL[kind], revision=None),
        offline=offline,
    )


class _NetworkReached(BaseException):
    """Not an `Exception` on purpose: fastembed retries and sleeps on those, hiding a reach."""


@dataclass
class _Sealed:
    hub: Path
    reached: list[str] = field(default_factory=list[str])


@pytest.fixture
def sealed_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> _Sealed:
    """An empty cache directory that exists, and a process that may not reach the network."""
    download = pytest.importorskip("fastembed.common.model_management")
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    # With HF_HUB_OFFLINE set fastembed goes local-only by itself, and these tests would pass on
    # code that ignores `offline` altogether — which is the defect.
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    sealed = _Sealed(hub=tmp_path / "hf" / "hub")
    sealed.hub.mkdir(parents=True)

    def forbid(way: str) -> Callable[..., NoReturn]:
        def refuse(*args: object, **kwargs: object) -> NoReturn:
            sealed.reached.append(way)
            raise _NetworkReached(way)

        return refuse

    # The calls fastembed makes to learn what a repo holds and to fetch it...
    monkeypatch.setattr(download, "model_info", forbid("model_info"))
    monkeypatch.setattr(download, "list_repo_tree", forbid("list_repo_tree"))
    local_snapshot_download = download.snapshot_download

    def snapshot_download_local_only(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("local_files_only") is not True:
            sealed.reached.append("snapshot_download without local_files_only")
            raise _NetworkReached("snapshot_download")
        return local_snapshot_download(*args, **kwargs)

    monkeypatch.setattr(download, "snapshot_download", snapshot_download_local_only)
    # ...and, for anything else, the process cannot open a socket at all.
    monkeypatch.setattr(socket, "getaddrinfo", forbid("getaddrinfo"))
    monkeypatch.setattr(socket, "create_connection", forbid("create_connection"))
    monkeypatch.setattr(socket.socket, "connect", forbid("socket.connect"))
    return sealed


def _plant(hub: Path, repo_id: str, files: Mapping[str, bytes]) -> None:
    """An entry as `huggingface_hub` lays it out: `refs/main` names `snapshots/<sha>/`."""
    repo = hub / f"models--{repo_id.replace('/', '--')}"
    (repo / "refs").mkdir(parents=True)
    (repo / "refs" / "main").write_text("abc123")
    for name, data in files.items():
        target = repo / "snapshots" / "abc123" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def _tree(root: Path) -> dict[str, bytes | None]:
    """Every path under `root` with its bytes (`None` for a directory) — the cache, as a value."""
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_offline_a_model_missing_from_an_existing_cache_fails_typed_and_fetches_nothing(
    sealed_cache: _Sealed, kind: str
) -> None:
    """The directory exists and this model is not in it: `EmbeddingError`, no traffic, no weights.

    Before: the directory check passed and fastembed went to the network (reached `model_info`).
    """
    with pytest.raises(EmbeddingError) as exc_info:
        _load_fastembed_kind(kind, offline=True)

    assert sealed_cache.reached == []
    assert [path for path in sealed_cache.hub.rglob("*") if path.is_file()] == []
    assert _FASTEMBED_MODEL[kind] in exc_info.value.message


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_the_offline_refusal_keeps_its_wording_and_its_remedy(
    sealed_cache: _Sealed, kind: str
) -> None:
    with pytest.raises(EmbeddingError) as exc_info:
        _load_fastembed_kind(kind, offline=True)

    assert exc_info.value.message.startswith("--offline was requested but ")
    assert str(sealed_cache.hub) in exc_info.value.message
    assert exc_info.value.remedy == _OFFLINE_REMEDY


def test_another_model_in_the_cache_does_not_stand_in_for_the_missing_one(
    sealed_cache: _Sealed,
) -> None:
    """The measured case: the embedder cached, the reranker not; the embedder is untouched."""
    _plant(
        sealed_cache.hub,
        "qdrant/bge-small-en-v1.5-onnx-q",
        {"config.json": b"{}", "model_optimized.onnx": b"embedder weights"},
    )
    before = _tree(sealed_cache.hub)

    with pytest.raises(EmbeddingError):
        _load_fastembed_kind("reranker", offline=True)

    assert sealed_cache.reached == []
    assert _tree(sealed_cache.hub) == before


def test_a_cached_model_that_cannot_be_read_fails_typed_too(sealed_cache: _Sealed) -> None:
    """Present but broken (an interrupted download): onnxruntime raises; that must not escape."""
    json_files = (
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
    )
    _plant(
        sealed_cache.hub,
        _FASTEMBED_MODEL["reranker"],
        {name: b"{}" for name in json_files} | {"onnx/model.onnx": b"not an onnx file"},
    )
    before = _tree(sealed_cache.hub)

    with pytest.raises(EmbeddingError) as exc_info:
        _load_fastembed_kind("reranker", offline=True)

    assert sealed_cache.reached == []
    assert _tree(sealed_cache.hub) == before
    # Going online cannot repair this: fastembed looks at the local snapshot first online too. So
    # the remedy says what will, and the message makes no claim about the cache.
    assert "model cache" not in exc_info.value.message
    assert "InvalidProtobuf" in exc_info.value.message
    assert exc_info.value.remedy == _UNLOADABLE_REMEDY.format(cache=sealed_cache.hub)


def test_a_failed_offline_load_removes_the_scratch_directory_fastembed_made(
    sealed_cache: _Sealed,
) -> None:
    """fastembed makes `<cache>/tmp` before it finds nothing; `hf cache scan` warns about it."""
    with pytest.raises(EmbeddingError):
        _load_fastembed_kind("reranker", offline=True)

    assert list(sealed_cache.hub.iterdir()) == []


def test_a_scratch_directory_that_was_already_there_is_left_alone(sealed_cache: _Sealed) -> None:
    (sealed_cache.hub / "tmp").mkdir()

    with pytest.raises(EmbeddingError):
        _load_fastembed_kind("reranker", offline=True)

    assert (sealed_cache.hub / "tmp").is_dir()


def _stub_fastembed(
    monkeypatch: pytest.MonkeyPatch,
    *,
    error: BaseException | None = None,
    before_failing: Callable[[], None] | None = None,
) -> list[dict[str, Any]]:
    """Swap fastembed's two model classes for one recorder; return what it was built with.

    `before_failing` runs just before `error` is raised: what a half-finished load leaves behind.
    """
    pytest.importorskip("fastembed.rerank.cross_encoder")
    calls: list[dict[str, Any]] = []

    class Recorder:
        tokenizer = SimpleNamespace(truncation={"max_length": 64})

        def __init__(self, **kwargs: Any) -> None:
            calls.append(kwargs)
            if error is not None:
                if before_failing is not None:
                    before_failing()
                raise error
            self._name: str = kwargs["model_name"]

        def list_supported_models(self) -> list[dict[str, Any]]:
            return [{"model": self._name, "dim": 384}]

        def rerank(self, query: str, documents: Sequence[str]) -> list[float]:
            return [float(len(document)) for document in documents]

    monkeypatch.setattr("fastembed.TextEmbedding", Recorder)
    monkeypatch.setattr("fastembed.rerank.cross_encoder.TextCrossEncoder", Recorder)
    return calls


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_offline_asks_fastembed_for_local_files_only_in_the_shared_cache(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    calls = _stub_fastembed(monkeypatch)

    _load_fastembed_kind(kind, offline=True)

    assert calls == [
        {
            "model_name": _FASTEMBED_MODEL[kind],
            "cache_dir": str(sealed_cache.hub),
            "local_files_only": True,
        }
    ]


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_online_makes_the_call_it_always_made(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """`offline=False` is not allowed to change: no `local_files_only` key, not even `False`."""
    calls = _stub_fastembed(monkeypatch)

    _load_fastembed_kind(kind, offline=False)

    assert calls == [{"model_name": _FASTEMBED_MODEL[kind], "cache_dir": str(sealed_cache.hub)}]


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_a_cached_model_loads_offline_exactly_as_it_does_online(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    _stub_fastembed(monkeypatch)

    offline = _load_fastembed_kind(kind, offline=True)
    online = _load_fastembed_kind(kind, offline=False)

    assert offline.info() == online.info()
    assert offline.info().model == _FASTEMBED_MODEL[kind]
    if kind == "reranker":
        assert offline.score("q", ["ab", "abcd"]) == online.score("q", ["ab", "abcd"]) == [2, 4]


def test_a_failure_that_is_not_a_pinakes_error_becomes_one_offline(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Whatever fastembed or onnxruntime raises: `pnk doctor` prints a FAIL line, no traceback."""
    cause = RuntimeError("boom\nsecond line of a long onnxruntime message")
    _stub_fastembed(monkeypatch, error=cause)

    with pytest.raises(EmbeddingError) as exc_info:
        _load_fastembed_kind("reranker", offline=True)

    assert exc_info.value.__cause__ is cause
    assert "RuntimeError: boom)" in exc_info.value.message
    assert "second line" not in exc_info.value.message
    assert exc_info.value.remedy == _UNLOADABLE_REMEDY.format(cache=sealed_cache.hub)


def test_online_failures_are_not_rewrapped(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only `--offline` changes what a failed load looks like; online, fastembed's error stands."""
    _stub_fastembed(monkeypatch, error=ValueError("Could not load model from any source"))

    with pytest.raises(ValueError, match="any source"):
        _load_fastembed_kind("reranker", offline=False)


def test_ctrl_c_still_interrupts_an_offline_load(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_fastembed(monkeypatch, error=KeyboardInterrupt())

    with pytest.raises(KeyboardInterrupt):
        _load_fastembed_kind("reranker", offline=True)


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_offline_with_no_cache_directory_is_refused_before_fastembed_can_make_one(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    calls = _stub_fastembed(monkeypatch)
    sealed_cache.hub.rmdir()

    with pytest.raises(EmbeddingError) as exc_info:
        _load_fastembed_kind(kind, offline=True)

    assert exc_info.value.message == (
        f"--offline was requested but no model cache exists at {sealed_cache.hub}."
    )
    assert exc_info.value.remedy == _OFFLINE_REMEDY
    assert calls == []
    assert not sealed_cache.hub.exists()


# ── the same promise for the default provider ─────────────────────────────────────────────────────
#
# `[st]` is the default backend. Its loaders pass `local_files_only=offline`, which the wheel and
# the keyword's name say keeps them from downloading — read, not run: nothing here has seen the
# real package refuse a download. What they lacked was a typed failure. For a model absent from the
# cache sentence-transformers 5.6.1 swallows the Hub's `LocalEntryNotFoundError` itself
# and the failure that reaches the caller is transformers'. Neither package is installed for these
# tests (torch is gigabytes), so a stand-in module is put in `sys.modules` and raises whatever the
# test says: that pins what the loader *does* with an exception, not which class the real
# package raises — the loader converts every `Exception` for exactly that reason.


@pytest.fixture
def shared_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """`HF_HOME` in a `tmp_path`, with its (empty) cache directory in place."""
    monkeypatch.setenv("HF_HOME", str(tmp_path / "hf"))
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    hub = tmp_path / "hf" / "hub"
    hub.mkdir(parents=True)
    return hub


def _stub_sentence_transformers(
    monkeypatch: pytest.MonkeyPatch, *, error: BaseException | None = None
) -> list[dict[str, Any]]:
    """Put a `sentence_transformers` stand-in in `sys.modules`; return what it was built with."""
    calls: list[dict[str, Any]] = []

    class Recorder:
        max_seq_length = 128
        config = SimpleNamespace(max_position_embeddings=256)

        def __init__(self, model_name: str, **kwargs: Any) -> None:
            calls.append({"model_name": model_name, **kwargs})
            if error is not None:
                raise error

        def get_sentence_embedding_dimension(self) -> int:
            return 384

        def predict(self, pairs: Sequence[tuple[str, str]]) -> list[float]:
            return [float(len(passage)) for _query, passage in pairs]

    stand_in = ModuleType("sentence_transformers")
    stand_in.__dict__.update(SentenceTransformer=Recorder, CrossEncoder=Recorder)
    monkeypatch.setitem(sys.modules, "sentence_transformers", stand_in)
    return calls


def _load_st_kind(kind: str, *, offline: bool) -> Any:
    if kind == "embedding":
        return load_backend(
            EmbeddingSection(
                provider=SENTENCE_TRANSFORMERS,
                model=_FASTEMBED_MODEL[kind],
                dim=384,
                revision="rev1",
            ),
            offline=offline,
        )
    return load_reranker(
        RerankSection(
            provider=SENTENCE_TRANSFORMERS, model=_FASTEMBED_MODEL[kind], revision="rev1"
        ),
        offline=offline,
    )


_LOADERS = ["fastembed-embedding", "fastembed-reranker", "st-embedding", "st-reranker"]


def _failing_loader(
    monkeypatch: pytest.MonkeyPatch, loader: str, cause: BaseException
) -> tuple[Callable[[], Any], str]:
    """Stub the library behind `loader` so building a model raises `cause`; return (load, model)."""
    provider, kind = loader.split("-")
    if provider == "fastembed":
        _stub_fastembed(monkeypatch, error=cause)
        return (lambda: _load_fastembed_kind(kind, offline=True)), _FASTEMBED_MODEL[kind]
    _stub_sentence_transformers(monkeypatch, error=cause)
    return (lambda: _load_st_kind(kind, offline=True)), _FASTEMBED_MODEL[kind]


# (what the library raises, the reason `doctor` shows, whether it is class (a))
# Class (a), "fastembed could not find a usable local copy (usually: absent)", is a
# FileNotFoundError (a subclass counts), or a ValueError whose first non-empty line *starts with*
# fastembed's "Could not load model" — the one message matched by its text. Everything else is a
# different problem with its own remedy, and each near-miss below is a way to get this wrong.
_OFFLINE_CAUSES = [
    pytest.param(
        lambda: ValueError("Could not load model m from any source."),
        "ValueError: Could not load model m from any source.",
        True,
        id="fastembed-could-not-load-model",
    ),
    pytest.param(
        lambda: pytest.importorskip("huggingface_hub.errors").LocalEntryNotFoundError(
            "Cannot find the requested files in the disk cache."
        ),
        "LocalEntryNotFoundError: Cannot find the requested files in the disk cache.",
        True,
        id="huggingface-hub-LocalEntryNotFoundError-a-subclass",
    ),
    pytest.param(
        lambda: ValueError("Could not find tokenizer.json in /x"),
        "ValueError: Could not find tokenizer.json in /x",
        False,
        id="ValueError-that-shares-only-a-prefix-with-fastembeds",
    ),
    pytest.param(
        lambda: ValueError("see: Could not load model x from any source."),
        "ValueError: see: Could not load model x from any source.",
        False,
        id="fastembeds-words-not-at-the-start",
    ),
    pytest.param(
        lambda: ValueError("irrelevant\nCould not load model x from any source."),
        "ValueError: irrelevant",
        False,
        id="fastembeds-words-on-a-later-line",
    ),
    pytest.param(
        lambda: RuntimeError("Could not load model x from any source."),
        "RuntimeError: Could not load model x from any source.",
        False,
        id="fastembeds-words-but-not-a-ValueError",
    ),
    pytest.param(
        lambda: RuntimeError("a" * 450),
        "RuntimeError: " + "a" * 199 + "…",
        False,
        id="line-of-450-characters-is-cut-to-200-with-an-ellipsis",
    ),
    pytest.param(
        lambda: RuntimeError("b" * 201),
        "RuntimeError: " + "b" * 199 + "…",
        False,
        id="line-one-over-the-cap-is-cut",
    ),
    pytest.param(
        lambda: RuntimeError("c" * 200),
        "RuntimeError: " + "c" * 200,
        False,
        id="line-exactly-at-the-cap-is-left-whole",
    ),
    pytest.param(
        lambda: ValueError("\n\nCould not load model m from any source."),
        "ValueError: Could not load model m from any source.",
        True,
        id="absent-after-blank-lines",
    ),
    pytest.param(
        lambda: FileNotFoundError("modules.json"),
        "FileNotFoundError: modules.json",
        True,
        id="FileNotFoundError",
    ),
    pytest.param(
        lambda: ValueError("Model m is not supported in TextEmbedding."),
        "ValueError: Model m is not supported in TextEmbedding.",
        False,
        id="ValueError-that-is-not-absent",
    ),
    pytest.param(
        lambda: OSError("no cached copy"), "OSError: no cached copy", False, id="plain-OSError"
    ),
    pytest.param(
        lambda: PermissionError(13, "Permission denied"),
        "PermissionError: [Errno 13] Permission denied",
        False,
        id="errno-style-PermissionError",
    ),
    pytest.param(lambda: MemoryError(), "MemoryError", False, id="MemoryError-no-message"),
    pytest.param(lambda: AssertionError(), "AssertionError", False, id="AssertionError-no-message"),
    pytest.param(
        lambda: TypeError("__init__() got an unexpected keyword argument 'local_files_only'"),
        "TypeError: __init__() got an unexpected keyword argument 'local_files_only'",
        False,
        id="TypeError-from-a-changed-signature",
    ),
    pytest.param(
        lambda: RuntimeError("\n\nreal message\nsecond line"),
        "RuntimeError: real message",
        False,
        id="leading-blank-lines",
    ),
    pytest.param(lambda: RuntimeError("first\r\nsecond"), "RuntimeError: first", False, id="CRLF"),
    pytest.param(
        lambda: RuntimeError("  \n\t real  \nsecond"),
        "RuntimeError: real",
        False,
        id="whitespace-lines-and-indent",
    ),
    pytest.param(lambda: RuntimeError("\n \n"), "RuntimeError", False, id="only-blank-lines"),
]


@pytest.mark.parametrize("loader", _LOADERS)
@pytest.mark.parametrize(("make_cause", "reason", "absent"), _OFFLINE_CAUSES)
def test_every_loader_reports_an_offline_failure_by_its_cause(
    shared_cache: Path,
    monkeypatch: pytest.MonkeyPatch,
    loader: str,
    make_cause: Callable[[], Exception],
    reason: str,
    absent: bool,
) -> None:
    """One rule for all four loaders. A missing model keeps the original text and its remedy; any
    other failure makes no claim about the cache and names what will help instead of "go online"."""
    cause = make_cause()
    load, model = _failing_loader(monkeypatch, loader, cause)

    with pytest.raises(EmbeddingError) as exc_info:
        load()

    if absent:
        message = (
            f"--offline was requested but {model} could not be loaded from the model cache at "
            f"{shared_cache} ({reason})."
        )
        remedy = _OFFLINE_REMEDY
    else:
        message = f"--offline was requested but {model} could not be loaded ({reason})."
        remedy = _UNLOADABLE_REMEDY.format(cache=shared_cache)
    assert exc_info.value.message == message
    assert exc_info.value.remedy == remedy
    assert exc_info.value.__cause__ is cause


# Plain `OSError`s (no errno) that transformers 5.14.1 (the pinned version) raises while loading a
# config under `local_files_only=True`, copied from the source. Read, not run — no test here has
# seen the real package raise any of them. Only the first is a model missing from the cache
# (`utils/hub.py:513-516`); the others are *other* plain `OSError`s from the same call:
# `configuration_utils.py:798-803` is raised only when `cached_file` raised a non-`OSError` (an
# `OSError` is re-raised before it, `:792-795`), `:813-814` is a config that is not valid JSON,
# `utils/hub.py:481-486` a `PermissionError`.
_TRANSFORMERS_OSERRORS = {
    "cache-miss": (
        "We couldn't connect to 'https://huggingface.co' to load the files, and couldn't find them "
        "in the cached files.\nCheck your internet connection or see how to run the library in "
        "offline mode at 'https://huggingface.co/docs/transformers/installation#offline-mode'."
    ),
    "generic-configuration-error": (
        "Can't load the configuration of '{model}'. If you were trying to load it from "
        "'https://huggingface.co/models', make sure you don't have a local directory with the same "
        "name. Otherwise, make sure '{model}' is the correct path to a directory containing a "
        "config.json file"
    ),
    "config-is-not-valid-json": (
        "It looks like the config file at '/cache/models--x/snapshots/abc/config.json' is not a "
        "valid JSON file."
    ),
    "permission-error": (
        "PermissionError at /cache/models--x/.locks/lock when downloading {model}. Check cache "
        "directory permissions. Common causes: 1) another user is downloading the same model "
        "(please wait); 2) a previous download was canceled and the lock file needs manual removal."
    ),
}


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
@pytest.mark.parametrize("which", list(_TRANSFORMERS_OSERRORS))
def test_st_offline_plain_oserrors_from_transformers_name_both_remedies(
    shared_cache: Path, monkeypatch: pytest.MonkeyPatch, kind: str, which: str
) -> None:
    """Transformers raises a plain `OSError` for a model missing from the cache and also for other
    failures (a config that is not valid JSON among them), so the class cannot tell "absent" from
    "damaged": the message makes no claim about the cache, and the remedy covers both readings.
    Only fastembed's one `ValueError` is classed by reading its text; these are not."""
    model = _FASTEMBED_MODEL[kind]
    text = _TRANSFORMERS_OSERRORS[which].format(model=model)
    cause = OSError(text)
    assert cause.errno is None and type(cause) is OSError
    _stub_sentence_transformers(monkeypatch, error=cause)

    with pytest.raises(EmbeddingError) as exc_info:
        _load_st_kind(kind, offline=True)

    first_line = text.splitlines()[0]
    if len(first_line) > 200:  # the cap, written out here rather than imported: it is a spec
        first_line = first_line[:199] + "…"
    assert exc_info.value.message == (
        f"--offline was requested but {model} could not be loaded (OSError: {first_line})."
    )
    assert "model cache at" not in exc_info.value.message
    assert exc_info.value.remedy == _UNLOADABLE_REMEDY.format(cache=shared_cache)
    assert "run once without --offline to populate it" in exc_info.value.remedy
    assert "delete its folder" in exc_info.value.remedy
    assert exc_info.value.__cause__ is cause


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_st_offline_passes_revision_local_files_only_and_the_shared_cache(
    shared_cache: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """A cached model loads: the same call as before, and the model comes back usable."""
    calls = _stub_sentence_transformers(monkeypatch)

    loaded = _load_st_kind(kind, offline=True)

    assert calls == [
        {
            "model_name": _FASTEMBED_MODEL[kind],
            "revision": "rev1",
            "local_files_only": True,
            "cache_folder": str(shared_cache),
        }
    ]
    assert loaded.info().model == _FASTEMBED_MODEL[kind]
    assert loaded.info().revision == "rev1"
    if kind == "reranker":
        assert loaded.score("q", ["ab", "abcd"]) == [2.0, 4.0]


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_st_online_makes_the_call_it_always_made(
    shared_cache: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    calls = _stub_sentence_transformers(monkeypatch)

    _load_st_kind(kind, offline=False)

    assert calls == [
        {
            "model_name": _FASTEMBED_MODEL[kind],
            "revision": "rev1",
            "local_files_only": False,
            "cache_folder": str(shared_cache),
        }
    ]


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_st_online_failures_are_not_rewrapped(
    shared_cache: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    cause = OSError("the Hub said no")
    _stub_sentence_transformers(monkeypatch, error=cause)

    with pytest.raises(OSError) as exc_info:
        _load_st_kind(kind, offline=False)

    assert exc_info.value is cause


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_st_ctrl_c_still_interrupts_an_offline_load(
    shared_cache: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    _stub_sentence_transformers(monkeypatch, error=KeyboardInterrupt())

    with pytest.raises(KeyboardInterrupt):
        _load_st_kind(kind, offline=True)


# ── what the cleanup, the directory guard and a cached model do ───────────────────────────────────


def test_a_scratch_directory_that_is_not_empty_is_left_alone_and_the_error_stays_typed(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Something else is downloading into `<cache>/tmp`: the cleanup must neither delete it nor
    let the `rmdir` that refuses escape as an `OSError` in place of the typed error."""
    scratch = sealed_cache.hub / "tmp"

    def a_download_in_progress() -> None:
        scratch.mkdir()
        (scratch / "x").write_text("half a model")

    _stub_fastembed(
        monkeypatch,
        error=ValueError("Could not load model m from any source."),
        before_failing=a_download_in_progress,
    )

    with pytest.raises(EmbeddingError):
        _load_fastembed_kind("reranker", offline=True)

    assert (scratch / "x").read_text() == "half a model"


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_online_with_no_cache_directory_is_not_refused(
    sealed_cache: _Sealed, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """A first `pnk sync` on a fresh machine has no cache directory and must be allowed to fetch."""
    calls = _stub_fastembed(monkeypatch)
    sealed_cache.hub.rmdir()

    _load_fastembed_kind(kind, offline=False)

    assert calls == [{"model_name": _FASTEMBED_MODEL[kind], "cache_dir": str(sealed_cache.hub)}]


def _protobuf_varint(number: int) -> bytes:
    out = bytearray()
    while True:
        low, number = number & 0x7F, number >> 7
        out.append(low | (0x80 if number else 0))
        if not number:
            return bytes(out)


def _protobuf_field(number: int, wire_type: int, payload: bytes) -> bytes:
    key = _protobuf_varint((number << 3) | wire_type)
    if wire_type == 2:  # length-delimited
        return key + _protobuf_varint(len(payload)) + payload
    return key + payload


def _protobuf_string(number: int, text: str) -> bytes:
    return _protobuf_field(number, 2, text.encode())


def _protobuf_int(number: int, value: int) -> bytes:
    return _protobuf_field(number, 0, _protobuf_varint(value))


def _tiny_onnx_identity() -> bytes:
    """A valid ONNX model, encoded by hand (the `onnx` package is not a dependency): `out =
    Identity(input_ids)` on an int64 vector. It is not an embedder; it only has to *load*."""

    def int64_vector(name: str) -> bytes:  # ValueInfoProto
        shape = _protobuf_field(1, 2, _protobuf_string(2, "n"))  # TensorShapeProto.dim: dim_param
        tensor = _protobuf_int(1, 7) + _protobuf_field(2, 2, shape)  # elem_type INT64, shape
        return _protobuf_string(1, name) + _protobuf_field(2, 2, _protobuf_field(1, 2, tensor))

    node = (
        _protobuf_string(1, "input_ids")
        + _protobuf_string(2, "out")
        + _protobuf_string(3, "id")
        + _protobuf_string(4, "Identity")
    )
    graph = (
        _protobuf_field(1, 2, node)
        + _protobuf_string(2, "g")
        + _protobuf_field(11, 2, int64_vector("input_ids"))
        + _protobuf_field(12, 2, int64_vector("out"))
    )
    opset = _protobuf_string(1, "") + _protobuf_int(2, 13)
    return _protobuf_int(1, 8) + _protobuf_field(8, 2, opset) + _protobuf_field(7, 2, graph)


def _plant_loadable_model(hub: Path, kind: str) -> None:
    """Cache a minimal model that the real fastembed can load, where it will look for it.

    The repository and file name come from fastembed's public `list_supported_models()`, not from
    this file, so a registry that moves a model moves the plant with it.
    """
    tokenizers = pytest.importorskip("tokenizers")
    if kind == "embedding":
        listed = pytest.importorskip("fastembed").TextEmbedding.list_supported_models()
    else:
        cross_encoder = pytest.importorskip("fastembed.rerank.cross_encoder")
        listed = cross_encoder.TextCrossEncoder.list_supported_models()
    entry = next(entry for entry in listed if entry["model"] == _FASTEMBED_MODEL[kind])
    repo = entry["sources"]["hf"]
    if repo is None:
        pytest.skip(
            f"fastembed no longer sources {_FASTEMBED_MODEL[kind]} from the Hugging Face Hub"
        )

    vocabulary = tokenizers.models.WordLevel(
        {"[UNK]": 0, "[PAD]": 1, "hello": 2}, unk_token="[UNK]"
    )
    tokenizer = tokenizers.Tokenizer(vocabulary)
    tokenizer.pre_tokenizer = tokenizers.pre_tokenizers.Whitespace()
    files: dict[str, bytes] = {
        entry["model_file"]: _tiny_onnx_identity(),
        "tokenizer.json": tokenizer.to_str().encode(),
        "config.json": json.dumps({"pad_token_id": 1}).encode(),
        "tokenizer_config.json": json.dumps(
            {"model_max_length": 64, "pad_token": "[PAD]"}
        ).encode(),
        "special_tokens_map.json": json.dumps(
            {"unk_token": "[UNK]", "pad_token": "[PAD]"}
        ).encode(),
    }
    additional_files: list[str] = entry.get("additional_files") or []
    for extra in additional_files:
        files.setdefault(extra, b"")
    _plant(hub, repo, files)


@pytest.mark.parametrize("kind", ["embedding", "reranker"])
def test_a_cached_model_loads_offline_through_the_real_fastembed_exactly_as_online(
    sealed_cache: _Sealed, kind: str
) -> None:
    """The success path with nothing stubbed but the network: the real fastembed, the real
    onnxruntime, a model in a Hugging Face layout cache.

    What is real, per kind. **Both:** the model loads offline and online (an ONNX session is built
    from the planted file), nothing is fetched, and the cache tree is unchanged afterwards.
    **The embedder only:** `max_seq_length` and the token count come out of the planted tokenizer,
    so they prove it was read from the cache; `dim` is looked up in fastembed's registry and proves
    nothing about the planted files. **The reranker's `info()` returns constants**, so the
    equality of its offline and online `info()` is vacuous; only "loads, reaches nothing, cache
    unchanged" is real for it.

    This **passes on the code before the fix too** (fastembed tries the local snapshot first, flag
    or no flag): it is a regression guard on the success path, not proof of the fix. The cached
    model is a hand-encoded one-node ONNX graph, so it says nothing about real weights; the
    `model`-marked tests above cover real weights, online only.
    """
    _plant_loadable_model(sealed_cache.hub, kind)
    before = _tree(sealed_cache.hub)

    offline = _load_fastembed_kind(kind, offline=True)
    online = _load_fastembed_kind(kind, offline=False)

    assert offline.info() == online.info()
    assert offline.info().model == _FASTEMBED_MODEL[kind]
    if kind == "embedding":
        assert offline.info().dim == 384
        assert offline.info().max_seq_length == 64  # the planted tokenizer_config's, not a default
        # The tokenizer came out of the cache too: "hello" is the planted vocabulary's one word.
        assert offline.count_tokens("hello hello") == online.count_tokens("hello hello") == 2
    assert sealed_cache.reached == []
    assert _tree(sealed_cache.hub) == before
