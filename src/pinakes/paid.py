"""What every paid client obeys — with no client in it.

Two modules in this package construct a vendor client: `extract/claude.py` (the PDF extractor,
I7b) and `deep/client.py` (`pnk ask --deep`, E3). They ask different things of the model and fail
into different sentences, but four rules are the same for both, and each of the four fails
*silently* when a second copy drifts from the first:

* **the key is `PINAKES_ANTHROPIC_API_KEY`, never the SDK's own variable** (`CLAUDE.md`);
* **the SDK's own retries are off**, because a retry it makes is a billed request the accountant
  never reserved (`build_client_kwargs`);
* **a transport failure is classified by whether it billed**, which is what decides `void` versus
  `unknown outcome` (`docs/INVARIANTS.md`, `budget/ledger.py`);
* **a reconciliation is computed from the response's own usage**, never from the reservation.

So they live here once. `CLAUDE.md` calls an `ANTHROPIC_API_KEY` fallback "the same defect, one
layer apart"; a second copy of the rule that forbids it is the same defect one file apart.

**Deliberately *not* on `.paid-path-allowlist`, and that is the point.** Nothing here imports a
vendor SDK — `classify` is handed the caller's already-imported module rather than importing one —
so `tools/paid_path_gate.py` scans this file like any other and would refuse an `import anthropic`
added to it. The allowlist stays two entries long: the two modules that actually construct a
client.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, cast

from pinakes.budget.prices import ModelPrice
from pinakes.errors import ApiKeyMissingError

API_KEY_ENV = "PINAKES_ANTHROPIC_API_KEY"
"""**Not** `ANTHROPIC_API_KEY`, and the difference is the whole point.

`anthropic.Anthropic()` reads `ANTHROPIC_API_KEY` from the process environment on its own. On any
machine where that is exported for some other tool — an editor, an agent, a shell someone forgot —
the paid path would find a live key it was never handed, and the "deliberate act of supplying the
key" that `CLAUDE.md` counts as a defence would not be one. Reading a name only Pinakes uses, and
passing it explicitly, makes the defence real rather than a property of a tidy machine.
"""


def resolve_api_key(environ: Mapping[str, str] | None = None, *, surface: str) -> str:
    """The key, or a named refusal. Never a fallback to the SDK's own variable.

    `environ` is injectable so the tests can prove the fallback is absent without mutating the
    process environment — the assertion that matters is that a set `ANTHROPIC_API_KEY` and an
    unset `PINAKES_ANTHROPIC_API_KEY` refuses.

    `surface` names the entry point that wanted to spend, because that is what the user typed and
    what they can turn off: "the `claude-vision` extractor" reads as nonsense to someone who ran
    `pnk ask --deep`, and a refusal naming the wrong command sends them to the wrong manifest key.
    """
    source = os.environ if environ is None else environ
    key = (source.get(API_KEY_ENV) or "").strip()
    if not key:
        raise ApiKeyMissingError(surface)
    return key


def build_client_kwargs() -> dict[str, Any]:
    """The client's construction arguments, as a pure function of nothing.

    `max_retries=0` because the SDK's default of 2 silently turns one `messages.create` into up to
    three billed HTTP requests — and a request retried after a timeout can be billed twice for
    generation the server already completed. The accountant owns retry, not the SDK.

    A function rather than a literal at the construction site so an unmarked test can assert it
    with `anthropic` absent: a test that could only inspect a stand-in would be asserting a
    property of itself.
    """
    return {"max_retries": 0}


class Billability(Enum):
    """Whether a failed call cost money — the only question that decides void vs. unknown."""

    NOT_BILLED = "not billed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Failure:
    """A transport failure, described rather than raised.

    A value and not an exception because the two paid entry points raise *different* exception
    types — an extraction failure isolates one document, a deep failure ends one question — while
    the classification itself is identical and must not be. Each caller wraps this in its own
    error; the branch order below is what neither of them re-derives.
    """

    message: str
    billability: Billability
    retryable: bool
    status: int | None = None


def classify(exc: Exception, *, sdk: Any) -> Failure:
    """Map an SDK exception onto the only distinction that matters: did it bill?

    `APIConnectionError` is a *sibling* of `APIStatusError`, not a subclass, and it splits by
    phase: a failure before any response byte never billed and may be retried, while a timeout —
    which the SDK models as its own subclass — is billable-unknown, because the server may have
    generated the response we never saw. **`APITimeoutError` is therefore checked first**; it is a
    subclass of `APIConnectionError`, so the opposite order would classify every timeout as
    not-billed and void a reservation for a call that may well have been charged.

    `sdk` is the caller's already-imported client module, passed in rather than imported here, so
    this module needs no allowlist entry and the tests can drive every branch with a stand-in
    module and `anthropic` absent. It is typed `Any` for the same reason: the SDK's stubs are not
    resolvable on a `[light]` install, where this classification still has to type-check.
    """
    if isinstance(exc, sdk.APITimeoutError):
        return Failure(
            f"the request timed out: {exc}", billability=Billability.UNKNOWN, retryable=False
        )
    if isinstance(exc, sdk.APIConnectionError):
        return Failure(
            f"the connection failed before any response: {exc}",
            billability=Billability.NOT_BILLED,
            retryable=True,
        )
    if isinstance(exc, sdk.APIStatusError):
        # Read through `getattr` and checked, rather than trusted: the SDK's own type stubs are
        # not resolvable on a `[light]` install, and a status silently arriving as something other
        # than an int would make `>= 500` a comparison against a string.
        raw: object = getattr(exc, "status_code", None)
        status = raw if isinstance(raw, int) else None
        return Failure(
            f"the API returned {status}: {exc}",
            billability=Billability.NOT_BILLED,
            retryable=status is not None and (status == 429 or status >= 500),
            status=status,
        )
    return Failure(f"the client failed: {exc}", billability=Billability.UNKNOWN, retryable=False)


class SchemaFailureError(Exception):
    """A response that returned but cannot be used: invalid JSON, or the wrong shape inside it.

    Not a `PinakesError`: it is control flow between a parser and the caller that decides whether
    to retry, never a sentence printed to a user. Each caller turns an exhausted retry budget into
    its own reported failure.
    """


def text_blocks(response: Mapping[str, Any]) -> str:
    """The response's text, selected by an explicit `block["type"] == "text"` check.

    The block union is narrowed by *reading the discriminator*, never by asserting a block is the
    variant we hoped for. A response carrying no text block at all is a schema failure, not a
    crash.
    """
    content: object = response.get("content")
    if not isinstance(content, list):
        raise SchemaFailureError("response carried no content list")
    parts: list[str] = []
    for block in cast(list[object], content):
        if not isinstance(block, dict):
            continue
        typed = cast(dict[str, object], block)
        if typed.get("type") != "text":
            continue
        text = typed.get("text")
        if isinstance(text, str):
            parts.append(text)
    if not parts:
        raise SchemaFailureError("response carried no text block")
    return "".join(parts)


def usage_of(response: Mapping[str, Any]) -> tuple[int, int]:
    """`(input_tokens, output_tokens)` as the response reports them, zero when it reports nothing.

    Zero rather than a raise: this runs on the reconciliation path, and a response whose usage
    block is missing must still close its ledger pair.
    """
    raw: object = response.get("usage")
    if not isinstance(raw, dict):
        return 0, 0
    usage = cast(dict[str, object], raw)
    inputs = usage.get("input_tokens")
    outputs = usage.get("output_tokens")
    return (
        inputs if isinstance(inputs, int) else 0,
        outputs if isinstance(outputs, int) else 0,
    )


def actual_cost_usd(response: Mapping[str, Any], *, price: ModelPrice) -> Decimal:
    """What the call really cost, from the response's own usage.

    The reservation is a worst case; **the reconciliation must supersede it with this**, or the
    protocol is a no-op that records the estimate twice and charges every window worst-case
    forever — the reservation stands, nothing corrects it, and `pnk budget` reports an estimate as
    if it were spend.
    """
    input_tokens, output_tokens = usage_of(response)
    million = Decimal(1_000_000)
    return (Decimal(input_tokens) / million) * price.input_per_mtok_usd + (
        Decimal(output_tokens) / million
    ) * price.output_per_mtok_usd
