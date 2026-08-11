"""How many characters a chunk of N *embedding* tokens actually holds — the offline half of the
measurement behind `deep/estimate.py`'s `VENDOR_TOKENS_PER_CHUNK_TOKEN` (E2).

**The problem this exists for.** A chunk is sized in the embedding model's tokenizer
(`[chunking] max_tokens`, counted by `EmbeddingBackend.count_tokens`) and *priced* in the vendor's,
and the two are different tokenizers over the same text. Nothing in this repository can count
vendor tokens without a network call to a paid API, so the conversion cannot be measured here. What
can be measured — exactly, offline, over the committed corpora — is the **character** width of a
chunk at a given `max_tokens`, which is the term both tokenizers are a function of.

**How the number is used.** `chars_per_chunk_token` measured here, divided by an assumed
characters-per-vendor-token, is the multiplier `deep/estimate.py` applies to `[chunking]
max_tokens`. The estimator's constant is set *above* that quotient at a pessimistic assumption,
because a ceiling below a measurement is not a ceiling (`budget/estimate.py`'s
`PAGE_TOKEN_CEILING` records the same trade, and refused the same shortcut).

**E6 replaces the assumed half, never this half.** The measurement run counts real vendor tokens
for real passages with `messages.count_tokens` and publishes the over-reservation factor. This tool
stays useful after that: it is what says whether a *corpus* has moved, without spending anything.

Usage — the command the constant's comment names:

    uv run --frozen python3 tools/measure_passage_tokens.py \\
        tests/demo-kb/docs tests/partner-kb/docs docs

Every root is walked for `*.md`; sidecars (`*.pnk.yaml`) are skipped. Chunking runs at the shipped
template defaults (`max_tokens = 510`, `overlap = 64`), **not** at any corpus's own manifest
setting — the question is what the default chunk width holds, and `tests/demo-kb` deliberately
chunks at 120 to keep its fixtures small.

Needs `pinakes[light]` (fastembed) for the real tokenizer. A word-count stand-in would answer a
different question: the whole point is the *model's* tokenizer, not an approximation of it.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

from pinakes.chunk import chunk_document
from pinakes.embed import load_backend
from pinakes.manifest import EmbeddingSection

#: The shipped `notes` template's chunking, not any corpus's own — see the module docstring.
MAX_TOKENS = 510
OVERLAP = 64

#: The template's default embedding model, so the tokenizer is the one a stock KB actually uses.
MODEL = "BAAI/bge-small-en-v1.5"
DIM = 384


@dataclass(frozen=True, slots=True)
class Widest:
    """The worst chunk found, by one measure."""

    ratio: float
    chars: int
    tokens: int
    path: str

    def describe(self) -> str:
        return (
            f"{self.ratio:.2f} chars/token — {self.path} ({self.chars} chars, {self.tokens} tokens)"
        )


def measure(roots: list[Path]) -> tuple[int, Widest, Widest, tuple[int, str]]:
    """Chunk every Markdown file under `roots`; return count, worst ratio, widest chunk, envelope.

    Two worsts, deliberately. The **widest** chunk is the one that bounds a full-size passage; the
    **worst ratio** is usually a short block whose ratio no full-size chunk could sustain, and
    reporting only the first would hide that the two disagree by nearly 2x on this corpus.

    The fourth number is the longest `path — heading_path` a passage is *wrapped* in, which is what
    `PASSAGE_ENVELOPE_TOKENS` has to clear: the citation line scales with `final_k`, not with the
    text, so it is charged per passage.
    """
    backend = load_backend(
        EmbeddingSection(provider="fastembed", model=MODEL, dim=DIM, revision=None)
    )
    worst_ratio = Widest(0.0, 0, 0, "")
    widest = Widest(0.0, 0, 0, "")
    envelope = (0, "")
    total = 0
    for root in roots:
        for path in sorted(root.rglob("*.md")):
            if path.name.endswith(".pnk.yaml"):
                continue
            chunks = chunk_document(
                path.read_text(encoding="utf-8"),
                counter=backend,
                max_tokens=MAX_TOKENS,
                overlap=OVERLAP,
                kind="markdown",
            )
            for chunk in chunks:
                total += 1
                if not chunk.token_count:
                    continue
                found = Widest(
                    ratio=len(chunk.text) / chunk.token_count,
                    chars=len(chunk.text),
                    tokens=chunk.token_count,
                    path=str(path),
                )
                if found.ratio > worst_ratio.ratio:
                    worst_ratio = found
                if found.chars > widest.chars:
                    widest = found
                citation = f"{path} — {chunk.heading_path or ''}"
                if len(citation) > envelope[0]:
                    envelope = (len(citation), citation)
    return total, worst_ratio, widest, envelope


def main(argv: list[str]) -> int:
    roots = [Path(arg) for arg in argv[1:]]
    if not roots:
        print(f"usage: {argv[0]} <root> [root ...]", file=sys.stderr)
        return 2
    missing = [root for root in roots if not root.is_dir()]
    if missing:
        print(f"not a directory: {', '.join(str(root) for root in missing)}", file=sys.stderr)
        return 2

    total, worst_ratio, widest, envelope = measure(roots)
    print(f"chunks measured: {total}  (max_tokens={MAX_TOKENS}, overlap={OVERLAP}, model={MODEL})")
    print(f"worst ratio:   {worst_ratio.describe()}")
    print(f"widest chunk:  {widest.describe()}")
    print(f"longest citation envelope: {envelope[0]} chars — {envelope[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
