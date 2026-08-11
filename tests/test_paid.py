"""`src/pinakes/paid.py` — the rules every paid client obeys, with no client in it.

**Not `test_paid_path.py`**, which is about the *allowlist gate*: which modules may import a client
at all. This file is about what the two that may then have to do — the key's name, the SDK's
retries, and the classification that decides whether a failed call is voided or left unresolved.

Every test here runs with `anthropic` absent. `classify` is handed the caller's already-imported SDK
module rather than importing one, which is both why `paid.py` needs no allowlist entry and why a
stand-in module can drive every branch of it.
"""

from importlib.util import find_spec
from pathlib import Path

import pytest

from pinakes.errors import ApiKeyMissingError
from pinakes.paid import API_KEY_ENV, Billability, build_client_kwargs, classify, resolve_api_key

STUB = Path(__file__).parent.parent / "stubs" / "anthropic.pyi"


class _FakeSdk:
    """The four exception classes `classify` reads, in the **real** inheritance relationship —
    `APITimeoutError` under `APIConnectionError`, and `APIConnectionError` a *sibling* of
    `APIStatusError`. `stubs/anthropic.pyi` states the same shape, and one test below holds the two
    against each other so this stand-in cannot quietly describe a hierarchy the SDK does not have.
    """

    class APIError(Exception): ...

    class APIStatusError(APIError):
        # Declared here and deliberately **not** in `stubs/anthropic.pyi`: the stub is a claim about
        # a library, and `classify` reads this through `getattr` with an `isinstance` check rather
        # than trusting a shape this project wrote down itself. The fake declares it because a test
        # has to be able to set it.
        status_code: object

    class APIConnectionError(APIError): ...

    class APITimeoutError(APIConnectionError): ...


def _status_error(status: object) -> Exception:
    exc = _FakeSdk.APIStatusError("boom")
    exc.status_code = status
    return exc


# --- the key is supplied to pinakes, never found by the SDK --------------------------------------


def test_the_key_is_read_from_the_pinakes_variable_and_stripped() -> None:
    assert API_KEY_ENV == "PINAKES_ANTHROPIC_API_KEY"
    assert resolve_api_key({API_KEY_ENV: "  sk-test\n"}, surface="x") == "sk-test"


def test_an_ambient_anthropic_api_key_is_not_enough() -> None:
    """The rule the whole module exists for: `anthropic.Anthropic()` reads `ANTHROPIC_API_KEY` from
    the process environment by itself, so on a machine where another tool exports it the paid path
    would find a live key nobody handed it."""
    with pytest.raises(ApiKeyMissingError):
        resolve_api_key({"ANTHROPIC_API_KEY": "sk-ambient"}, surface="x")


@pytest.mark.parametrize("value", ["", "   ", "\n"])
def test_a_blank_key_refuses_rather_than_being_sent(value: str) -> None:
    with pytest.raises(ApiKeyMissingError):
        resolve_api_key({API_KEY_ENV: value}, surface="x")


def test_the_refusal_names_the_surface_that_wanted_to_spend() -> None:
    """Two paid entry points, two refusals. The surface is a parameter rather than a constant here
    because a refusal naming the `claude-vision` extractor to someone who typed `pnk ask --deep`
    sends them to a manifest section they never touched."""
    for surface in ("the `claude-vision` extractor", "`pnk ask --deep`"):
        with pytest.raises(ApiKeyMissingError) as exc_info:
            resolve_api_key({}, surface=surface)
        assert exc_info.value.message.startswith(surface)
        assert API_KEY_ENV in exc_info.value.remedy


def test_the_sdk_retries_are_off() -> None:
    """The SDK's default of 2 silently turns one `messages.create` into up to three billed HTTP
    requests, and a request retried after a timeout can be billed twice for generation the server
    already completed. The accountant owns retry, not the SDK."""
    assert build_client_kwargs() == {"max_retries": 0}


# --- classification: the only question is whether the call billed --------------------------------


def test_a_timeout_is_classified_before_the_connection_error_it_is_a_subclass_of() -> None:
    """The single most consequential ordering in the paid path, and it had **no direct test** until
    E3 made the classifier shared code: every branch of it was reached only through a fixture that
    raised an already-classified error.

    A timeout *is* an `APIConnectionError`, so checking the parent first classifies every timeout as
    not-billed — which voids a reservation for a call the server may have generated and charged for.
    """
    timeout = classify(_FakeSdk.APITimeoutError("slow"), sdk=_FakeSdk)
    assert timeout.billability is Billability.UNKNOWN
    assert timeout.retryable is False

    connection = classify(_FakeSdk.APIConnectionError("refused"), sdk=_FakeSdk)
    assert connection.billability is Billability.NOT_BILLED
    assert connection.retryable is True


def test_the_stub_states_the_hierarchy_the_classifier_depends_on() -> None:
    """`stubs/anthropic.pyi` is what pyright reads on a `[light]` install, and `_FakeSdk` above is
    what this suite reads. Both are claims about a library neither of them is — so they are held
    against each other, and against the real package when it happens to be installed."""
    stub = STUB.read_text(encoding="utf-8")
    assert "class APITimeoutError(APIConnectionError)" in stub
    assert "class APIConnectionError(APIError)" in stub
    assert "class APIStatusError(APIError)" in stub

    if find_spec("anthropic") is not None:  # pragma: no cover - the [light] leg skips this half
        import anthropic

        assert issubclass(anthropic.APITimeoutError, anthropic.APIConnectionError)
        assert not issubclass(anthropic.APIConnectionError, anthropic.APIStatusError)


@pytest.mark.parametrize(
    ("status", "retryable"), [(429, True), (500, True), (503, True), (400, False), (404, False)]
)
def test_a_status_error_is_never_billed_and_retries_only_where_retrying_can_help(
    status: int, retryable: bool
) -> None:
    failure = classify(_status_error(status), sdk=_FakeSdk)
    assert failure.billability is Billability.NOT_BILLED
    assert failure.retryable is retryable
    assert failure.status == status


def test_a_status_arriving_as_something_other_than_an_int_does_not_crash_the_comparison() -> None:
    """`>= 500` against a string raises, and it would raise on the failure path — where a crash
    replaces a classified failure with a traceback and an open reservation."""
    failure = classify(_status_error("500"), sdk=_FakeSdk)
    assert failure.status is None
    assert failure.retryable is False
    assert failure.billability is Billability.NOT_BILLED


def test_an_exception_the_hierarchy_does_not_cover_is_billable_unknown() -> None:
    """The safe default: something nobody classified may have billed."""
    failure = classify(ValueError("who knows"), sdk=_FakeSdk)
    assert failure.billability is Billability.UNKNOWN
    assert failure.retryable is False
