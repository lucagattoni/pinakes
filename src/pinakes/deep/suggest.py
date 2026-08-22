"""What a `--deep` run learned about the KB's own shape, printed as a sidecar fragment (E7).

**It prints. It never writes.** D-25 option A splits the write-back in two: this half proposes,
and `--write-suggestions` — its own increment, with its own `docs/INVARIANTS.md` edit — stages.
Nothing here opens a file for writing.

**The observation is co-citation.** One `AnswerBlock` is one paid answering call over one merged
retrieval, so the documents it cited are the documents that *jointly* supported that answer. Every
unordered pair of distinct documents inside one block is a fact about this KB that the run paid to
discover and that nothing else records — the structure `docs/graph/PINAKES_APPROACH.md` § 6 says
every investigated system throws away per query.

**Observing and proposing are two functions, not one, and the split is the safety property.**
`co_citations` says what the run saw; `propose` decides what may be printed and re-checks every
endpoint it is handed against the run's own citations. If they were one function the check would be
unreachable — every candidate would come from the same expression that validates it, and no test
could tell a working guard from a missing one.

**The two rules from § 5 of the plan, and where each is enforced:**

* *A proposed link's endpoints must both be document ids that appeared in this run's own
  retrieval.* `propose` refuses any `doc_id` outside `cited_documents`. That set is **tighter than
  the rule** — cited is a subset of retrieved — so satisfying it satisfies § 5 strictly.
* *Resolved through the existing containment check rather than a new one.* `link.source_sidecar`
  is that check: it puts the path through `link._document_in` — inside the KB root, the document
  present, its sidecar present — and nothing here re-implements any part of it.
  `link.resolve_target` is deliberately **not** used, close as it looks: it also accepts the
  `<alias>:<path>` grammar, so a local document at `notes:2026.md` in a KB declaring a
  `[[links.kb]]` named `notes` would resolve against the *partner*.

**Why the model cannot reach this at all.** It never sees a document identifier: `answer_schema`
gives it passage *numbers* bounded by an `enum`, and `parse_answer` refuses one outside the range
it was sent. Hostile text inside a retrieved document therefore has no identifier to name and no
field to name it in — the injection defence is the wire format's, inherited here rather than
re-implemented as a filter over prose. **Nothing in this module reads `AnswerBlock.text`.**

**The ULID comes off the sidecar, not out of the index, and the two are compared.** A run's
`Citation.doc_id` is what the index held when the passage was retrieved; a sidecar that no longer
agrees means the KB moved under the run, and a `pnk://` built from the stale half would name a
document nobody cited. Such an endpoint is dropped.

**Every failure here is a dropped suggestion, never a raised one.** This runs after the money is
spent, and a courtesy at the end of a paid run must not become the thing that stops the answer
reaching the person who paid for it.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pinakes import link as link_module
from pinakes import sidecar as sidecar_module
from pinakes.deep.loop import DeepAnswer
from pinakes.errors import PinakesError
from pinakes.manifest import Manifest
from pinakes.uri import PnkUri

REL: Final = "co-cited"
"""The relation a suggestion proposes.

Names the evidence and nothing more: these two documents were cited in support of one answer. A
warmer word — `related`, `cites` — would claim a relationship the run did not observe, and renaming
it before pasting is the cheap half of reviewing a suggestion.
"""

ORIGIN: Final = "deep"
"""`origin: deep` on each proposed entry — the provenance D-25 specifies for a suggested link.

Pinakes never writes it in this release; it is printed so that what a user pastes says where it
came from. It survives the paste: `sidecar._links` reads `to` and `rel` and ignores every other
key, and `_merge_links` touches nothing else inside a matched entry, so an unknown per-link key is
round-tripped rather than dropped (`docs/DESIGN.md` §2.2).
"""

HEADER: Final = (
    "suggested links — documents this run cited together. Nothing was written: paste a block into "
    "the sidecar its first line names."
)
"""The one line above the fragment.

A constant because `tests/test_docs_quote_the_shipped_sentences.py` reads it: a sentence a
documented command prints is one the documentation may quote, and the gate compares the two.
"""

ALREADY_HAS_LINKS: Final = "already has `links:` — add these entries under it"
"""What a sidecar's first line says when it carries a `links:` key already.

Pasting a second `links:` into a mapping that has one is a YAML duplicate key, which ruamel refuses
outright — so that sidecar's block omits the key and says why instead.
"""


@dataclass(frozen=True, slots=True)
class CoCitation:
    """Two documents one or more of this run's answering calls cited together."""

    first: str
    second: str
    """Document ULIDs, ordered by the documents' KB-relative paths — see `co_citations`."""

    rounds: tuple[int, ...]
    """The rounds that cited the pair, ascending. More than one is a stronger observation, and it
    is the only strength signal available without a second paid call."""


@dataclass(frozen=True, slots=True)
class Suggestion:
    """One proposed `links[]` entry, and the sidecar it belongs in."""

    sidecar: str
    """The sidecar to paste into, relative to the KB root and POSIX-separated — the form every
    other path this command prints already takes."""

    source: str
    """The document that sidecar belongs to, KB-relative."""

    target: str
    """The document the entry points at, KB-relative — the readable half of `to`, because a ULID
    identifies nothing to a reader."""

    to: PnkUri
    rel: str

    rounds: tuple[int, ...]
    """`CoCitation.rounds`, carried through.

    The fragment renders the *count* rather than the numbers: the cheap branch's single block is
    round `0`, and `docs/CLI.md` calls round 0 the *free* retrieval — so a comment saying "cited in
    round 0" would name the one round that never made a paid call. The numbers stay on the object,
    where `--json` can have them and nothing has to read a sentence.
    """

    into_existing: bool
    """The sidecar already has a `links:` key, so its block omits one (`ALREADY_HAS_LINKS`)."""


def cited_documents(answer: DeepAnswer) -> dict[str, str]:
    """Every document this run cited: doc ULID → KB-relative path.

    **This is the membership set § 5's rule is checked against.** A citation is a passage the run
    retrieved *and* an answering call cited, so this is a subset of the retrieved set and refusing
    anything outside it is strictly the stronger check. It is also the only set a `DeepAnswer`
    carries — and widening `DeepAnswer` to carry the retrieved set would loosen the rule to buy
    nothing.
    """
    return {
        citation.doc_id: citation.path for block in answer.blocks for citation in block.citations
    }


def co_citations(answer: DeepAnswer) -> tuple[CoCitation, ...]:
    """What the run observed: every pair of distinct documents some block cited together.

    **Ordered by path, not by citation order.** The model decides which passage it cites first and
    two runs over the same evidence can differ, so pairing on that would make the suggested
    *direction* a property of the run rather than of the KB — and a user who pasted one entry and
    re-asked would meet its mirror image.

    Observation only: nothing here touches the disk, and a pair named here has still to survive
    `propose`.
    """
    cited = cited_documents(answer)
    rounds: dict[tuple[str, str], list[int]] = {}
    for block in answer.blocks:
        documents = sorted({citation.doc_id for citation in block.citations}, key=cited.__getitem__)
        for index, first in enumerate(documents):
            for second in documents[index + 1 :]:
                rounds.setdefault((first, second), []).append(block.round_number)
    return tuple(
        CoCitation(first=first, second=second, rounds=tuple(sorted(set(numbers))))
        for (first, second), numbers in rounds.items()
    )


@dataclass(frozen=True, slots=True)
class _Endpoint:
    """One resolved endpoint: where its sidecar is, what it already says, and what it may be
    called."""

    path: str
    sidecar: Path
    uri: PnkUri
    links: tuple[sidecar_module.Link, ...]
    has_links_key: bool


def _resolve(doc_id: str, *, cited: Mapping[str, str], manifest: Manifest) -> _Endpoint | None:
    """One endpoint, or `None` when it may not be suggested.

    Four refusals, in the order they can be decided:

    1. **the run never cited it** — § 5's rule. It is the only one a document *inside* this KB
       would ever meet: every other check below passes for any document `pnk sync` has indexed,
       which is exactly why the check cannot be inferred from the others;
    2. **the containment check refuses the path** — `link.source_sidecar`, unchanged and
       un-reimplemented: outside the KB root, no such document, or no sidecar to carry a ULID;
    3. **the sidecar will not parse** — a `SidecarError`, and so a `PinakesError` too;
    4. **the sidecar's ULID is not the one the run retrieved** — the KB moved under the run, and
       the pair would name a document nobody cited.

    A refusal is `None` rather than an exception on purpose: see the module docstring.
    """
    path = cited.get(doc_id)
    if path is None:
        return None
    try:
        sidecar_path = link_module.source_sidecar(manifest, path)
        loaded = sidecar_module.read(sidecar_path, owner=manifest.kb.id)
    except (PinakesError, OSError):
        return None
    if str(loaded.id) != doc_id:
        return None
    return _Endpoint(
        path=path,
        sidecar=sidecar_path,
        uri=PnkUri(kb=manifest.kb.id, doc=loaded.id),
        links=loaded.links,
        has_links_key="links" in loaded.present,
    )


def propose(
    observations: Sequence[CoCitation], *, cited: Mapping[str, str], manifest: Manifest
) -> tuple[Suggestion, ...]:
    """The observations that may be printed, resolved to sidecars and URIs, in a stable order.

    **Every endpoint is re-checked against `cited`**, whoever built the observations. That is § 5's
    rule, and it is enforced here rather than trusted from `co_citations` because a rule that only
    holds while one caller stays correct is not enforced at all.

    **The entry goes in the first document's sidecar.** A link is written forward into one sidecar
    and the other end learns about it by reverse-scan (`pnk link`), so a pair needs one direction
    and the choice between them is arbitrary — which makes an arbitrary but *deterministic* rule
    the right one.

    **A pair already linked in that sidecar is not proposed**, whatever its `rel`: a suggestion is
    an *addition*, an entry that is already authored is not one, and printing it would spend the
    reader's attention on a paste that changes nothing.
    """
    suggestions: list[Suggestion] = []
    for observation in observations:
        source = _resolve(observation.first, cited=cited, manifest=manifest)
        target = _resolve(observation.second, cited=cited, manifest=manifest)
        if source is None or target is None:
            continue
        if any(existing.to == target.uri for existing in source.links):
            continue
        suggestions.append(
            Suggestion(
                sidecar=source.sidecar.relative_to(manifest.root).as_posix(),
                source=source.path,
                target=target.path,
                to=target.uri,
                rel=REL,
                rounds=observation.rounds,
                into_existing=source.has_links_key,
            )
        )
    # **By path at both levels, never by URI.** A ULID's order is its mint order, which is
    # arbitrary to a reader and to this KB's shape alike — so sorting the entries inside one
    # sidecar by `to` would print them in an order nothing on screen explains.
    suggestions.sort(key=lambda item: (item.sidecar, item.target))
    return tuple(suggestions)


def for_run(answer: DeepAnswer, *, manifest: Manifest) -> tuple[Suggestion, ...]:
    """`co_citations` then `propose` — what a caller with a finished run wants.

    A named composition rather than a third implementation: the two steps stay separately callable,
    which is what lets `propose`'s guard be tested against a pair no run would produce.
    """
    return propose(co_citations(answer), cited=cited_documents(answer), manifest=manifest)


def render(suggestions: Sequence[Suggestion]) -> str:
    """The copy-pasteable fragment: `HEADER`, then one block per sidecar.

    Empty for no suggestions, so a caller prints nothing rather than an empty section — an answer
    citing one document per block produces none, and on a narrow question that is the common case
    rather than an edge one.

    **Built as text rather than dumped through `ruamel`.** Every value in it is constrained to a
    charset that needs no quoting — `to` is a `PnkUri`, so two ULIDs and a fixed scheme; `rel` and
    `origin` are the constants above — and `test_deep_suggest.py` pins that against
    `sidecar.needs_quoting` rather than asserting it here. What a dumper would buy is quoting that
    is not needed; what it would cost is that the round-trip test would then be a test of `ruamel`.
    """
    if not suggestions:
        return ""
    blocks: list[str] = []
    for sidecar in sorted({item.sidecar for item in suggestions}):
        group = [item for item in suggestions if item.sidecar == sidecar]
        note = f" {ALREADY_HAS_LINKS}" if group[0].into_existing else ""
        lines = [f"# {sidecar}{note}"]
        if not group[0].into_existing:
            lines.append("links:")
        for item in group:
            rounds = "1 round" if len(item.rounds) == 1 else f"{len(item.rounds)} rounds"
            lines.append(f"- to: {item.to}  # {item.target}, cited with it in {rounds}")
            lines.append(f"  rel: {item.rel}")
            lines.append(f"  origin: {ORIGIN}")
        blocks.append("\n".join(lines))
    return f"{HEADER}\n\n" + "\n\n".join(blocks)
