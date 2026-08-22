## Capping mcp, and the leg that had to be run against the defect (20260822 08:20)

**HIGH — a CI leg written to catch a defect is a claim until it is run against the defect, and the
mutation battery cannot reach this one.** No mutant of any tracked file makes `uv` resolve `mcp`
2.0.0: the thing under test is a *dependency resolve*, and `tools/mutate.py` mutates bytes in the
tree. So the leg was verified the only way left — `git archive HEAD | tar -x` into `/tmp`, the cap
deleted from the copy, `uv build`, and both new steps pointed at the resulting wheel:

    wheel-import: 1 module(s) did not import against the resolved dependency set:
      pinakes.serve: ModuleNotFoundError: No module named 'mcp.server.fastmcp'

and `pnk serve` exited 1 with no `"serverInfo"` anywhere in its output. (That block is the run's
real stdout, pasted. The first draft of this fragment paraphrased it into two module lines — in
the fragment whose whole thesis is that the artifact has to be run. Caught by review; a quoted
output that was retyped is a claim wearing evidence's clothes.)

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

**HIGH — and then the remedies for *those* had defects, in the same shape, found by a second
review that was asked only to refute them.** Three rounds, each finding less than the last, and
the third still finding four things that mattered:

- **The guard against a missing wheel failed open.** `set -- dist/*.whl; test -f "$1" && test $#
  -eq 1` — under `set -e`, a failing *first* command of an `&&` list does not abort, so an empty
  `dist/` fell through to `wheel="$PWD/dist/*.whl"` and carried on. The two-wheel case aborted,
  which is why it looked right. It is an `if` now. Two sessions found this independently within
  minutes of each other; it came in as a review suggestion and was implemented verbatim.
- **`make smoke` exited 0 while printing a traceback.** `pnk serve … | grep -q '"serverInfo"'` —
  grep matches, closes the pipe, the server dies on `BrokenPipeError`, and the pipeline's status
  is grep's. The target printed *"answers an MCP handshake"* over a crashed server, and a
  changelog entry claimed it ran the same checks as CI. Output to a file, then grep it twice.
- **`continue-on-error: true` defeats an assertion written against `if:`.** The test said *a gate
  that can be switched off is not a gate* and then checked one of the two ways to switch one off.
  On the step in front of `uv publish`, where being wrong is a version number PyPI will not take
  back.
- **The source-tree refusal was scoped to the checkout the script lives in.** This project mandates
  a worktree per change, so *another* checkout's editable install is a path the gate has never
  heard of — demonstrated with one checkout's interpreter and another's gate: a clean green pass
  over `src/pinakes`. A negative check has to enumerate every wrong answer; the positive one —
  the package must be inside a `site-packages` or `dist-packages` directory — has one right
  answer, and that is the difference between the two shapes.

**And a declaration test only pins the file the last edit touched.** `--min-modules 50` sat at
four call sites across three files; deleting it from any one of them survived every test, and the
tool then falls back to a floor of 20 against a package of 57 modules. The assertion now iterates
the invocations rather than grepping the tree, which is the same lesson as *read the sequence, not
the neighbourhood* in [`docs/RELEASING.md`](RELEASING.md): a property of a set is not a property of
any member of it.

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

**The battery is what turned three rounds of prose into three rounds of evidence.** Round one:
11 mutants, 11 killed. Round two, after the first review's fixes: 21 mutants, **3 survived** — and
all three were tests written from the fix's own description, which is a test of the description.
Round three, after the second review: 12 of 26 survived, every one of them in surface the remedies
had added. **A remedy is new code, and new code that nothing has tried to break is a claim.**

**What the new legs still cannot see, named so nobody reads them as more.** Import-time breaks
only, on the install states CI runs. A dependency that keeps its module layout and changes a
signature passes every step added here and fails on a user's machine. `[st]` — the *default*
backend — is resolved fresh by nothing, because it is ~2GB of torch. And `ci.yml` runs on push and
pull_request, so a major published on a quiet day is caught at the next push or at the tag, never
before: `release.yml` is where that matters, and it now carries both checks in front of
`uv publish`.
