"""Identity: ULIDs are permanent, canonical, and strictly parsed."""

import pytest

from pinakes import ids
from pinakes.errors import InvalidIdError
from pinakes.ids import ID_LENGTH, is_id, mint_doc_id, mint_kb_id, parse_doc_id, parse_kb_id

CANONICAL = "01KYCJ8ZVMBJDB4FKRJRNYS5DT"


def test_minted_ids_are_canonical() -> None:
    for minted in (mint_kb_id(), mint_doc_id()):
        assert len(minted) == ID_LENGTH
        assert minted == minted.upper()
        assert parse_kb_id(minted) == minted


def test_minted_ids_are_distinct() -> None:
    assert len({mint_doc_id() for _ in range(1000)}) == 1000


def test_round_trip_preserves_the_exact_string() -> None:
    minted = mint_doc_id()
    assert parse_doc_id(minted) == minted


@pytest.mark.parametrize(
    ("raw", "why"),
    [
        ("", "empty"),
        ("01KYCJ8ZVMBJDB4FKRJRNYS5D", "too short"),
        ("01KYCJ8ZVMBJDB4FKRJRNYS5DTX", "too long"),
        ("01KYCI8ZVMBJDB4FKRJRNYS5DT", "contains ambiguous I"),
        ("01KYCU8ZVMBJDB4FKRJRNYS5DT", "contains ambiguous U"),
        ("81KYCJ8ZVMBJDB4FKRJRNYS5DT", "timestamp past the 48-bit ceiling"),
        ("01kycj8zvmbjdb4fkrjrnys5dt", "lowercase"),
        ("01KYCJ8ZVMBJDB4FKRJRNYS5dt", "mixed case"),
        ("research-archive", "an alias, not an ID"),
        (" 01KYCJ8ZVMBJDB4FKRJRNYS5DT", "leading whitespace"),
    ],
)
def test_malformed_ids_are_rejected(raw: str, why: str) -> None:
    with pytest.raises(InvalidIdError) as exc_info:
        parse_doc_id(raw)
    assert exc_info.value.raw == raw
    assert "document" in exc_info.value.message
    assert not is_id(raw), why


def test_lowercase_is_rejected_rather_than_normalised() -> None:
    """Two spellings of one identity would defeat the duplicate-ID check that protects §6.4."""
    minted = mint_doc_id()
    with pytest.raises(InvalidIdError):
        parse_doc_id(minted.lower())


class _Normalising:
    """A `python-ulid` that reads any case and writes the uppercase form — what 4.1.0 does.

    The two lowercase tests above passed on 4.0.1 only because the *library* refused lowercase, and
    failed the day 4.1.0 stopped refusing it: they tested the installed version, not this module.
    This stands in for the version that normalises, so the rejection is pinned to the code that owns
    it whichever `python-ulid` a fresh install resolves.
    """

    def __init__(self, text: str) -> None:
        self._text = text

    @classmethod
    def from_str(cls, raw: str) -> "_Normalising":
        return cls(raw.upper())

    def __str__(self) -> str:
        return self._text


@pytest.mark.parametrize(
    "raw",
    [CANONICAL.lower(), CANONICAL[:13] + CANONICAL[13:].lower()],
    ids=["lowercase", "mixed case"],
)
def test_a_library_that_normalises_case_does_not_make_a_non_canonical_id_valid(
    raw: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ids, "ULID", _Normalising)
    with pytest.raises(InvalidIdError) as doc_error:
        parse_doc_id(raw)
    with pytest.raises(InvalidIdError):
        parse_kb_id(raw)
    assert doc_error.value.raw == raw
    assert not is_id(raw)


def test_the_canonical_spelling_still_parses_through_a_normalising_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The control: a guard that refuses everything passes the test above and breaks every sync."""
    monkeypatch.setattr(ids, "ULID", _Normalising)
    assert parse_doc_id(CANONICAL) == CANONICAL
    assert parse_kb_id(CANONICAL) == CANONICAL
    assert is_id(CANONICAL)


def test_kb_and_document_errors_name_which_kind_failed() -> None:
    with pytest.raises(InvalidIdError) as kb_error:
        parse_kb_id("nope")
    with pytest.raises(InvalidIdError) as doc_error:
        parse_doc_id("nope")
    assert "KB" in kb_error.value.message
    assert "document" in doc_error.value.message


def test_errors_carry_a_remedy_that_forbids_renumbering() -> None:
    with pytest.raises(InvalidIdError) as exc_info:
        parse_doc_id("nope")
    assert "renumbering breaks every inbound link" in exc_info.value.remedy
