## Capping mcp, and the leg that had to be run against the defect (20260822 08:20)

**HIGH — a CI leg written to catch a defect is a claim until it is run against the defect, and the
mutation battery cannot reach this one.** No mutant of any tracked file makes `uv` resolve `mcp`
2.0.0: the thing under test is a *dependency resolve*, and `tools/mutate.py` mutates bytes in the
tree. So the leg was verified the only way left — `git archive HEAD | tar -x` into `/tmp`, the cap
deleted from the copy, `uv build`, and both new steps pointed at the resulting wheel:

    wheel-import: 1 module(s) did not import against the resolved dependency set:
      pinakes.extract.pdfium → the declared allowance; pinakes.serve: ModuleNotFoundError:
      No module named 'mcp.server.fastmcp'
    pnk serve → exit 1, no "serverInfo" anywhere in the output

Without that, *"the leg would have caught it"* is a statement about a check that has only ever
been run against a fixed tree — the shape [`docs/BUILDING.md`](BUILDING.md) already refuses for a
test (*"pinned by test X is a claim about a failing test"*). **The generalisation: when the battery
cannot reach a guard, build the broken artifact by hand and point the guard at it.** It cost about
four minutes.

**HIGH — the review's own remedies were where the remaining defects were, exactly as
[*verify the remedy, not only the finding*](#verify-the-remedy-not-only-the-finding-20260822-0725)
predicted the night it landed.** Two of the three worst findings in this increment were not in the
first draft's *logic* but in the mechanisms written to guard it:

- **An allowance keyed on the library forgave the module the gate exists for.** `--allow-missing
  pypdfium2` excused *any* module failing on `pypdfium2` — including `pinakes.serve`, had anything
  on its import chain ever reached it. Demonstrated against a synthetic package: `serve` did not
  import and the gate printed a clean pass. An allowance now names the **module and the library**,
  and a `--require`d module may never appear in one.
- **The "the gate can still fail" step was satisfied by an environment where the gate never ran.**
  It grepped the tool's generic failure headline — which the tool also printed when the package
  itself was not importable, i.e. when `--with` installed nothing (a mistyped extras syntax does
  exactly that; measured). The two branches now print different headlines and the step names the
  one failure the bare wheel genuinely has. The defect was *inside the step written to prevent that
  class*, and a test pinned the collision rather than catching it.

The fragment's cheap test applied to this increment's own thesis — *what input would look
different if the remedy were absent?* — is the uncapped wheel above. It exists, and it is the
answer to the question this increment turns on: without it, the cap is the only real change and
the CI leg is decoration.

**MEDIUM — a gate that reads a range of lines reads the prose inside the range.** `check.sh`'s
extras-not-core gate is `awk '/^dependencies = \[/,/^\]/' pyproject.toml | grep -qiE
'pypdfium2|anthropic'`. The comment added above `mcp` — explaining that `anthropic` was measured
and deliberately *not* capped — turned it red and reported anthropic as a core dependency. The gate
had been correct for a year only because nobody had written a comment in that block. Same class as
0.25.3's `textwrap` reflow of a `\`-continued shell command: a line-shaped tool applied to
structure it does not model. The parsed-side test never had the problem, because it reads the
requirement list rather than the lines.

**MEDIUM — nothing resolves a test path written in a comment.** `check.sh` and
`tests/test_paid_path.py` both pointed readers at
`test_packaging.py::test_paid_and_pdf_clients_stay_out_of_core`. That test has never existed under
either file's history; the real name is `test_extractors_stay_extras`. `docs/VERIFICATION.md` is
gated for precisely this reason — *a table of test paths is prose until something executes it* —
and a comment is prose that nothing gates at all. Both fixed; the class is open everywhere else.

**MEDIUM — measure the sibling before capping it, and measure the surface you actually call.**
Capping all three lower-bound-only requirements was the obvious response and would have been
wrong. Both siblings were measured: `anthropic` 1.0.0 and `sentence-transformers` 6.0.0 keep every
constructor parameter, response-model field (`Message`, `Usage`, `MessageTokensCount`) and method
signature (`encode`, `predict`, `get_sentence_embedding_dimension`, `max_seq_length`) that `src/`
touches. **The first pass measured only the constructors, and review caught that.** The gap mattered:
`extract/claude.py` consumes `response.model_dump()` as a *dict*, so a renamed `Usage` field would
compute a cost of **0** — the spending guard silently disabled, with no exception anywhere. A
constructor signature says nothing about that. **The remedy for the class is testing the resolve,
not capping on reflex**; a project that caps everywhere buys the same silence with a different
cause.

**What the new legs still cannot see, named so nobody reads them as more.** Import-time breaks
only, on the install states CI runs. A dependency that keeps its module layout and changes a
signature passes every step added here and fails on a user's machine. `[st]` — the *default*
backend — is resolved fresh by nothing, because it is ~2GB of torch. And `ci.yml` runs on push and
pull_request, so a major published on a quiet day is caught at the next push or at the tag, never
before: `release.yml` is where that matters, and it now carries both checks in front of
`uv publish`.
