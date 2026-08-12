"""`.pinakes/deep/<operation_id>.json` — what one paid run was asked, and what it answered (E5).

**Why a file at all** (D-26 option A): the ledger deliberately stores **no query text**, so without
this nothing on disk would ever say what a `pnk budget` row was *for*. A cron run's `--json` is gone
the moment the pipe closes; the spend is not. The transcript is a second file beside the ledger, not
a loosening of it — the ledger's rule is unchanged.

**It cost real money to produce, so it is protected exactly as a paid cache entry is** (INVARIANTS):
nothing sweeps it, `--rebuild` does not touch it, and `pnk sync --clear-cache` — bare or `=paid` —
leaves it alone. `pnk sync --clear-cache=transcripts` is the one thing that removes it, and that
value names this store rather than authorising something inside the extraction cache.

**KB-local, and it never leaves `.pinakes/`.** It holds the question and the model's prose about
this KB's documents, which is why it is written where the KB's own gitignored state lives and is
returned to no caller that could forward it.

**Nothing here reads a clock, a manifest or an argument parser.** `now` arrives formatted and the
filters arrive as a mapping the caller already built, so the whole module is a pure serialisation
of a `DeepAnswer` plus an envelope — which is what makes a transcript testable without a run.

**A transcript records a run that produced an answer, and only that.** A run that was refused by a
budget window, declined at the confirmation, or halted with `[budget] on_exceed = "abort"` writes
none: `abort`'s whole meaning is that the rounds already paid for are *discarded* (D-23), and a file
holding the prose it discarded would hand back what the setting exists to withhold. Their spend is
in the ledger, where it belongs, and `pnk budget` names them as `ask` rows with no transcript.
"""

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from pinakes.budget.reserve import display_eur
from pinakes.ids import is_id

if TYPE_CHECKING:  # pragma: no cover — typing only, and deliberately so: see below
    from pinakes.deep.loop import DeepAnswer

#: **`DeepAnswer` is imported for typing only, and that is load-bearing.** `deep/loop.py` imports
#: `deep/client.py`, the module `tests/test_paid_path.py` asserts never reaches the MCP surface or a
#: free command. A runtime import here would drag it into every process that so much as writes or
#: reads a transcript path.

TRANSCRIPTS_DIRNAME: Final = "deep"
"""Under `.pinakes/`, beside `cache/` and `ledger.jsonl` — not *inside* `cache/`, because
everything in there is swept, surveyed and cleared by machinery keyed on extraction entries."""

SCHEMA_VERSION: Final = 1
"""This file format's version. Distinct from `deep/client.py`'s `SCHEMA_VERSION` (the shape of a
*response*) and from its `PROMPT_VERSION` (the wording that produced one) — both of which are
recorded *in* the transcript, because what a run produced depends on what it was asked."""

FILE_SUFFIX: Final = ".json"


def transcript_dir(state_dir: Path) -> Path:
    return state_dir / TRANSCRIPTS_DIRNAME


def transcript_path(state_dir: Path, operation_id: str) -> Path:
    """Where one operation's transcript lives.

    **The id is validated as a ULID before it becomes a filename.** `Accountant` mints one for every
    run, so in practice it always is — but `Accountant(operation_id=...)` is a parameter, and the
    one thing a caller-supplied path component must never be able to do is name a directory above
    this one. A `ValueError` rather than a `PinakesError`: reaching here with a malformed id is a
    defect in the caller, not something a user can cause or fix.
    """
    if not is_id(operation_id):
        raise ValueError(
            f"transcript_path: operation_id={operation_id!r} is not a ULID — a transcript is "
            "filed under the id `pnk budget` groups its calls by, and nothing else."
        )
    return transcript_dir(state_dir) / f"{operation_id}{FILE_SUFFIX}"


def answer_payload(deep: "DeepAnswer") -> dict[str, object]:
    """One `DeepAnswer` as JSON — the answer, the blocks it came in, and what it cost.

    **One renderer, two consumers**: `pnk ask --deep --json` prints this object under its `answer`
    key and the transcript stores it under the same one, so the object a script parsed off stdout
    and the object it reads back off disk are the same object. Two copies would be two shapes free
    to drift, and the drift would be silent — both would still be valid JSON.

    Money is a string of cents, never a float: JSON has no decimal type and a float would
    reintroduce exactly the representation error `Decimal` exists to avoid (INVARIANTS).
    """
    return {
        "text": answer_text(deep),
        "branch": deep.branch,
        "rounds_used": deep.rounds_used,
        "stopped_by": deep.stopped_by,
        "label": deep.label,
        "partial": deep.partial,
        "calls": deep.tally.calls,
        "call_ids": list(deep.tally.call_ids),
        "estimated_eur": display_eur(deep.estimate.total_eur),
        "spent_eur": display_eur(deep.spent_eur),
        "blocks": [
            {
                "round": block.round_number,
                "asked": list(block.asked),
                "text": block.text,
                "citations": [
                    {
                        "number": citation.number,
                        "doc_id": citation.doc_id,
                        "path": citation.path,
                        "citation": citation.locator,
                    }
                    for citation in block.citations
                ],
            }
            for block in deep.blocks
        ],
    }


def answer_text(deep: "DeepAnswer") -> str:
    """Every block's prose in order — the answer as one piece of text.

    **Blocks are joined, never renumbered.** Each block's `[n]` indexes the passages *its own* call
    was handed, and rewriting those numbers into a single global sequence would mean editing prose
    the model wrote: a `[3]` inside a quotation would be rewritten into a citation of something
    else. So the sources stay listed per block, right under the text that cites them.
    """
    return "\n\n".join(block.text for block in deep.blocks)


def record(
    *,
    deep: "DeepAnswer",
    operation_id: str,
    question: str,
    filters: Mapping[str, object],
    final_k: int,
    confidence: str,
    confidence_reason: str,
    model: str,
    prompt_version: int,
    response_schema_version: int,
    pinakes_version: str,
    now: str,
) -> dict[str, object]:
    """The whole file, as a dict — the envelope that makes an answer explicable, plus the answer.

    Everything here is either what the run was *asked* or what it *was*; nothing is re-derived.
    `deep` already carries the blocks, their citations resolved to documents, `stopped_by` out of
    `STOP_REASONS`, the estimate and the tally with its `call_ids` (E4's own handover note), so this
    serialises a value rather than recomputing one.

    **`confidence` is round 0's, and it is here because it is *why* this run cost what it did.**
    D-28 gives the branch to the free signal: `high` buys one synthesis call, `unknown` buys a loop
    with no early stop. A transcript naming the branch but not the reading that chose it would leave
    the one question a reader asks of a bill — *why was this the expensive shape?* — unanswerable.

    **`filters` is what the user typed, not what retrieval resolved it to.** D-27 gives `--deep`
    every one of `pnk search`'s filters, so the same question under `--tag` is a different run with
    a different price; recording the typed form is what lets someone re-run it. The caller builds
    the mapping because argparse is the caller's, and the expected shape is
    `{"tags": [...], "path_prefix": str|None, "source_type": str|None, "modified_after": str|None,
    "modified_before": str|None}`.

    `prompt_version` and `response_schema_version` are `deep/client.py`'s two constants, passed in
    rather than imported: importing them here would put the paid client in the import graph of
    everything that touches a transcript, which is the thing this module's typing-only import of
    `DeepAnswer` exists to avoid.
    """
    return {
        "schema": SCHEMA_VERSION,
        "operation_id": operation_id,
        "written_at": now,
        "pinakes_version": pinakes_version,
        "prompt_version": prompt_version,
        "response_schema_version": response_schema_version,
        "model": model,
        "question": question,
        "filters": dict(filters),
        "final_k": final_k,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "answer": answer_payload(deep),
    }


def write(state_dir: Path, body: Mapping[str, object]) -> Path:
    """Write one transcript, atomically, and return where it landed.

    **The filename comes out of the body, never beside it.** A transcript filed under an id other
    than its own is a record that would price the wrong run, and passing the id twice is how that
    happens — so there is one id, and `transcript_path` validates it.

    Temp file plus `os.replace`, with the temp named `.tmp` rather than `.json`: `Path.glob`
    matches dot-files, so a `*.json`-suffixed leftover from an uncatchable kill would be counted
    and cleared as though it were a finished transcript (`extract/cache.py` records the same trap).
    """
    operation_id = body.get("operation_id")
    if not isinstance(operation_id, str):
        raise ValueError("write: the body has no `operation_id` to file it under.")
    path = transcript_path(state_dir, operation_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            # `dict(body)`, because `json.dump` serialises a `dict` and not every `Mapping` —
            # accepting the wider type at the door and narrowing here is what lets a caller pass
            # whatever mapping it has without the failure landing three lines into an open file.
            json.dump(dict(body), handle, indent=2)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return path


def paths(state_dir: Path) -> tuple[Path, ...]:
    """Every transcript on disk, oldest first — ULIDs sort lexicographically by mint time."""
    directory = transcript_dir(state_dir)
    if not directory.is_dir():
        return ()
    return tuple(sorted(directory.glob(f"*{FILE_SUFFIX}")))


def stats(state_dir: Path) -> tuple[int, int]:
    """Count and bytes, for the confirmation prompt that precedes destroying them."""
    found = paths(state_dir)
    return len(found), sum(path.stat().st_size for path in found)


def call_ids(state_dir: Path) -> set[str]:
    """Every ledger `call_id` the transcripts on disk name — the join key that prices them.

    **The ledger is asked what they cost, never the transcript**, which is why this returns ids
    rather than a number: a transcript's own `spent_eur` is a snapshot taken at write time, and a
    later `pnk budget --resolve` closing an unknown outcome would leave it saying the wrong thing.
    The extraction cache is priced the same way and for the same reason (`sync.paid_cache_spend`).

    A file that cannot be read or that names no calls contributes nothing. It is also a file whose
    loss tells the reader least, so under-counting there is the safe direction.
    """
    found: set[str] = set()
    for path in paths(state_dir):
        try:
            raw: object = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict):
            continue
        answer = cast(dict[str, Any], raw).get("answer")
        if not isinstance(answer, dict):
            continue
        listed = cast(dict[str, Any], answer).get("call_ids")
        if not isinstance(listed, list):
            continue
        found.update(item for item in cast(list[Any], listed) if isinstance(item, str))
    return found


def clear_all(state_dir: Path) -> tuple[int, int]:
    """`--clear-cache=transcripts`: remove every transcript, and nothing else.

    The explicit, confirmed, whole-directory removal the flag value names — the counterpart of
    `extract/cache.clear_all`, kept separate from it because the two stores are protected
    separately and a user asking for one has not asked for the other.
    """
    found = paths(state_dir)
    total_bytes = sum(path.stat().st_size for path in found)
    for path in found:
        path.unlink(missing_ok=True)
    return len(found), total_bytes
