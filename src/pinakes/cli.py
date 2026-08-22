"""Command-line entry point.

The whole v0.1 command surface (docs/DESIGN.md §8) is declared here from the start, with each
command dispatching to a `run(args) -> int`. Commands whose increment has not landed raise
`NotImplementedYetError`, so the CLI never implies a capability it lacks.

Exit codes are a contract, not an accident:

    0  success
    1  operational failure — a `PinakesError`; message and remedy printed to stderr
    2  usage error — argparse's own code for a malformed invocation
    3  no baseline — `pnk upgrade` alone: the comparison could not be made, and no action of the
       user's would make it possible. Distinct from 1 because nothing is wrong and nothing is
       theirs to fix; distinct from 0 because a script reads 0 as "up to date".

The framework is stdlib `argparse`: v0.1's flag surface is small and a dependency would buy
nothing (plans/20260725_1317-v0.1.md, decisions table).
"""

import argparse
import sys
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # `sync` pulls numpy and the store; the CLI stays fast to start
    import sqlite3
    from decimal import Decimal

    from pinakes.deep.loop import DeepAnswer
    from pinakes.deep.suggest import Suggestion
    from pinakes.embed import EmbeddingBackend, Reranker
    from pinakes.search import Filters, Passage, SearchResult
    from pinakes.sync import SyncReport

from pinakes import __version__
from pinakes.errors import NotImplementedYetError, PinakesError
from pinakes.manifest import Manifest

DESIGN_URL = "https://github.com/lucagattoni/pinakes/blob/main/docs/DESIGN.md"

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_NO_BASELINE = 3

# Where the dispatch target is stashed on the parsed namespace. Underscore-prefixed so it can never
# collide with a future command's own option: argparse would silently let `--runner` overwrite the
# dispatch target, and the CLI would call the wrong thing (or a string).
RUNNER_DEST = "_runner"

type CommandRunner = Callable[[argparse.Namespace], int]


class Command:
    """One `pnk` subcommand: its help text, the increment that implements it, and its runner."""

    def __init__(
        self,
        name: str,
        help_: str,
        increment: str,
        *,
        runner: CommandRunner | None = None,
        arguments: Callable[[argparse.ArgumentParser], None] | None = None,
    ) -> None:
        self.name = name
        self.help = help_
        self.increment = increment
        self._runner = runner
        self._arguments = arguments

    def configure(self, parser: argparse.ArgumentParser) -> None:
        if self._arguments is not None:
            self._arguments(parser)

    def run(self, args: argparse.Namespace) -> int:
        if self._runner is None:
            raise NotImplementedYetError(self.name, increment=self.increment)
        return self._runner(args)


def _kb_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--kb",
        type=Path,
        default=None,
        metavar="PATH",
        help="KB root (default: the nearest pinakes.toml, searching upwards)",
    )


def _init_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="directory to create the KB in")
    parser.add_argument("--name", default=None, help="human-facing name (default: the directory)")
    parser.add_argument("--template", default="notes", help="blueprint to stamp from")
    parser.add_argument(
        "--backend",
        default="st",
        choices=["st", "light"],
        help="which install extra's models to stamp (default: st)",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="also write a GitHub Actions workflow that syncs with the free extractor",
    )


def run_init(args: argparse.Namespace) -> int:
    from pinakes.hooks import FREE_BACKEND_NOTICE
    from pinakes.init import init

    result = init(
        args.path,
        name=args.name,
        template_name=args.template,
        ci=args.ci,
        backend=args.backend,
    )
    print(f"created {result.root} from {result.template}")
    print(f"  kb id: {result.kb_id}  (permanent — never edit it)")
    if result.workflow is not None:
        print(f"  workflow: {result.workflow.relative_to(result.root)}")
        print(f"  it {FREE_BACKEND_NOTICE}")
    if result.adopted:
        # Named, never merely counted. A file silently *not* written is indistinguishable from one
        # written and then reverted, and the whole point of adopting a directory is that the files
        # already in it are the user's.
        listed = ", ".join(str(path.relative_to(result.root)) for path in result.adopted)
        print(f"  left as they were: {listed}")
    if result.gitignore_unprotected:
        print("\n  ⚠️  your .gitignore does not ignore `.pinakes/`. Add this line:")
        print("        .pinakes/")
        print("      It holds the index and the spend ledger — ignoring it is what keeps them")
        print("      off any remote you push to.")
    print("\nNext:")
    print(f"  1. put Markdown files in {result.root / 'docs'}")
    print("  2. `pnk sync` to index them, then commit the sidecars it writes")
    print('  3. `pnk search "…"` to search, for free, offline')
    return EXIT_OK


def _templates_arguments(parser: argparse.ArgumentParser) -> None:
    # **No `--kb`, deliberately.** This lists what *this build* has installed, which is the same
    # answer wherever it is run from — a `--kb` would imply the listing varies per KB and invite a
    # later reader to "fix" its absence. Which template a given KB is on is a different question,
    # and `pnk upgrade` is the command that answers it.
    parser.add_argument("--json", action="store_true", help="machine-readable output")


def run_templates(args: argparse.Namespace) -> int:
    """`pnk templates`. What this build can stamp a KB from.

    **The listing exists because the information did not.** `template.available()` was reachable
    only by naming a template that does not exist and reading the error, so the way to find out what
    was installed was to get something wrong first.

    **CLI-only, decided 20260808 — there is no `pinakes_*` tool for this.** The MCP server answers
    about the KBs it was pointed at, and a template is not one of them: it is package data consumed
    at *creation* time, and creation has no MCP surface at all. A tool listing templates would name
    things the caller has no way to act on, and it would be the first tool on that surface reporting
    machine state from outside the served KBs — which `docs/DESIGN.md` §4.7 states as a boundary
    rather than a convenience.

    **One damaged template does not hide the rest, and that is this command's problem alone.**
    Before this command, a damaged template broke only the run that named it; a listing that
    aborted on the first bad one would report nothing about the good ones while telling the user
    their install has no templates. So the failure is caught per template and shown as a row.

    That is still this command's own concern after open-corrections item 3 closed. **The item made
    the failure a `TemplateError` instead of a bare `OSError`, which changes what to catch and
    nothing about why to catch it**: `cli.main` now prints a message rather than a traceback for
    the *single*-template commands, but a listing has no message to print — it has a row per
    template, and the run must continue to the next one.
    """
    import json as json_module

    from pinakes.errors import TemplateError
    from pinakes.template import TemplateInfo, available, describe

    # `str` in the second slot is the failure. Keyed by the *directory* name rather than the
    # declared one, because a template that cannot be read has no declared name to key it by.
    rows: list[tuple[str, TemplateInfo | str]] = []
    for name in available():
        try:
            rows.append((name, describe(name)))
        except TemplateError as exc:
            # One type, because `describe` now raises exactly one. This caught `(OSError,
            # ValueError)` while the reads underneath were unguarded — a missing `template.toml`
            # arrived as `FileNotFoundError`, a malformed one as `tomllib.TOMLDecodeError`. Both
            # are `TemplateError` now, so those arms would be dead, and a dead arm here is not
            # harmless: it would keep this listing green if `describe` ever started raising raw
            # again, which is the whole property the guard exists to hold.
            rows.append((name, exc.message))

    damaged = [name for name, entry in rows if isinstance(entry, str)]

    if args.json:
        print(
            json_module.dumps(
                [
                    {
                        "name": entry.name,
                        "version": entry.version,
                        # The string a manifest records, emitted rather than left to be
                        # reassembled: `name@version` is `TemplateInfo.reference`'s format, and a
                        # consumer joining the two fields itself would be a second definition of it.
                        "reference": entry.reference,
                        "description": entry.description,
                    }
                    if isinstance(entry, TemplateInfo)
                    else {"name": name, "unreadable": entry}
                    for name, entry in rows
                ],
                indent=2,
            )
        )
        return EXIT_FAILURE if damaged else EXIT_OK

    if not rows:
        # Reachable only if the package data is damaged, which is exactly when a silent empty
        # listing is worst: it reads as "you have no templates" rather than "this install is
        # broken".
        print("no templates are installed — this build's package data is incomplete.")
        return EXIT_FAILURE

    # The declared name where there is one, the directory name where there is not — which is the
    # same string for every template that parses, and the only one available for a template that
    # does not. Both surfaces use it, so the human listing and `--json` never name a template
    # differently.
    display = {
        name: entry.name if isinstance(entry, TemplateInfo) else name for name, entry in rows
    }
    width = max(len(shown) for shown in display.values())
    for name, entry in rows:
        if isinstance(entry, TemplateInfo):
            print(f"{display[name].ljust(width)}  {entry.version}  {entry.description}")
        else:
            print(f"{display[name].ljust(width)}  ?      unreadable: {entry}")
    if damaged:
        print(f"\nreinstall pinakes: {', '.join(damaged)} could not be read.")
    # Non-zero because something *is* wrong and it is the user's to fix. The good rows are still
    # printed: naming what broke *and* answering the question asked beats doing neither, which is
    # what the traceback did.
    return EXIT_FAILURE if damaged else EXIT_OK


def _retrieval_arguments(parser: argparse.ArgumentParser, *, query_help: str) -> None:
    """The filter surface `pnk search` and `pnk ask` share, declared once for both.

    D-27 of `plans/20260811_1358-deep-release.md`: `ask` takes **every** one of `search`'s filters,
    because a filter narrows retrieval and so narrows what answering the question would take.
    Declared here rather than copied, so the two commands cannot drift into accepting different
    flags — the failure that would leave `--source-type` meaning something on one and nothing on
    the other, with `--help` right about both.
    """
    parser.add_argument("query", help=query_help)
    _kb_argument(parser)
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        metavar="TAG",
        help="only documents carrying this tag (repeatable)",
    )
    parser.add_argument(
        "--path-prefix",
        default=None,
        metavar="PREFIX",
        help="only documents whose path starts with this",
    )
    parser.add_argument(
        "--source-type", default=None, metavar="TYPE", help="markdown, text, code or pdf"
    )
    parser.add_argument(
        "--modified-after",
        default=None,
        metavar="YYYYMMDD",
        help="only documents modified on or after this date",
    )
    parser.add_argument(
        "--modified-before",
        default=None,
        metavar="YYYYMMDD",
        help="only documents modified on or before this date",
    )
    parser.add_argument("-k", type=int, default=None, help="how many passages to return")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--offline", action="store_true", help="never reach out for model weights")


def _search_arguments(parser: argparse.ArgumentParser) -> None:
    _retrieval_arguments(parser, query_help="what to search for")


def _ask_arguments(parser: argparse.ArgumentParser) -> None:
    _retrieval_arguments(parser, query_help="the question to answer")
    parser.add_argument(
        "--deep",
        action="store_true",
        help="answer it with paid reasoning, bounded by [deep] and [budget] (costs money)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help=(
            "answer this run's confirmation prompt (cron use). Raises no cap — a run over a "
            "[budget] window is refused whether or not this is given"
        ),
    )


def _as_timestamp(value: str | None) -> float | None:
    from datetime import datetime

    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").timestamp()
    except ValueError as exc:
        raise PinakesError(
            f"{value!r} is not a date.", remedy="Use YYYYMMDD, for example 20260725."
        ) from exc


@dataclass(frozen=True, slots=True)
class _Retrieval:
    """One KB opened once: the manifest, the models and the index a command searches through.

    **Opened once because `pnk ask --deep` searches many times.** `pnk search` retrieves a single
    query and closes; the loop retrieves once per subproblem, several times a round. Until E4 this
    was one function that loaded the embedding backend, loaded the reranker and opened the index on
    every call — which for the loop would mean reloading two models per subproblem, on a path where
    the models are the slowest thing there is.

    The filters and the limit belong here rather than to each call, because §5 requires a
    subproblem's retrieval to inherit the caller's filters exactly: a per-call parameter is a
    parameter something could pass differently, and the one thing that must never differ between
    round 0 and a subproblem's search is which documents are in scope.
    """

    manifest: Manifest
    connection: "sqlite3.Connection"
    backend: "EmbeddingBackend"
    reranker: "Reranker | None"
    filters: "Filters"
    limit: int | None

    @property
    def final_k(self) -> int:
        """How many passages a search here may return — `-k` when given, else the manifest's.

        The number `deep/estimate.py` prices a call at and `deep/client.py` caps one to, so it is
        read from the one place that decides it rather than recomputed beside each of them.
        """
        return self.limit or self.manifest.retrieval.final_k

    def search(self, query: str) -> "SearchResult":
        from pinakes.search import search

        return search(
            self.connection,
            self.manifest,
            query,
            backend=self.backend,
            reranker=self.reranker,
            filters=self.filters,
            limit=self.limit,
        )

    def confidence(self, passages: "Sequence[Passage]") -> tuple[str, str]:
        """§4.2's signal over an arbitrary passage set — the loop's sufficiency step (§5).

        The same function `search()` reports its own confidence with, against the same manifest and
        the same reranker instance, so a run cannot stop early on a threshold reading that
        `pnk search` would have disagreed with.
        """
        from pinakes.search import confidence_of

        return confidence_of(self.manifest, self.reranker, passages)


@contextmanager
def _retrieval(args: argparse.Namespace) -> "Generator[_Retrieval]":
    """Open the §4.1 pipeline for whichever command asked. Free, and identical for all of them.

    `pnk search` and `pnk ask` differ in what they *say* about a result, never in how they get one
    (D-21). Two copies of this would be two retrieval pipelines wearing one name.
    """
    from pinakes import manifest as manifest_module
    from pinakes import store
    from pinakes.embed import load_backend, load_reranker
    from pinakes.search import Filters

    loaded = manifest_module.discover(args.kb)
    backend = load_backend(loaded.embedding, offline=args.offline)
    reranker = (
        load_reranker(loaded.rerank, offline=args.offline)
        if loaded.retrieval.rerank == "local"
        else None
    )

    connection = store.connect_ro(loaded.index_path)
    try:
        yield _Retrieval(
            manifest=loaded,
            connection=connection,
            backend=backend,
            reranker=reranker,
            filters=Filters(
                tags=tuple(args.tag),
                path_prefix=args.path_prefix,
                source_type=args.source_type,
                modified_after=_as_timestamp(args.modified_after),
                modified_before=_as_timestamp(args.modified_before),
            ),
            limit=args.k,
        )
    finally:
        connection.close()


def _retrieve(args: argparse.Namespace) -> "SearchResult":
    """One query through the pipeline, for a command that asks exactly one."""
    with _retrieval(args) as pipeline:
        return pipeline.search(args.query)


def _retrieval_payload(result: "SearchResult") -> dict[str, object]:
    """The `--json` object both retrieval commands print. `pnk ask` adds two keys to it."""
    return {
        "query": result.query,
        "confidence": result.confidence,
        "confidence_reason": result.confidence_reason,
        "considered": result.considered,
        "passages": [
            {
                "doc_id": passage.doc_id,
                "path": passage.path,
                "title": passage.title,
                "heading_path": passage.heading_path,
                "char_start": passage.char_start,
                "char_end": passage.char_end,
                # Separate fields, never the rendered `p12-13`: a consumer that has to parse a
                # citation back apart is a consumer that will get it wrong.
                "page_start": passage.page_start,
                "page_end": passage.page_end,
                "citation": passage.citation(),
                "stale_extraction": passage.stale_extraction,
                "text": passage.text,
                "rerank_score": passage.rerank_score,
                "fused_score": passage.fused_score,
            }
            for passage in result.passages
        ],
    }


def _print_passages(result: "SearchResult") -> None:
    """The numbered, cited blocks both retrieval commands render."""
    for position, passage in enumerate(result.passages, start=1):
        heading = f" — {passage.heading_path}" if passage.heading_path else ""
        print(f"[{position}] {passage.path}{heading}")
        for line in passage.text.strip().splitlines():
            print(f"    {line}")
        print(f"    ({passage.citation()})")
        if passage.stale_extraction is not None:
            # Marked, never withheld (§4.4, decision 13): the text is correct, merely extracted by
            # a paid backend the manifest has since moved off.
            print(
                f"    ! extracted by a paid backend since superseded "
                f"({passage.stale_extraction}); re-extracting would spend."
            )
        print()


def run_search(args: argparse.Namespace) -> int:
    """`pnk search`. Prints cited passages and an honest confidence line."""
    import json as json_module

    from pinakes.search import LOW, UNKNOWN

    result = _retrieve(args)

    if args.json:
        print(json_module.dumps(_retrieval_payload(result), indent=2))
        return EXIT_OK

    if not result.passages:
        print("no passages matched.")
        print(f"confidence: {result.confidence} — {result.confidence_reason}")
        return EXIT_OK

    _print_passages(result)

    print(f"confidence: {result.confidence} — {result.confidence_reason}")
    # The constants, not `("low", "unknown")` as this read until E1: `_escalation` two functions
    # below compares against the same values, and two spellings of one vocabulary in one file is
    # how they come to disagree.
    if result.confidence in (LOW, UNKNOWN):
        # Names `pnk ask`, and — since E4 — its `--deep`, which now exists. The sentence this
        # replaced advertised a command *and* a flag that could not be typed, in the very line
        # whose test is named for not doing that; the rule was never "say less", it was "name
        # only what this build can do".
        print(
            "retrieval-only result. `pnk ask` prints the same evidence plus what answering the "
            "question would take and what it would cost, and `pnk ask --deep` pays to answer it. "
            "Narrowing the query or adding a filter is the free lever."
        )
    return EXIT_OK


NO_ANSWER_SYNTHESISED = "no answer was synthesised — this is evidence, not a conclusion."
"""Printed by every `pnk ask`, whatever the confidence.

Someone typing `ask` expects an answer, and passages are not one. The line is the difference
between an honest retrieval surface and one that lets a reader mistake evidence for a conclusion.
`tests/free_path_run.py` also matches on it, which is how the free-path gate proves it reached
`pnk ask` at all rather than assuming it.
"""

DEEP_OFFER = "`pnk ask --deep` pays to turn this evidence into an answer"
"""The offer, naming the flag — which exists as of E4, and did not until it did.

E1 printed the release's name and no command line, because a `--deep` that parses and then
apologises is the defect `0.20.1` fixed for `vector_tier`: the fix was to refuse the value, not to
keep accepting it. The rule was never *say less*, it was **name only what this build can do**, so
the increment that implements the flag is the increment that prints it.

Never printed alone: `_deep_notice` below always attaches what the run would cost, or why it cannot
say — an offer to spend with no number is the half of this sentence that would be worth doubting.
"""

CALIBRATE_REMEDY = (
    "fit [retrieval.confidence] with `python -m pinakes.calibrate <kb>` — with reranking on, and "
    "with the fitted reranker the one actually in use."
)
"""One sentence covering all three ways confidence comes back `unknown`.

`SearchResult.confidence_reason` already discriminates them (`search.py`'s `confidence_of`) and is
printed on the line above, so the remedy does not branch. Re-checking the three conditions here
would be a second copy of that logic, and a second copy can disagree with the first.
"""

UNPRICEABLE_NOTICE = (
    "what it would cost cannot be computed here — see the reason `pnk doctor` gives for the price "
    "table, and note `--deep` itself refuses rather than guessing"
)
"""What replaces the estimate when the estimator refuses.

**The free path degrades and the paid path refuses, deliberately.** `pnk ask` without `--deep`
spends nothing, so a stale price table or an unpriceable `[deep] model` must not turn a free
retrieval into a failed command; `--deep` inherits the refusal instead, because there the number is
what a reservation is made of (DESIGN §5).
"""


@dataclass(frozen=True, slots=True)
class _Escalation:
    """What answering the question would take — one value, rendered by both surfaces.

    Built once per run so `--json` and the human output cannot describe different work for the same
    result.
    """

    branch: str
    """`synthesis`, `decomposition`, `unknown` or `none` — what a consumer discriminates on, and
    what `deep/estimate.py` prices. `none` is the one it will not price."""

    work: str
    """One sentence: how much work answering would take."""

    notice: str | None
    """The `--deep` offer and its price, or `None` when offering to answer would be beside the
    point.

    Carried rather than decided by the renderer: `if branch != "none"` at the print site would put
    the branch vocabulary in two places, and the one that matters — *do not offer to answer a
    question nothing matched* — would live in neither of them.
    """

    remedy: str | None
    """What the user could do about an `unknown`, or `None` when there is nothing to fix."""

    cost_eur: "Decimal | None"
    """What `--deep` would cost on this branch, worst case, or `None` when it cannot be priced.

    The estimator this reads is E2's, and it is the same call `run_deep` makes before round 0 — so
    the number printed here and the number a reservation is checked against come from one place.
    """


def _estimated_cost(
    manifest: Manifest, *, branch: str, final_k: int, now: str | None = None
) -> "Decimal | None":
    """Price the branch this question falls in, or return `None` rather than fail.

    **The free path must never fail on the price of something it is not buying.** A stale price
    table, an unpriceable `[deep] model` or a context window a huge `final_k` would overflow are all
    real refusals — but they are refusals `--deep` owes, not refusals a free retrieval owes, and
    turning `pnk ask` into a failed command over the cost of a run nobody asked for would be the
    strictness in exactly the wrong place. `run_deep` re-runs the same estimate and lets every one
    of them through.
    """
    from datetime import UTC, datetime

    from pinakes.budget.estimate import TIMESTAMP_FORMAT
    from pinakes.budget.prices import load_prices
    from pinakes.deep.estimate import BRANCHES, estimate_operation

    if branch not in BRANCHES:
        return None
    try:
        return estimate_operation(
            branch=branch,
            max_rounds=manifest.deep.max_rounds,
            final_k=final_k,
            chunk_max_tokens=manifest.chunking.max_tokens,
            model=manifest.deep.model,
            prices=load_prices(),
            now=now or datetime.now(UTC).strftime(TIMESTAMP_FORMAT),
            max_price_age_days=manifest.budget.max_price_age_days,
        ).total_eur
    except PinakesError:
        return None


def _deep_notice(cost_eur: "Decimal | None") -> str:
    """The offer, always carrying its price or the reason there is none."""
    if cost_eur is None:
        return f"{DEEP_OFFER}; {UNPRICEABLE_NOTICE}."
    from pinakes.budget.reserve import display_eur

    return (
        f"{DEEP_OFFER}, estimated at €{display_eur(cost_eur)} worst case — every call is "
        "reconciled to what it actually cost, which `pnk budget` shows."
    )


def _escalation(result: "SearchResult", *, manifest: Manifest, final_k: int) -> _Escalation:
    """Size the work from the confidence signal — never authorise it, and never spend (D-28).

    The branches are the ones §5 of the deep-release plan names: a confident retrieval needs one
    synthesis call, a low-confidence one needs decomposition and repeated search, and an
    uncalibrated KB cannot tell which — it is bounded by the caps rather than by the signal (D-22).

    **Anything that is not `high`, `medium` or `low` falls through to `unknown`**, which is the safe
    direction: a value this function has never heard of is precisely one it cannot size.
    """
    from pinakes.deep.estimate import DECOMPOSITION, SYNTHESIS, UNKNOWN
    from pinakes.search import HIGH, LOW, MEDIUM

    if not result.passages:
        # Not an `unknown`: nothing matched, so no amount of reasoning has anything to reason
        # over. Telling this user to calibrate would answer a question they did not ask, and
        # offering paid synthesis would offer to reason over nothing — which is also why
        # `estimate_operation` refuses to price this branch at all.
        return _Escalation(
            "none", "nothing matched, so there is nothing to answer from.", None, None, None
        )

    # The estimator's own constants, never four string literals here: `run_deep` is handed this
    # value and prices it, so a spelling that differed would be a branch nothing could price.
    remedy: str | None = None
    if result.confidence in (HIGH, MEDIUM):
        branch = SYNTHESIS
        work = "answering this would take one synthesis call over the passages above."
    elif result.confidence == LOW:
        branch = DECOMPOSITION
        work = (
            "answering this would take decomposition into subquestions, a search for each, and a "
            "synthesis over what they return — several calls."
        )
    else:
        branch = UNKNOWN
        work = (
            "how much answering this would take cannot be told from here: with no calibrated "
            "signal, a run ends at its caps rather than at sufficiency."
        )
        remedy = CALIBRATE_REMEDY

    cost_eur = _estimated_cost(manifest, branch=branch, final_k=final_k)
    return _Escalation(branch, work, _deep_notice(cost_eur), remedy, cost_eur)


def run_ask(args: argparse.Namespace) -> int:
    """`pnk ask`. The question surface — and, with `--deep`, the one paid answer Pinakes gives.

    **Without `--deep` it never synthesises an answer and it never spends.** What it adds over
    `pnk search` is the third thing: `search` answers *what is in the KB about this*, `ask` answers
    *what it would take to answer this*, and now *what that would cost* (D-21). The escalation block
    prints on **every** confidence value, not only below the threshold, because the branch — and so
    the price — differs by confidence (D-28).

    **With `--deep` the free retrieval still runs first, and always.** It is round 0: its passages
    are the cheap branch's whole evidence, and its confidence is what decides which branch runs.
    Nothing about the paid path replaces it, which is why the same output appears above the answer.
    """
    import json as json_module

    with _retrieval(args) as pipeline:
        result = pipeline.search(args.query)
        escalation = _escalation(result, manifest=pipeline.manifest, final_k=pipeline.final_k)
        # Inside the block: the loop retrieves once per subproblem, through this same open index.
        run = _run_deep(args, pipeline, result, escalation) if args.deep else None
    deep = run.answer if run is not None else None

    if args.json:
        payload = _retrieval_payload(result)
        # `answer` is a key in every form of this command — `null` when nothing was paid for, an
        # object when a run produced one — so a consumer parses one schema either way (E1).
        payload["answer"] = _answer_payload(deep) if deep is not None else None
        # `transcript` is the same shape of promise: always present, `null` when nothing was paid
        # for. Relative to the KB root, never absolute — a transcript is KB-local (D-26), and
        # printing where *this machine* keeps the KB would put a fact about the machine into a
        # script's input.
        payload["transcript"] = run.relative_transcript if run is not None else None
        # And so is `suggestions` — `null` without a paid run, an object with one. It carries the
        # rendered fragment beside the parsed entries so a script pastes the same bytes a human
        # was shown, from one renderer rather than two that are free to drift.
        payload["suggestions"] = _suggestions_payload(run.suggestions) if run is not None else None
        payload["escalation"] = {
            "branch": escalation.branch,
            "work": escalation.work,
            "cost_eur": _money(escalation.cost_eur),
            "remedy": escalation.remedy,
        }
        print(json_module.dumps(payload, indent=2))
        # The same exit code as the human surface: a paid run that produced no answer is not a
        # success, and `--json` is the surface a script actually reads that from.
        return EXIT_OK if deep is None or deep.answered else EXIT_FAILURE

    if result.passages:
        _print_passages(result)
    else:
        print("no passages matched.")

    print(f"confidence: {result.confidence} — {result.confidence_reason}")
    if run is not None:
        _print_answer(run.answer, run.relative_transcript)
        _print_suggestions(run.suggestions)
        return EXIT_OK if run.answer.answered else EXIT_FAILURE

    print(NO_ANSWER_SYNTHESISED)
    print(escalation.work)
    for line in (escalation.notice, escalation.remedy):
        if line is not None:
            print(line)
    return EXIT_OK


@dataclass(frozen=True, slots=True)
class _DeepRun:
    """One paid run and the file it left behind — what `run_ask` needs after the index is closed.

    A pair rather than two returns, because the transcript's whole point is that it is *this* run's:
    handing the answer and the path back separately is how a later edit prints one run's cost beside
    another run's path.
    """

    answer: "DeepAnswer"
    relative_transcript: str
    """Where the transcript landed, relative to the KB root — the form both surfaces print.

    A POSIX string, computed once: the citations above it are printed KB-relative too, so a reader
    already reads paths that way, and `--json` must not carry a separator that depends on which
    machine ran the command. It is inside `.pinakes/` by construction (E5), so it never escapes."""

    suggestions: tuple["Suggestion", ...]
    """The links this run's own citations propose (E7) — printed, never written.

    Computed here rather than at print time because it needs the manifest and the sidecars on
    disk, and `run_ask` has closed the index by then. Empty is the ordinary case: an answer citing
    one document per block observes no pair.
    """


def _run_deep(
    args: argparse.Namespace,
    pipeline: _Retrieval,
    result: "SearchResult",
    escalation: _Escalation,
) -> _DeepRun:
    """Build one operation's accountant, run the loop (E4), and record what it did (E5).

    **Imported here and nowhere higher.** `pinakes.deep.client` is one of the two modules in this
    package permitted to construct a vendor client, and `tests/test_paid_path.py` runs the whole
    free path in a fresh subprocess asserting it never reaches `sys.modules`. A module-scope import
    would put it there for every `pnk search`, `pnk sync` and `pnk serve` in the process.

    `operation="ask"` needs no ledger change: `operation` is already a free-form string whose own
    docstring names this value (M9).

    **The transcript is written here, after `run_deep` returns, and only then.** The loop reads no
    clock and opens no file by design, so the I/O belongs to the caller — and a run that never
    returns an answer never writes one: a budget refusal, a declined confirmation and an
    `on_exceed = "abort"` halt all raise past this line. That is deliberate for the last of the
    three, whose meaning is that the rounds already paid for are discarded (D-23); their spend is
    in the ledger either way.
    """
    from datetime import UTC, datetime

    from pinakes.budget.accountant import Accountant
    from pinakes.budget.estimate import TIMESTAMP_FORMAT
    from pinakes.budget.prices import load_prices
    from pinakes.deep import suggest as suggest_module
    from pinakes.deep import transcript as transcript_module
    from pinakes.deep.client import PROMPT_VERSION, SCHEMA_VERSION, default_transport
    from pinakes.deep.loop import NothingToAnswerError, run_deep

    if escalation.branch == "none":
        raise NothingToAnswerError

    accountant = Accountant(
        pipeline.manifest,
        prices=load_prices(),
        operation="ask",
        # The terminal facts belong to the caller, as they do for `pnk sync`: nothing below this
        # line probes for a tty, it is told whether one is attached.
        interactive=sys.stdin.isatty(),
        ask=input,
        yes=args.yes,
    )
    now = datetime.now(UTC).strftime(TIMESTAMP_FORMAT)
    answer = run_deep(
        question=args.query,
        round0=result,
        branch=escalation.branch,
        final_k=pipeline.final_k,
        retrieve=pipeline.search,
        sufficiency=pipeline.confidence,
        # Unbuilt: `run_deep` calls it after the caps have admitted the run, so a KB whose
        # `[budget]` refuses says so instead of demanding an API key first.
        open_transport=default_transport,
        accountant=accountant,
        now=now,
    )
    written = transcript_module.write(
        pipeline.manifest.state_dir,
        transcript_module.record(
            deep=answer,
            operation_id=accountant.operation_id,
            question=args.query,
            filters=_filters_payload(args),
            final_k=pipeline.final_k,
            # Round 0's own reading, because it is *why* this run cost what it did: D-28 gives the
            # branch to the free signal, so `high` bought one call and `unknown` bought a loop.
            confidence=result.confidence,
            confidence_reason=result.confidence_reason,
            # The model the estimate priced and the calls used — not a second read of the manifest,
            # which is how a transcript comes to name a model the run did not pay for.
            model=answer.estimate.model,
            prompt_version=PROMPT_VERSION,
            response_schema_version=SCHEMA_VERSION,
            pinakes_version=__version__,
            now=now,
        ),
    )
    return _DeepRun(
        answer=answer,
        relative_transcript=written.relative_to(pipeline.manifest.root).as_posix(),
        # After the transcript, deliberately: the record of what was paid for is on disk before
        # anything derived from it is computed.
        suggestions=suggest_module.for_run(answer, manifest=pipeline.manifest),
    )


def _filters_payload(args: argparse.Namespace) -> dict[str, object]:
    """The filters a run was narrowed by, as the user typed them (D-27).

    The typed form rather than the resolved `Filters`, on purpose: `--modified-after 20260101`
    resolves to an epoch float, and a transcript recording that would say what the code did instead
    of what the user asked — the one of the two a reader can re-run.
    """
    return {
        "tags": list(args.tag),
        "path_prefix": args.path_prefix,
        "source_type": args.source_type,
        "modified_after": args.modified_after,
        "modified_before": args.modified_before,
    }


def _money(amount: "Decimal | None") -> str | None:
    """Cents, as a string. `null` stays `null`.

    A string because JSON has no decimal type and a float would reintroduce exactly the
    representation error `Decimal` is used to avoid (INVARIANTS). Two places, because that is what
    the ledger stores and what `pnk budget` reports — a machine consumer reconciling the two should
    not have to notice one of them was rendered at a different precision. Through
    `budget.reserve.display_eur` for the same reason: every euro Pinakes prints rounds the one way.
    """
    from pinakes.budget.reserve import display_eur

    return None if amount is None else display_eur(amount)


def _answer_payload(deep: "DeepAnswer") -> dict[str, object]:
    """`--json`'s `answer` object: the prose, the blocks it came in, and what it cost.

    **The same renderer the transcript stores** (`deep/transcript.py`), so the object a script
    parsed off stdout and the object it reads back off disk are the same object rather than two
    shapes free to drift — and the drift would be silent, since both would still be valid JSON.
    """
    from pinakes.deep.transcript import answer_payload

    return answer_payload(deep)


def _suggestions_payload(suggestions: "tuple[Suggestion, ...]") -> dict[str, object]:
    """`--json`'s `suggestions` object (E7): the fragment, and its entries parsed out.

    **Not folded into `answer`**, which is the object the transcript stores: a suggestion is
    resolved against the sidecars on disk *now*, not against what the run was answered from, and
    putting it inside the record of what was paid for would date the record to whichever of the two
    was read last.
    """
    from pinakes.deep.suggest import render

    return {
        "fragment": render(suggestions),
        "links": [
            {
                "sidecar": item.sidecar,
                "source": item.source,
                "target": item.target,
                "to": str(item.to),
                "rel": item.rel,
                "rounds": list(item.rounds),
            }
            for item in suggestions
        ],
    }


NO_ANSWER_FROM_A_PAID_RUN = (
    "the run was paid for and produced no answer — the label above says what stopped it."
)
"""Printed when a `--deep` run made calls and came back with nothing to show.

**Reachable, and it exits non-zero.** A round can decompose into subproblems that match nothing, or
into nothing at all; both stop the loop before any answering call. The run is not a *failure* in the
sense an exception is — the calls were made, reconciled and are in the ledger — but a command that
asked a question and produced no answer must not report success to a script. `NO_ANSWER_SYNTHESISED`
is the free path's line and says something different: *nothing was even attempted*.
"""


TRANSCRIPT_PREFIX = "what was asked and what came back is kept in "
"""The line naming the file the run wrote (E5).

A constant because `tests/test_docs_quote_the_shipped_sentences.py` reads it: a sentence a
documented command prints is one the documentation may quote, and the gate compares the two."""


ANSWER_SYNTHESISED = "answer — synthesised from the evidence above, and cited back into it:"
"""The `--deep` counterpart to `NO_ANSWER_SYNTHESISED`, and the reason both exist.

Whichever way the run went, the output has to say what the prose below it *is*. The free path's
line stops a reader mistaking evidence for a conclusion; this one stops the opposite mistake —
reading a synthesised paragraph as if it were quoted from a document. The citations under it are
what make the difference checkable.
"""


def _print_answer(deep: "DeepAnswer", transcript: str) -> None:
    """The paid run's own output, under the free evidence that produced it.

    **The answer first, then how the run ended.** The label is provenance — which bound stopped it,
    whether the signal was calibrated — and a reader who came for an answer should not have to read
    past a sentence about round caps to reach one. It sits with the cost, where the rest of what
    this run *was* lives.

    **The transcript is named because it was written, not as a courtesy.** It holds the question and
    the model's prose about this KB's documents, and a file appearing under `.pinakes/` with that in
    it is something the person who caused it should be told about once — beside the cost, which is
    the other thing this run left behind.
    """
    from pinakes.budget.reserve import display_eur

    if deep.answered:
        print(f"\n{ANSWER_SYNTHESISED}")
    for block in deep.blocks:
        print()
        for asked in block.asked:
            print(f"round {block.round_number} asked: {asked}")
        print(block.text)
        for citation in block.citations:
            print(f"  [{citation.number}] {citation.locator}")
    if not deep.answered:
        print(f"\n{NO_ANSWER_FROM_A_PAID_RUN}")
    print(f"\n{deep.label}")
    print(
        f"{deep.tally.calls} paid call(s), €{display_eur(deep.spent_eur)} spent against an "
        f"estimated €{display_eur(deep.estimate.total_eur)} worst case. `pnk budget` has the "
        "record."
    )
    print(f"{TRANSCRIPT_PREFIX}{transcript}")


def _print_suggestions(suggestions: "tuple[Suggestion, ...]") -> None:
    """The sidecar fragment a run's own citations propose (E7), or nothing at all.

    **Nothing at all is the common case and prints nothing** — no header, no empty section. A
    question answered from one document per block observes no pair, and a line saying so on every
    such run would be noise under an answer that is already long.
    """
    from pinakes.deep.suggest import render

    fragment = render(suggestions)
    if fragment:
        print(f"\n{fragment}")


def _doctor_arguments(parser: argparse.ArgumentParser) -> None:
    _kb_argument(parser)
    parser.add_argument(
        "--prune",
        action="store_true",
        help="delete orphaned sidecars, after printing every path",
    )


def run_doctor(args: argparse.Namespace) -> int:
    """`pnk doctor`. Exit 1 on any FAIL; warnings are reported but do not fail the command."""
    from pinakes import manifest as manifest_module
    from pinakes.doctor import Status, diagnose, prune

    loaded = manifest_module.discover(args.kb)
    report = diagnose(loaded)
    for check in report.checks:
        print(check.line())

    if args.prune:
        if not report.orphans:
            print("\nnothing to prune.")
        else:
            print("\nremoving these orphaned sidecars:")
            for path in report.orphans:
                print(f"  {path.relative_to(loaded.root)}")
            removed = prune(report.orphans)
            print(f"removed {len(removed)}.")

    return EXIT_FAILURE if report.worst is Status.FAIL else EXIT_OK


def _upgrade_arguments(parser: argparse.ArgumentParser) -> None:
    _kb_argument(parser)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the hunks that apply cleanly — [budget] included — after printing them; "
        "refuses entirely if any hunk conflicts, and backs the manifest up first",
    )


def run_upgrade(args: argparse.Namespace) -> int:
    """`pnk upgrade`. Prints what the template changed and how it fits; `--apply` also writes it.

    **The exit codes, and the third is the one worth knowing about.** `0` says the comparison was
    made and reported — including, without `--apply`, a report whose every hunk conflicts, because
    a report writes nothing and so has nothing to fail at. `3` says the comparison could not be made
    at all: the version a KB records is not one whose content this build ships, which is true of
    every KB created before the archive existed. **`--apply` changes neither of them**; what it adds
    is `1` for a refusal, which is what `1` already means everywhere else — *something is wrong and
    it is yours to fix*. A conflict is exactly that once a write was asked for, and is not that in
    a report, which is why the same finding carries two codes under the two invocations.

    **The report is printed before anything is written, and the spending-cap heading is part of
    it.** That is the consent path D-10 rests on. It is a property of the order of this function,
    which is why a test asserts it by line position rather than by reading the code.
    """
    import json as json_module

    from pinakes import manifest as manifest_module
    from pinakes.errors import UpgradeError
    from pinakes.upgrade import APPLIABLE, Outcome, applied_lines, apply, as_json, lines, plan

    loaded = manifest_module.discover(args.kb)
    report = plan(loaded)
    # `APPLIABLE`, not `is DRIFTED`: the `same manifest` outcome has no hunks and still has a
    # reference to record (D-16). The set lives beside `Outcome` so this predicate and `apply`'s
    # own guard cannot disagree about which outcomes are writable — two copies of that rule is how
    # the CLI ends up calling a function that then refuses.
    applying = args.apply and report.outcome in APPLIABLE

    if not args.json:
        for line in lines(report, applying=applying):
            print(line)

    if not applying:
        if args.json:
            # JSON on every path, the refusal included: a caller promised machine-readable output
            # and handed a traceback instead has been given the worst of both.
            print(json_module.dumps(as_json(report), indent=2))
        return EXIT_NO_BASELINE if report.outcome is Outcome.NO_BASELINE else EXIT_OK

    # `--json --apply` emits **one** document, after the attempt, and emits it whether the attempt
    # wrote or refused: two JSON documents on one stdout is not JSON, and a consumer that asked for
    # machine-readable output should not have to parse a message off stderr to learn what happened.
    # Nothing is lost by printing late — the ordering the consent path needs is a property of the
    # human output, where a person is the one deciding.
    try:
        result = apply(loaded, report)
    except UpgradeError as exc:
        if not args.json:
            raise
        print(json_module.dumps(as_json(report, refused=exc), indent=2))
        return EXIT_FAILURE

    if args.json:
        print(json_module.dumps(as_json(report, applied=result), indent=2))
    else:
        for line in applied_lines(result):
            print(line)
    return EXIT_OK


def _install_hooks_arguments(parser: argparse.ArgumentParser) -> None:
    _kb_argument(parser)


def run_install_hooks(args: argparse.Namespace) -> int:
    """`pnk install-hooks`. Exits 1 if any existing hook was left alone rather than clobbered."""
    from pinakes import manifest as manifest_module
    from pinakes.hooks import FREE_BACKEND_NOTICE, install, suggestion

    loaded = manifest_module.discover(args.kb)
    written, refused = install(loaded.root)

    for status in written:
        print(f"installed {status.name}")
    if written:
        print(f"each hook {FREE_BACKEND_NOTICE}")
    for status in refused:
        print(f"\nleft {status.path} alone — it is not ours, and editing it is not our call.")
        print("To wire pinakes in yourself, add this line:")
        print(f"    {suggestion(status.name)}")

    return EXIT_FAILURE if refused else EXIT_OK


def _budget_arguments(parser: argparse.ArgumentParser) -> None:
    _kb_argument(parser)
    parser.add_argument(
        "--resolve",
        default=None,
        metavar="CALL_ID",
        help="close an `unknown outcome` call by appending a reconciliation (needs --actual)",
    )
    parser.add_argument(
        "--actual",
        default=None,
        metavar="EUR",
        help="with --resolve: what the call actually cost, in euros, from the vendor's dashboard",
    )


def run_budget(args: argparse.Namespace) -> int:
    """`pnk budget`. Reads the ledger; `--resolve` appends to it and never edits it.

    Money arrives from the command line as a string and is parsed with `Decimal(text)` directly —
    never through `float` — for the reason docs/INVARIANTS.md states: `Decimal(0.05)` is not
    `Decimal("0.05")`, and a ledger written from the first carries an imprecision nobody can
    explain later.
    """
    from datetime import UTC, datetime
    from decimal import Decimal, InvalidOperation
    from zoneinfo import ZoneInfo

    from pinakes import manifest as manifest_module
    from pinakes.budget import ledger as ledger_module
    from pinakes.budget.accountant import caps_of
    from pinakes.budget.summary import euros, render, summarise

    loaded = manifest_module.discover(args.kb)
    path = ledger_module.ledger_path(loaded.state_dir)

    if args.resolve is not None:
        if args.actual is None:
            raise PinakesError(
                "--resolve needs --actual.",
                remedy="`pnk budget --resolve <call_id> --actual <eur>`, from the vendor's usage "
                "dashboard. Guessing would defeat the point of resolving it.",
            )
        try:
            actual = Decimal(args.actual)
        except InvalidOperation as exc:
            raise PinakesError(
                f"--actual {args.actual!r} is not a number.",
                remedy="Use a plain decimal in euros, for example 0.043.",
            ) from exc
        record = ledger_module.resolve_unknown(path, call_id=args.resolve, actual_eur=actual)
        print(f"resolved {record.call_id} at €{euros(record.cost_eur)} (appended, nothing edited).")
        return EXIT_OK
    if args.actual is not None:
        raise PinakesError(
            "--actual only means something with --resolve.",
            remedy="`pnk budget --resolve <call_id> --actual <eur>`.",
        )

    summary = summarise(
        path,
        kb_name=loaded.kb.name,
        kb_id=loaded.kb.id,
        caps=caps_of(loaded.budget),
        timezone=ZoneInfo(loaded.budget.timezone),
        now=datetime.now(UTC),
    )
    for line in render(summary):
        print(line)
    print(
        "\n`monthly_eur` is per KB: ten paid KBs have ten monthly allowances. "
        "There is no global cap in this release."
    )
    return EXIT_OK


def _serve_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "kb_paths",
        nargs="*",
        type=Path,
        metavar="KB",
        help="KB directories to serve (default: the nearest one)",
    )
    parser.add_argument("--offline", action="store_true", help="never reach out for model weights")


def run_serve(args: argparse.Namespace) -> int:
    """`pnk serve`. Serves only the KBs named here — no tool argument accepts a path (§4.7)."""
    from pinakes import manifest as manifest_module
    from pinakes.serve import build

    roots = list(args.kb_paths) or [manifest_module.find_kb_root()]
    mcp, server = build(roots, offline=args.offline)
    try:
        mcp.run()
    finally:
        server.close()
    return EXIT_OK


def _sync_arguments(parser: argparse.ArgumentParser) -> None:
    _kb_argument(parser)
    parser.add_argument(
        "--rebuild", action="store_true", help="rebuild the index from scratch (keeps the ledger)"
    )
    parser.add_argument(
        "--sidecars-only",
        action="store_true",
        help="only mint missing sidecars; never touch the index (the pre-commit half)",
    )
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="only update the index; never write into docs/ (the post-commit half)",
    )
    parser.add_argument(
        "--stage",
        action="store_true",
        help="with --sidecars-only: limit to staged files, and git add them",
    )
    parser.add_argument("--offline", action="store_true", help="never reach out for model weights")
    parser.add_argument(
        "--scan-links",
        action="store_true",
        help="re-read every linked KB's sidecars now, ignoring the freshness window",
    )
    parser.add_argument(
        "--force-unlock", action="store_true", help="take a lock held by another machine"
    )
    parser.add_argument(
        "--extract",
        default=None,
        metavar="BACKEND",
        help="override `[extraction] backend` for this run only",
    )
    parser.add_argument(
        "--estimate-only",
        action="store_true",
        # No markdown here: `--help` renders in a terminal, and `**bold**` reaches the user as
        # literal asterisks. The emphasis belongs in CLI.md, which is rendered.
        help=(
            "price the first slice against the real tokeniser and exit without extracting. "
            "This is a NETWORK CALL and needs a key; it generates nothing and bills no output"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        # The scope, stated in full, because a flag whose reach nobody wrote down grows one.
        help=(
            "overrule exactly two refusals: paying to extract a PDF whose free text layer is "
            "already healthy, and — only together with an explicit free --extract — overwriting "
            "a paid extraction (prints what it drops). It never widens a budget cap, the "
            "stale-price refusal, the missing-floor refusal, or the no-terminal abort"
        ),
    )
    # `all` rather than `free` as the bare form's value: both spellings clear the *whole* extraction
    # cache, so a value named `free` would read as "clear only the free entries", which is not what
    # either does. Between those two the value names what you are authorising, not what is removed.
    #
    # `transcripts` is the one value that names a *store* instead (E5), and it has to: layering it
    # as a third authorisation over the same store would mean `--clear-cache=transcripts` also
    # emptying the extraction cache — destroying more than the flag names. So it clears
    # `.pinakes/deep/` and nothing else, and neither other spelling touches it.
    parser.add_argument(
        "--clear-cache",
        nargs="?",
        const="all",
        default=None,
        choices=("all", "paid", "transcripts"),
        metavar="paid|transcripts",
        help=(
            "empty the extraction cache, after confirming (never the ledger); "
            "=paid also authorises destroying entries a paid backend wrote; "
            "=transcripts instead empties the deep-run records under .pinakes/deep/"
        ),
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help=(
            "answer this run's confirmation prompts (cron use). Raises no cap, and does not "
            "authorise clearing paid cache entries — that needs --clear-cache=paid as well"
        ),
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="print only problems")


def print_sync_report(report: "SyncReport", *, quiet: bool) -> None:
    """Render one sync's outcome. Split out of `run_sync` so `-q`'s own rules are testable without
    driving the whole command — the quiet path is the one the recommended git hooks actually take,
    and it had no test at all."""
    if not quiet:
        for line in report.lines():
            print(line)
        return
    # `-q` prints only problems — and a file skipped for want of a glob is one. The hooks
    # `docs/GUIDE.md` recommends run `pnk sync --quiet`, so dropping it here would leave the
    # project's own documented workflow as the single place this never reaches.
    if report.unmatched:
        print(report.unmatched_line(), file=sys.stderr)
    for line in report.escape_lines():
        print(line, file=sys.stderr)
    for line in report.failure_lines():
        print(line, file=sys.stderr)


def _progress_printer() -> tuple[Callable[[int, int], None], Callable[[], None]]:
    """A `SyncOptions.progress` callback for a real terminal: `done/total` and a rate, on one line
    it overwrites in place — not a spinner, because the number is what tells slow from stuck on a
    multi-hour, CPU-only sync. Throttled to roughly once a second so a fast run (or a small KB)
    does not spend more time printing than syncing.

    Returns `(progress, finish)`. `progress` ends the line with a newline exactly when `done ==
    total` — the ordinary case — but a `[budget]` cap or an unhandled failure can stop `_run`'s
    loop before `total` is reached, leaving the cursor mid-line with no newline printed. `finish`
    closes that line if `progress` left it open; the caller runs it unconditionally after `sync()`
    returns *or raises*, before anything else reaches stdout, so a report or an error message never
    lands glued onto the tail of a progress line.
    """
    import time

    start = time.monotonic()
    last_shown: float | None = None
    dirty = False  # a line is open (no trailing newline printed for it yet)

    def progress(done: int, total: int) -> None:
        nonlocal last_shown, dirty
        now = time.monotonic()
        finished = done >= total
        if not finished and last_shown is not None and now - last_shown < 1.0:
            return
        last_shown = now
        elapsed = now - start
        rate = (done / elapsed * 60) if elapsed > 0 else 0.0
        line = f"\rsyncing: {done}/{total} documents ({rate:.1f}/min)"
        print(line, end="\n" if finished else "", flush=True)
        dirty = not finished

    def finish() -> None:
        nonlocal dirty
        if dirty:
            print()
            dirty = False

    return progress, finish


def run_sync(args: argparse.Namespace) -> int:
    """`pnk sync`. Exit 0 on success (including a busy lock), 1 if any document failed."""
    from pinakes import manifest as manifest_module
    from pinakes.sync import SyncOptions, sync

    loaded = manifest_module.discover(args.kb)

    if args.clear_cache is not None:
        return _run_clear_cache(loaded, args)

    def _no_finish() -> None:
        pass

    # `-q` prints only problems (see `print_sync_report`), and a hook can inherit a real tty while
    # still asking for quiet — so both gates apply, not just the tty check.
    progress: Callable[[int, int], None] | None = None
    finish_progress: Callable[[], None] = _no_finish
    if sys.stdout.isatty() and not args.quiet:
        progress, finish_progress = _progress_printer()

    try:
        report = sync(
            loaded,
            options=SyncOptions(
                rebuild=args.rebuild,
                sidecars_only=args.sidecars_only,
                scan_links=args.scan_links,
                index_only=args.index_only,
                stage=args.stage,
                offline=args.offline,
                force_unlock=args.force_unlock,
                extract=args.extract,
                force=args.force,
                estimate_only=args.estimate_only,
                yes=args.yes,
                # The terminal facts belong to the caller: `sync()` does no I/O beyond the
                # filesystem, so it is told whether one is attached rather than probing for it.
                interactive=sys.stdin.isatty(),
                ask=input,
                progress=progress,
            ),
        )
    finally:
        # Unconditional, and before anything else reaches stdout: a `[budget]` cap or an unhandled
        # failure can stop `_run`'s loop before `progress`'s own `done == total` ever fires, which
        # leaves the line open (a trailing `\r`, no newline) for whatever prints next to land on.
        finish_progress()

    if report.estimates:
        print("estimate only — nothing was extracted, and no output tokens were billed:")
        for path, pages, requests, tokens, eur in report.estimates:
            print(
                f"  {path}: {pages} page(s), {requests} request(s), {tokens:,} input tokens →€{eur}"
            )
        return EXIT_OK
    if args.estimate_only:
        print("estimate only: no PDF in this KB would be extracted by the configured backend.")
        return EXIT_OK

    if report.busy:
        if not args.quiet:
            print("another sync is already running; nothing to do.")
        return EXIT_OK

    if report.reclaimed_lock:
        print(
            "took over a stale sync lock left by a process that is no longer running.",
            file=sys.stderr,
        )
    print_sync_report(report, quiet=args.quiet)

    return EXIT_OK if report.ok else EXIT_FAILURE


def _run_clear_cache(loaded: Manifest, args: argparse.Namespace) -> int:
    """`sync()` never prompts (it does no I/O beyond the filesystem, like every other function in
    that module) — this is the one place that reads a TTY and asks, then re-calls with `yes=True`
    once confirmed.

    Two authorisations (I6b). `--yes` answers the entry-count prompt. Entries a paid backend wrote
    need a second, explicit one: either `--clear-cache=paid`, or an interactive `y` to a prompt
    that names the paid count. What is forbidden is the unattended case — `--yes` alone, no
    terminal, paid entries present — because that is the line a cron job or a hook could carry.

    **`=transcripts` targets the other store and needs one authorisation, not two** (E5): the value
    itself is already the explicit mention that `=paid` exists to force, and no bare form of this
    flag reaches `.pinakes/deep/` at all.
    """
    from pinakes.sync import CLEAR_TRANSCRIPTS, SyncOptions, sync

    transcripts = args.clear_cache == CLEAR_TRANSCRIPTS
    paid_authorised = args.clear_cache == "paid"
    report = sync(
        loaded,
        options=SyncOptions(
            clear_cache=True,
            clear_cache_paid=paid_authorised,
            clear_cache_transcripts=transcripts,
            yes=args.yes,
        ),
    )
    if report.busy:
        print("another sync is already running; nothing to do.")
        return EXIT_OK

    # Two nouns rather than one: the prompt has always said "cache entries" and the outcome line
    # "entries", and E5 changes neither — a sentence a user's eye knows is not worth tidying.
    noun = "transcripts" if transcripts else "entries"
    pending_noun = "transcripts" if transcripts else "cache entries"
    if report.cache_clear_aborted:
        print(
            f"this will remove {report.cache_pending_entries} {pending_noun} "
            f"({report.cache_pending_bytes} bytes)."
        )
        paid = report.cache_pending_paid_entries
        if transcripts:
            # A different sentence from the cache's, because the loss is a different kind. An
            # extraction can be bought again; the record of what a particular run was asked and
            # what it answered cannot — paying again buys a *new* run, not this one back.
            #
            # **The count leads and the euros follow**, deliberately. The count is a fact about the
            # files in front of it; the euro figure is a join against the ledger, and a join that
            # resolves nothing — a deleted `ledger.jsonl`, ids closed by nothing — returns 0.0000.
            # Led with, that reads as *these cost nothing*, which is the opposite of the warning,
            # at the one moment it has to land.
            print(
                f"they are the record of {paid} paid run(s), €{report.cache_pending_paid_eur} in "
                "the ledger. Nothing re-creates them — the ledger keeps the spend, but what was "
                "asked is only here."
            )
        elif paid:
            print(
                f"{paid} of them were written by a paid backend and cost "
                f"€{report.cache_pending_paid_eur} — re-creating them means paying again."
            )
        if not sys.stdin.isatty():
            if transcripts:
                flags = "--yes --clear-cache=transcripts"
            else:
                flags = "--yes --clear-cache=paid" if paid else "--yes"
            print(f"no terminal to confirm from; re-run with {flags}.", file=sys.stderr)
            return EXIT_FAILURE
        answer = input("proceed? [y/N] ").strip().lower()
        if answer != "y":
            print("aborted; nothing removed.")
            return EXIT_OK
        report = sync(
            loaded,
            options=SyncOptions(
                clear_cache=True,
                # Re-called with the *same target* the prompt described. `_clear_cache` branches on
                # the target first, so `clear_cache_paid` is already dead on a transcripts run —
                # this passes `False` anyway rather than relying on that: an authorisation nobody
                # was asked for should not sit in the options waiting for a branch order to change.
                clear_cache_paid=not transcripts,
                clear_cache_transcripts=transcripts,
                yes=True,
            ),
        )

    print(f"removed {report.cache_cleared} {noun} ({report.cache_cleared_bytes} bytes).")
    return EXIT_OK


def _link_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "source", help="the document the link is written in, relative to the KB root"
    )
    parser.add_argument(
        "target",
        help="pnk://<kb>/<doc> (self accepted), <alias>:<path> in a linked KB, or a path here",
    )
    _kb_argument(parser)
    parser.add_argument(
        "--rel", required=True, metavar="REL", help="the relation, for example cites or supersedes"
    )


def run_link(args: argparse.Namespace) -> int:
    """`pnk link`. Writes one entry into the source document's own sidecar, and nothing else."""
    from pinakes import manifest as manifest_module
    from pinakes.link import add

    loaded = manifest_module.discover(args.kb)
    outcome = add(loaded, source=args.source, target=args.target, rel=args.rel)
    where = outcome.sidecar.relative_to(loaded.root)

    if not outcome.written:
        print(f"{where} already carries {outcome.rel} -> {outcome.target}; nothing written.")
        return EXIT_OK
    print(f"{where}: {outcome.rel} -> {outcome.target}")
    print("`pnk sync` to index it, then commit the sidecar.")
    return EXIT_OK


# The v0.1 surface (docs/DESIGN.md §8), in the order a user meets it. `increment` points at
# plans/20260725_1317-v0.1.md, so an unimplemented command tells the user exactly when it arrives.
def _links_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("document", help="a document ULID, or its path within the KB")
    _kb_argument(parser)
    parser.add_argument("--rel", default=None, help="only links with this relation")
    parser.add_argument(
        "--direction",
        default="both",
        choices=("out", "in", "both"),
        help="links written here (out), links pointing here (in), or both",
    )
    parser.add_argument(
        "--depth", type=int, default=1, help="how many hops to follow (server-capped at 3)"
    )
    parser.add_argument(
        "--query", default=None, help="rank neighbours by similarity to this instead of by edge"
    )
    parser.add_argument("--offline", action="store_true", help="never reach out for model weights")
    parser.add_argument("--json", action="store_true", help="machine-readable output")


def run_links(args: argparse.Namespace) -> int:
    """`pnk links`. What this document connects to, and what connects to it."""
    import json as json_module

    from pinakes import manifest as manifest_module
    from pinakes import store
    from pinakes.errors import PinakesError
    from pinakes.graph import present
    from pinakes.graph import provider as provider_module
    from pinakes.graph.traverse import traverse

    loaded = manifest_module.discover(args.kb)
    connection = store.connect_ro(loaded.index_path)
    try:
        start_doc = provider_module.resolve_document(connection, args.document)
        if start_doc is None:
            raise PinakesError(
                f"no active document in this KB matches {args.document!r}.",
                remedy="Pass a document ULID, or its path as `pnk search` prints it.",
            )

        # Constructed first, so an unknown `--direction` is refused before a model is loaded.
        provider = provider_module.DocumentProvider(
            connection, local_kb=loaded.kb.id, direction=args.direction, rel=args.rel
        )
        scores: dict[str, float] = {}
        if args.query is not None:
            # Loaded only when a query was given: ranking by edge needs no model at all, and
            # `pnk links` should not pull weights for the common case.
            from pinakes.embed import load_backend

            scores = provider_module.score_documents(
                connection,
                load_backend(loaded.embedding, offline=args.offline),
                args.query,
                dim=loaded.embedding.dim,
            )

        provider.scores = scores
        result = traverse(
            provider,
            provider_module.document_key(str(loaded.kb.id), str(start_doc)),
            depth=args.depth,
            adjacent_k=loaded.retrieval.adjacent_k,
            query=args.query,
        )
        body = present.payload(result, provider=provider, document=str(start_doc))
        rows = body["neighbours"]
    finally:
        connection.close()

    if args.json:
        print(json_module.dumps(body, indent=2))
        return EXIT_OK

    if not rows:
        # The same precedence `pinakes_links` uses, for the same reason: when the caller narrowed
        # the walk, that is what changes their next move — a live neighbour may sit one dropped
        # argument away, and "your links resolve to nothing" would be false about the one they
        # filtered out. Only then does the dangling case get to speak.
        if present.is_filtered(rel=args.rel, direction=args.direction, depth=args.depth):
            print("no links match these arguments — retry without --rel/--direction, --depth 1")
        elif result.unresolved:
            print("links exist but resolve to nothing — see stderr")
        else:
            print("no links")
    for row in rows:
        arrow = present.arrow(row["direction"])
        label = row.get("title") or row["doc_id"]
        marker = " (other KB)" if row["terminal"] else ""
        print(f"{arrow} {row['rel']}: {label}{marker}  [hop {row['distance']}]")
    for entry in result.unresolved:
        print(f"!  {entry.rel}: {entry.node_key[1]} — {entry.reason}", file=sys.stderr)
    if result.truncated:
        print(
            f"truncated ({', '.join(sorted(result.truncated))}) — ask for fewer, or a lower depth",
            file=sys.stderr,
        )
    return EXIT_OK


COMMANDS: tuple[Command, ...] = (
    Command(
        "init",
        "Create a KB from a template",
        "I10",
        runner=lambda args: run_init(args),
        arguments=_init_arguments,
    ),
    Command(
        "templates",
        "List the templates this build can stamp a KB from",
        "T7",
        runner=lambda args: run_templates(args),
        arguments=_templates_arguments,
    ),
    Command(
        "sync",
        "Index changed sources (--rebuild for a full rebuild)",
        "I8b",
        runner=lambda args: run_sync(args),
        arguments=_sync_arguments,
    ),
    Command(
        "link",
        "Write a link from one document to another, into the source's sidecar",
        "L6",
        runner=lambda args: run_link(args),
        arguments=_link_arguments,
    ),
    Command(
        "links",
        "What a document connects to, and what connects to it",
        "L4",
        runner=lambda args: run_links(args),
        arguments=_links_arguments,
    ),
    Command(
        "search",
        "Hybrid retrieval: BM25 + vector + rerank",
        "I10",
        runner=lambda args: run_search(args),
        arguments=_search_arguments,
    ),
    Command(
        "ask",
        "What it would take to answer a question: cited evidence, confidence, and the work",
        "E1",
        runner=lambda args: run_ask(args),
        arguments=_ask_arguments,
    ),
    Command(
        "doctor",
        "Check environment, coherence, orphans, links, hooks",
        "I11",
        runner=lambda args: run_doctor(args),
        arguments=_doctor_arguments,
    ),
    Command(
        "upgrade",
        "Show what your template changed since this KB was stamped "
        "(writes nothing without --apply)",
        "T3",
        runner=lambda args: run_upgrade(args),
        arguments=_upgrade_arguments,
    ),
    Command(
        "install-hooks",
        "Install git hooks that keep the index fresh",
        "I12",
        runner=lambda args: run_install_hooks(args),
        arguments=_install_hooks_arguments,
    ),
    Command(
        "budget",
        "Show spend by day, month and operation (--resolve closes an unknown outcome)",
        "I6b",
        runner=lambda args: run_budget(args),
        arguments=_budget_arguments,
    ),
    Command(
        "serve",
        "Run the MCP server",
        "I13",
        runner=lambda args: run_serve(args),
        arguments=_serve_arguments,
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pnk",
        description="pinakes — a portable, agent-first knowledge base.",
        epilog=f"Design specification: {DESIGN_URL}",
    )
    parser.add_argument("--version", action="version", version=f"pinakes {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    for command in COMMANDS:
        sub = subparsers.add_parser(command.name, help=command.help, description=command.help)
        command.configure(sub)
        sub.set_defaults(_runner=command.run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    runner: CommandRunner | None = getattr(args, RUNNER_DEST, None)
    if runner is None:
        parser.print_help()
        return EXIT_OK

    try:
        return runner(args)
    except PinakesError as exc:
        print(f"error: {exc.message}\n{exc.remedy}", file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
