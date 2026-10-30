"""Embedding and reranking backends — the only part of the free path that needs model weights.

Two protocols, two open registries, and lazy imports. The shape follows three constraints:

* **Core install must stay light.** Neither backend is imported until a manifest asks for it, so
  `uv add pinakes` never pulls torch. A missing backend fails with the exact extra to install
  (docs/DESIGN.md §4.5), which is a supported state, not a broken one.
* **The registry is open.** Providers are looked up in a dict, not matched against an enum, so tests
  can register a deterministic fake and drive the real CLI end to end without downloading anything.
* **Weights live in one shared cache.** `HF_HOME` by default, so N KBs on a machine share one copy.
  fastembed left alone caches to `$TMPDIR/fastembed_cache` (verified in its `define_cache_dir`,
  20260725 15:15), so this module passes it an explicit directory under the HF cache instead.

Both protocols expose `info()`, because §4.4's coherence check compares what built the index against
what is loaded now, and §4.2's confidence thresholds are only valid for the reranker they were
fitted against.
"""

import contextlib
import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from pinakes.errors import BackendMissingError, BackendUnknownError, EmbeddingError
from pinakes.manifest import EmbeddingSection, RerankSection

SENTENCE_TRANSFORMERS = "sentence-transformers"
FASTEMBED = "fastembed"

type Vectors = np.ndarray[Any, np.dtype[np.float32]]


@dataclass(frozen=True, slots=True)
class ModelInfo:
    provider: str
    model: str
    revision: str | None
    dim: int
    max_seq_length: int

    def fingerprint(self) -> str:
        """`model@revision` — what `[retrieval.confidence] fitted_for` records (§4.2)."""
        return f"{self.model}@{self.revision}" if self.revision else self.model


class EmbeddingBackend(Protocol):
    def embed(self, texts: Sequence[str]) -> Vectors: ...
    def count_tokens(self, text: str) -> int: ...
    def info(self) -> ModelInfo: ...


class Reranker(Protocol):
    def score(self, query: str, passages: Sequence[str]) -> list[float]: ...
    def info(self) -> ModelInfo: ...


type EmbeddingFactory = Callable[[EmbeddingSection, bool], EmbeddingBackend]
type RerankerFactory = Callable[[RerankSection, bool], Reranker]

_EMBEDDING_BACKENDS: dict[str, EmbeddingFactory] = {}
_RERANKERS: dict[str, RerankerFactory] = {}


def register_embedding_backend(provider: str, factory: EmbeddingFactory) -> None:
    _EMBEDDING_BACKENDS[provider] = factory


def register_reranker(provider: str, factory: RerankerFactory) -> None:
    _RERANKERS[provider] = factory


def registered_embedding_providers() -> list[str]:
    return sorted(_EMBEDDING_BACKENDS)


def load_backend(section: EmbeddingSection, *, offline: bool = False) -> EmbeddingBackend:
    """Build the embedding backend a manifest asks for, and check it agrees about `dim`."""
    factory = _EMBEDDING_BACKENDS.get(section.provider)
    if factory is None:
        raise BackendUnknownError(section.provider, known=registered_embedding_providers())

    backend = factory(section, offline)
    info = backend.info()
    if info.dim != section.dim:
        raise EmbeddingError(
            f"[embedding] dim = {section.dim}, but {info.model} produces {info.dim} dimensions.",
            remedy=(
                f"Set dim = {info.dim} and run `pnk sync --rebuild`. A mismatch here would store "
                "vectors that cannot be compared."
            ),
        )
    return backend


def load_reranker(section: RerankSection, *, offline: bool = False) -> Reranker:
    factory = _RERANKERS.get(section.provider)
    if factory is None:
        raise BackendUnknownError(section.provider, known=sorted(_RERANKERS))
    return factory(section, offline)


def hf_cache_dir() -> Path:
    """The shared Hugging Face cache — one copy of the weights per machine, not per KB (§4.5)."""
    home = os.environ.get("HF_HOME")
    if home:
        return Path(home) / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


# The package each provider's factories import — used only to check, via `find_spec`, whether a
# *sibling* provider is already installed when the configured one is missing (never to import it:
# probing availability by loading a backend is exactly what the paid-path invariant forbids for
# the paid extractor, and the same reasoning applies here — a check must not have the side effects
# of the thing it is checking).
_PROVIDER_PACKAGE: dict[str, str] = {
    SENTENCE_TRANSFORMERS: "sentence_transformers",
    FASTEMBED: "fastembed",
}


def _installed_alternative(missing: str, siblings: Sequence[str]) -> str | None:
    """The first *other* registered provider whose package is importable on this machine, if any.

    `siblings` is every provider registered for the same kind (embedding or rerank) — including
    test fakes, which `_PROVIDER_PACKAGE` has no entry for and so are silently skipped rather than
    misreported as installed.
    """
    from importlib.util import find_spec

    for provider in siblings:
        if provider == missing:
            continue
        package = _PROVIDER_PACKAGE.get(provider)
        if package is not None and find_spec(package) is not None:
            return provider
    return None


def _import(module: str, extra: str, what: str, *, siblings: Sequence[str]) -> Any:
    try:
        return __import__(module, fromlist=["_"])
    except ImportError as exc:
        alternative = _installed_alternative(what, siblings)
        raise BackendMissingError(what, extra=extra, alternative=alternative) from exc


_OFFLINE_REMEDY = "Run once without --offline to populate the cache."


_REASON_LIMIT = 200  # characters of the quoted line, the ellipsis included


def _offline_load_error(model: str, exc: Exception) -> EmbeddingError:
    """What `--offline` reports when `model` could not be loaded: one rule for every loader.

    `exc` is whatever the library raised, and it is not a `PinakesError` (a `ValueError` from
    fastembed, an `OSError` or onnxruntime's `InvalidProtobuf` from the others), so left alone
    `pnk doctor` ends in a traceback instead of a FAIL line. Two classes, because the remedy
    differs:

    * **fastembed could not find a usable local copy (usually: absent)** — a `FileNotFoundError`
      (including huggingface_hub's `LocalEntryNotFoundError`), or fastembed's one `ValueError`,
      `"Could not load model … from any source"`, which is **matched by the start of its text**
      (the only place this helper reads a message to classify). "Usually absent" is the honest
      reading: fastembed swallows every failure of its local lookup (`model_management.py:424`,
      `:461`) and raises that `ValueError` at `:475`, so an unreadable snapshots directory or a
      truncated `files_metadata.json` reach it too (by reading, not run), and going online would
      not fix those. The text and remedy are kept as they were.
    * **Anything else** — a truncated download (onnxruntime's `InvalidProtobuf`), a
      `PermissionError`, a `MemoryError`, a `TypeError` from a changed signature, and the plain
      `OSError` transformers raises. No claim is made about the cache, and the remedy names both
      readings: going online fetches a model that is absent, but does not help a damaged one
      (fastembed tries the local snapshot first online too, and fails the same way). It has to name
      both because the class cannot tell them apart — transformers 5.14.1 raises one plain
      `OSError` class for a model missing from the cache (`utils/hub.py:513-516`) and for other
      failures: a generic "Can't load the configuration" when `cached_file` raised a non-`OSError`
      (`configuration_utils.py:796-803`; an `OSError` is re-raised untouched before it, `:792-795`),
      a config that is not valid JSON (`:813-814`), a `PermissionError` (`utils/hub.py:481-486`).
      Nothing is classified by reading those messages.

    The reason quotes the class and the first non-empty line of `str(exc)` (`splitlines`, so
    `"\\nreal message"` and CRLF work), cut to `_REASON_LIMIT` characters with an ellipsis, so a
    `doctor` check stays a line: an onnxruntime `Fail` line runs to ~450 characters with a build
    path. That is for length, not for privacy — onnxruntime's first line also carries the absolute
    path of the model file, which lies under the cache directory the remedy prints anyway.
    """
    first_line = next((line.strip() for line in str(exc).splitlines() if line.strip()), "")
    shown = first_line
    if len(first_line) > _REASON_LIMIT:
        shown = first_line[: _REASON_LIMIT - 1] + "…"
    reason = f"{type(exc).__name__}: {shown}" if first_line else type(exc).__name__
    cache = hf_cache_dir()
    model_is_absent = isinstance(exc, FileNotFoundError) or (
        isinstance(exc, ValueError) and first_line.startswith("Could not load model")
    )
    if model_is_absent:
        return EmbeddingError(
            f"--offline was requested but {model} could not be loaded from the model cache at "
            f"{cache} ({reason}).",
            remedy=_OFFLINE_REMEDY,
        )
    return EmbeddingError(
        f"--offline was requested but {model} could not be loaded ({reason}).",
        remedy=(
            "Fix the cause named above. If the model is not in the cache, run once without "
            "--offline to populate it; if its files are damaged, delete its folder under "
            f"{cache} first."
        ),
    )


def _sentence_transformers_backend(section: EmbeddingSection, offline: bool) -> EmbeddingBackend:
    """`local_files_only=offline` is meant to keep this from downloading; it did not keep it typed.

    The first half is read, not run: from the 5.6.1 wheel (read 20261030 20:02 UTC, never
    installed) and from the keyword's name — no test here has seen a download refused. What the
    wheel does show: for a model absent from the cache, its `load_file_path` swallows the Hub's
    `LocalEntryNotFoundError` and falls back to `_load_default_modules`, whose
    `AutoConfig.from_pretrained(..., local_files_only=True)` is transformers' to fail. Read in
    transformers 5.14.1 (the pinned version; 20261030 20:42 UTC, never installed): a model missing
    from the cache raises a **plain `OSError`**, never a `FileNotFoundError` — "We couldn't connect
    to … and couldn't find them in the cached files" (`utils/hub.py:513-516`). Other plain
    `OSError`s come from the same call: the generic "Can't load the configuration of …"
    (`configuration_utils.py:798-803`, only for a non-`OSError` from `cached_file`; an `OSError` is
    re-raised before it, `:792-795`), a config that is not valid JSON (`:813-814`), a
    `PermissionError` (`utils/hub.py:481-486`). So a missing model lands in the second class of
    `_offline_load_error`, whose remedy names both "not in the cache" and "files damaged".
    Nothing of sentence-transformers or transformers was *run*.
    """
    module = _import(
        "sentence_transformers", "st", section.provider, siblings=registered_embedding_providers()
    )
    try:
        model = module.SentenceTransformer(
            section.model,
            revision=section.revision,
            local_files_only=offline,
            cache_folder=str(hf_cache_dir()),
        )
    except Exception as exc:
        if not offline:
            raise
        raise _offline_load_error(section.model, exc) from exc
    return _SentenceTransformersBackend(section, model)


def _sentence_transformers_reranker(section: RerankSection, offline: bool) -> Reranker:
    module = _import("sentence_transformers", "st", section.provider, siblings=sorted(_RERANKERS))
    try:
        model = module.CrossEncoder(
            section.model,
            revision=section.revision,
            local_files_only=offline,
            cache_folder=str(hf_cache_dir()),
        )
    except Exception as exc:
        if not offline:
            raise
        raise _offline_load_error(section.model, exc) from exc
    return _SentenceTransformersReranker(section, model)


def _fastembed_backend(section: EmbeddingSection, offline: bool) -> EmbeddingBackend:
    module = _import(
        "fastembed", "light", section.provider, siblings=registered_embedding_providers()
    )
    _require_online_or_cached(offline)
    model = _load_fastembed(module.TextEmbedding, section.model, offline)
    return _FastembedBackend(section, model)


def _fastembed_reranker(section: RerankSection, offline: bool) -> Reranker:
    module = _import(
        "fastembed.rerank.cross_encoder", "light", section.provider, siblings=sorted(_RERANKERS)
    )
    _require_online_or_cached(offline)
    model = _load_fastembed(module.TextCrossEncoder, section.model, offline)
    return _FastembedReranker(section, model)


def _require_online_or_cached(offline: bool) -> None:
    """`--offline` against a cache directory that does not exist: refuse before fastembed runs.

    This is the cheap half of the guard and no more than that: it says nothing about *which* models
    the directory holds. `_load_fastembed` is the half that does, and it also keeps fastembed from
    creating the directory (its `define_cache_dir` does `mkdir`).
    """
    if offline and not hf_cache_dir().exists():
        raise EmbeddingError(
            f"--offline was requested but no model cache exists at {hf_cache_dir()}.",
            remedy=_OFFLINE_REMEDY,
        )


def _load_fastembed(model_class: Any, model: str, offline: bool) -> Any:
    """Construct a fastembed model; offline, from the cache or not at all.

    fastembed 0.8 *does* take `local_files_only` — through `**kwargs` into its download step
    (`common/model_management.py`, read 20261030 19:51 UTC against 0.8.0; the comment that said
    otherwise predated it).
    With it, a model missing from `cache_dir` raises `ValueError("Could not load model … from any
    source")` instead of being fetched, and a model that is there loads exactly as it did online
    (fastembed's first move online is the same local-only lookup). So a directory that exists but
    lacks *this* model no longer reaches the network, which is what the directory check alone let
    through (measured 20261019: `pnk doctor` fetched a 1.1 GB reranker).

    Every failure offline becomes an `EmbeddingError`: a missing model is a `ValueError` from
    fastembed, a cached but broken one is whatever onnxruntime raises, and neither is a
    `PinakesError`, so `pnk doctor` would crash with a traceback instead of printing a FAIL line.
    `except Exception` is deliberate and narrow in effect — it only re-raises, as the typed error —
    and `KeyboardInterrupt` still passes through. Online, nothing changes: the call is the one
    that was always made.
    """
    cache = hf_cache_dir()
    if not offline:
        return model_class(model_name=model, cache_dir=str(cache))

    # fastembed's local-only path makes `<cache>/tmp` before it finds nothing. An empty `tmp` in
    # the Hugging Face cache is not a repo, and `hf cache scan` warns about it; clean up our own.
    scratch = cache / "tmp"
    scratch_existed = scratch.exists()
    try:
        return model_class(model_name=model, cache_dir=str(cache), local_files_only=True)
    except Exception as exc:
        if not scratch_existed:
            _remove_if_empty(scratch)
        raise _offline_load_error(model, exc) from exc


def _remove_if_empty(directory: Path) -> None:
    with contextlib.suppress(OSError):  # absent, not empty, or not ours to remove: leave it
        directory.rmdir()


class _SentenceTransformersBackend:
    def __init__(self, section: EmbeddingSection, model: Any) -> None:
        self._section = section
        self._model = model

    def embed(self, texts: Sequence[str]) -> Vectors:
        vectors: Any = self._model.encode(
            list(texts), convert_to_numpy=True, normalize_embeddings=True
        )
        return np.ascontiguousarray(vectors, dtype=np.float32)

    def count_tokens(self, text: str) -> int:
        return len(self._model.tokenizer.encode(text, add_special_tokens=False))

    def info(self) -> ModelInfo:
        return ModelInfo(
            provider=self._section.provider,
            model=self._section.model,
            revision=self._section.revision,
            dim=int(self._model.get_sentence_embedding_dimension()),
            max_seq_length=int(self._model.max_seq_length),
        )


class _SentenceTransformersReranker:
    def __init__(self, section: RerankSection, model: Any) -> None:
        self._section = section
        self._model = model

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []
        scores: Any = self._model.predict([(query, passage) for passage in passages])
        return [float(score) for score in scores]

    def info(self) -> ModelInfo:
        config: Any = getattr(self._model, "config", None)
        window = int(getattr(config, "max_position_embeddings", 512)) if config else 512
        return ModelInfo(
            provider=self._section.provider,
            model=self._section.model,
            revision=self._section.revision,
            dim=0,  # a cross-encoder emits a score, not a vector
            max_seq_length=window,
        )


class _FastembedBackend:
    def __init__(self, section: EmbeddingSection, model: Any) -> None:
        self._section = section
        self._model = model

    def embed(self, texts: Sequence[str]) -> Vectors:
        listed = list(texts)
        if not listed:
            return np.zeros((0, self.info().dim), dtype=np.float32)
        vectors = np.vstack([np.asarray(v, dtype=np.float32) for v in self._model.embed(listed)])
        return np.ascontiguousarray(vectors, dtype=np.float32)

    def count_tokens(self, text: str) -> int:
        """fastembed exposes the HF tokenizer it loaded; `max_seq_length` is not public API."""
        tokenizer = self._tokenizer()
        return len(tokenizer.encode(text, add_special_tokens=False).ids)

    def _tokenizer(self) -> Any:
        model: Any = getattr(self._model, "model", self._model)
        tokenizer: Any = getattr(model, "tokenizer", None)
        if tokenizer is None:  # pragma: no cover — only if fastembed changes shape
            raise EmbeddingError(
                "this fastembed version does not expose a tokenizer.",
                remedy="Pin fastembed, or use the [st] backend, which does.",
            )
        return tokenizer

    def info(self) -> ModelInfo:
        described = [
            entry
            for entry in self._model.list_supported_models()
            if entry["model"] == self._section.model
        ]
        dim = int(described[0]["dim"]) if described else self._section.dim
        truncation: Any = getattr(self._tokenizer(), "truncation", None)
        window = int(truncation["max_length"]) if truncation else 512
        return ModelInfo(
            provider=self._section.provider,
            model=self._section.model,
            revision=self._section.revision,
            dim=dim,
            max_seq_length=window,
        )


class _FastembedReranker:
    def __init__(self, section: RerankSection, model: Any) -> None:
        self._section = section
        self._model = model

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        if not passages:
            return []
        return [float(score) for score in self._model.rerank(query, list(passages))]

    def info(self) -> ModelInfo:
        return ModelInfo(
            provider=self._section.provider,
            model=self._section.model,
            revision=self._section.revision,
            dim=0,
            max_seq_length=512,
        )


register_embedding_backend(SENTENCE_TRANSFORMERS, _sentence_transformers_backend)
register_embedding_backend(FASTEMBED, _fastembed_backend)
register_reranker(SENTENCE_TRANSFORMERS, _sentence_transformers_reranker)
register_reranker(FASTEMBED, _fastembed_reranker)
