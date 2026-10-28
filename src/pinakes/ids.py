"""Document and KB identity.

Every document and every KB carries a ULID, minted once and **never regenerated** — every inbound
`pnk://` link depends on it and this design has no migration machinery by choice
(docs/INVARIANTS.md).

IDs are canonical uppercase Crockford base32, 26 characters. Lowercase is **rejected, not
normalised**: two spellings of one identity would slip straight past the duplicate-ID check that
protects §6.4's pairing, and an ID is machine-minted, so a lowercase one means something already
went wrong. **This module enforces that itself, by requiring the library's canonical spelling to
equal the input**: it used to lean on `python-ulid` refusing lowercase, and 4.1.0 does not — it
accepts lowercase and mixed case and returns the uppercase form (measured 20261028 22:24, against
4.0.1 refusing both), so on a fresh install every lowercase ID was a valid one. `python-ulid` is
still relied on for the rest — it rejects the ambiguous Crockford letters (`I`, `L`, `O`, `U` — all
four probed), wrong lengths, and timestamps past the 48-bit ceiling (verified 20260725 14:05,
python-ulid 4.0.1; the four letters re-probed 20261028 22:24 on 4.1.0).
"""

from typing import NewType

from ulid import ULID

from pinakes.errors import InvalidIdError

KbId = NewType("KbId", str)
"""A KB's permanent identity — the authority in a `pnk://` URI (docs/DESIGN.md §2.2)."""

DocId = NewType("DocId", str)
"""A document's permanent identity, living in its sidecar."""

OperationId = NewType("OperationId", str)
"""One user-facing invocation — a whole `pnk sync`, a whole `pnk ask --deep`. The unit
`[budget] per_operation_eur` bounds (I6b). Not permanent: it identifies a run, not a thing."""

CallId = NewType("CallId", str)
"""One API call. The unit a ledger reservation/outcome pair keys on, and what an extraction cache
entry joins against (I6b). Distinct from `OperationId` because one operation makes many calls, and
one word for both made `per_operation_eur` ambiguous by a factor of forty."""

ID_LENGTH = 26


def mint_kb_id() -> KbId:
    return KbId(str(ULID()))


def mint_doc_id() -> DocId:
    return DocId(str(ULID()))


def mint_operation_id() -> OperationId:
    return OperationId(str(ULID()))


def mint_call_id() -> CallId:
    return CallId(str(ULID()))


def _canonical(raw: str) -> str:
    """`raw` in the library's canonical spelling, or `ValueError` when `raw` is not that spelling.

    The comparison is the whole point: whatever a version of `python-ulid` is willing to read
    (lowercase, in 4.1.0), only the one spelling it would itself write is an ID here.
    """
    canonical = str(ULID.from_str(raw))
    if canonical != raw:
        raise ValueError(f"{raw!r} is not the canonical spelling {canonical!r}")
    return canonical


def _parse(raw: str, *, kind: str) -> str:
    try:
        return _canonical(raw)
    except (ValueError, TypeError) as exc:
        raise InvalidIdError(raw, kind=kind) from exc


def parse_kb_id(raw: str) -> KbId:
    return KbId(_parse(raw, kind="KB"))


def parse_doc_id(raw: str) -> DocId:
    return DocId(_parse(raw, kind="document"))


def is_id(raw: str) -> bool:
    """Whether `raw` is a well-formed ULID — for telling an ID from an alias, not for validation."""
    try:
        _canonical(raw)
    except (ValueError, TypeError):
        return False
    return True
