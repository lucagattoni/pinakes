# Mutation batteries

One TOML file per target, run by [`tools/mutate.py`](../mutate.py) — the mutation step of
[`docs/BUILDING.md`](../../docs/BUILDING.md) § *One increment at a time* → 4.

    python3 tools/mutate.py tools/batteries/tools-release_order_gate.toml
    python3 tools/mutate.py --check-anchors tools/batteries/*.toml     # do they still hold?

Each row says: **break the code this way, and this named test dies.** A row is a claim about *one
assertion* — never about a commit, never about the file. A battery of forty-one kills does not say
the gate is correct; it says these forty-one breakages are each noticed by a test that names them.

## What this is, and what it is not

Say it precisely, because the obvious reading is wrong in a way that matters:

| | |
|---|---|
| **Committed** | the mutants, and the reasoning beside them |
| **Gated in `./check.sh`** | that every anchor still **resolves**, that every `kills` selector names a **test that exists**, that no file is claimed twice, and that each battery still carries the number of mutants it declares |
| **NOT gated** | **that the mutants still get killed.** Nothing runs a battery automatically |

**`tools/mutate.py` exits 0 when mutants SURVIVE** — deliberately: *"A SURVIVED row is a real
finding… It is not a harness failure, so this exits 0 — read the rows."* So the exit code cannot
carry a coverage regression, and anything CI-shaped built on top of this needs its own check on the
survivor count. `tests/test_batteries.py` is a **resolvability gate**, not a regression gate.

**And the denominator.** Every battery has exactly one primary target, and `ls
tools/batteries/*.toml` is the count — **do not restate it here**, because nothing turns red when it
moves: `tests/test_batteries.py` checks anchors and `kills` selectors, never this prose. It said
*"Nine … Seven"* from 20260826, when three batteries landed in one day and one was never added to
the total, until 20260830. **Two modules under `src/` have one** — `src-pinakes-init.toml`, over the
check that decides whether a KB's `.pinakes/` can reach a remote, and `src-pinakes-pairing.toml`, which spans **two** files,
`src/pinakes/pairing.py` and `src/pinakes/sync.py`, because the guarantee it mutates spans both. No
invariant in [`docs/INVARIANTS.md`](../../docs/INVARIANTS.md) has a battery of its own. The covered
files change 1–13 times in 30 days — **except `sync.py` at 39, which was this paragraph's own example
of high-churn code with no battery until 20260825**, and is named here so that change is visible
rather than quietly dropped. **Two further high-churn modules, one with no battery and one
covered without being named** — `src/pinakes/doctor.py` at 36 commits has none, while
`src/pinakes/cli.py` at 52 is mutated twice by `src-pinakes-init.toml` (measured 20260825 by
`git log --since="30 days ago" --follow`, over a repository whose first commit is 2026-07-25 — so
these are close to lifetime counts, not a steady-state rate; the `cli.py` correction is 20260826).
**A battery's name is not its coverage, and reading the names is how that sentence went wrong** —
`src-pinakes-init.toml` reaches `cli.py`, and `tools-mcp_handshake_gate.toml` reaches seven files
including `Makefile`, `check.sh`, `pyproject.toml` and both CI workflows. To ask what is actually
mutated, ask the batteries: `grep -h 'file = ' tools/batteries/*.toml | sort -u`. This is a
starting point, not a coverage claim, and a reader who greps a battery and finds every anchor
resolving has learned nothing about the code that has no battery at all.

**This paragraph is asserted, because it went stale in silence.** It read *"Four batteries, four
primary targets"* while five were on disk — the fifth arrived and nobody re-counted, which is the
same hidden-denominator failure the paragraph exists to prevent.
`test_the_committed_batteries_cover_only_tools_and_the_readme_says_so` now requires every battery
whose name does not begin `tools-` to be named here, so a new area cannot be added without the
sentence moving.

## Why these are committed

Batteries used to be discarded with the session that wrote them, and `tools/mutate.py`'s 0.27.0
docstring stated that as design. It was an assumption, and on **20260823** it was measured against
81 mutants recovered from six increments' session scratchpads:

| | |
|---|---|
| Anchors that still resolved exactly once, a day to a week later | **78 of 81** |
| The three that did not | **refused** — named, counted, exit 1, target untouched |
| Anchors that broke while their own code had not changed | **0** |

So the failure mode of keeping a battery is a **maintenance prompt, never a false certificate**. A
stale anchor cannot produce a false `KILLED` or a false `SURVIVED`: `mutate.py` resolves every
anchor in the batch before it writes anything, and refuses on 0 matches and on 2.

**That measurement is about anchors, which is the half that held.** The half that historically
broke is the **selector**: `docs/RETROSPECTIVES.md` records it going stale twice in a single
increment — *"a battery is source that goes stale like any other, and a SURVIVED row is a claim
about a pair — the mutant and the selector — either half of which can be wrong."* That is why
`tests/test_batteries.py` resolves selectors as well as anchors, and it is the more valuable half.

What being kept preserves is **not the proof**. Re-deriving forty-one mutants against a gate is an
afternoon's work. It is the *reasoning about which mutants were worth writing* — which breakages
are plausible, which one is the shipped defect the increment closed, and which two exist only
because a first-draft guard-test turned out to be a tautology. None of that is in the code.

The durable channel for that reasoning already existed: a per-mutant table can be written into a
`retro.d/` fragment, and `docs/RETROSPECTIVES.md` has exactly **one**, against 93 commits that speak
of a mutation pass. Discipline alone did not hold. That is the argument for a directory, and it is
also the reason not to over-claim what the directory does.

## How a battery earns its name

**A battery is named for its primary target: the path, `/` → `-`, extension dropped.** Not the
`YYYYMMDD_HHMM-` prefix `plans/`, `changelog.d/` and `retro.d/` carry — a battery is named for what
it covers, never for when it was written, because the name is how the next increment finds it.

    tools/release_order_gate.py   →  tools/batteries/tools-release_order_gate.toml
    src/pinakes/graph/traverse.py →  tools/batteries/src-pinakes-graph-traverse.toml

**Not collision-free** — two real pairs in this repository already flatten to one stem
(`src/pinakes/extract/floors.py` / `floors.toml`, and `src/pinakes/budget/prices.py` /
`prices.toml`). When that happens the second one **keeps its extension**
(`src-pinakes-extract-floors.toml.toml`), and `test_every_battery_is_named_for_a_file_it_actually_mutates`
accepts both spellings.

**A battery may mutate more than one file when the guarantee spans more than one.**
`tools-mcp_handshake_gate.toml` mutates seven — the gate, `src/pinakes/serve.py`, both workflows,
the `Makefile`, `check.sh` and `pyproject.toml`'s dependency floor — because the thing it protects,
*a published wheel still answers `initialize` with Pinakes' own name, version and tool list*, lives
in all seven. Four of its mutants are one idea in three files (`| tee` and `|| true` in `ci.yml`,
`set +e` in `release.yml`, a command substitution in the `Makefile`: a gate is only a gate when its
exit status is what the next command reads). Split by file, that pattern is invisible.

**Adding a mutant: grep first.**

    grep -l 'file *= *"src/pinakes/serve.py"' tools/batteries/*.toml

The `*` matters — a battery may align its keys, and a lookup that misses one reports *no battery
claims this file*, whose remedy below is the single thing this convention forbids.

One hit → add it there. No hits → start a battery named for that file. **Two hits is a defect**, and
both `--check-anchors` and `./check.sh` fail on it: a file belongs to exactly one battery, so an
increment touching it again has one place to add to and cannot leave two sets of mutants that
disagree. That is the whole reason these are one-file-per-target rather than one-file-per-increment.

**An increment appends a section; it never starts a second file for a target that already has one.**
Sections are ordered oldest release first and name the release that shipped the property; work that
has not been released yet says `unreleased, YYYYMMDD` — a version number belongs to a release when
it is cut.

## When an anchor rots

It rots loudly — `mutate.py` names the anchor and its count and exits 1 with the file untouched.
Four repairs, all of them from real instances:

- **0 matches, the code moved.** Re-anchor on the property and say in a comment what changed.
  (`ascending=True` / `minimum=15,` stopped being adjacent when `starts_at` landed between them.)
- **2 matches, a second call site appeared.** Widen by one *stable* neighbouring line, not by a
  comment. (A second `newest_may_lag=True,` arrived with the seventh sequence; the `minimum=15,`
  above it belongs to that sequence alone.)
- **The target was split.** Move the mutant to the battery of the file its code now lives in — or,
  if the guarantee still spans both, keep it here and let this battery mutate both files. Deletion
  is not the repair for a move.
- **The property is genuinely gone.** Delete the mutant, say so in the section, and change
  `mutants = N` in the same edit. That second line is what makes a shrinking corpus visible.

**Repair `new` whenever you repair `old`.** Both recorded repairs widened `old` and left `new`
behind, and one of them produced a mutant that deleted a neighbouring keyword argument and
duplicated another — `keyword argument repeated`, a `SyntaxError` at import, which this repository's
tests raise *inside* a test rather than at collection. It read `KILLED`, in a batch reporting
`0 errored`, about a property never exercised. `refuse_a_mutant_that_cannot_compile` now catches the
syntax half of that; **nothing catches the other half**, where the edit still compiles and simply
changes two things under a name promising one. Read the diff the mutant produces, not the anchor.

## Conventions

- **`mutants = N`, at the top of every battery.** `load_battery` refuses a file whose count is
  wrong. Nothing else here is a count, and without one a corpus can shrink to a single mutant with
  every other check green.
- **No `pytest` key.** A committed battery takes the default, `uv run --frozen pytest` — one fewer
  thing that can rot. Keep it only for a battery that genuinely needs another runner.
- **Targets under `tests/` are refused**, by `mutate.py` and by `./check.sh`: a mutant in the file
  its own selector runs can make that test vacuous, and no printed outcome would say so.
- **Selectors are `tests/x.py::test_y` or `tests/x.py::TestClass::test_y`.** A bare file path is a
  legal pytest selector and is refused here — a mutant that names a whole file names no assertion.
- **Comments carry the reasoning.** They are the reason these files exist; `mutate.py` ignores them
  and a reader does not.

## What the cheap checks cannot see

`--check-anchors` resolves anchors against the **working tree** — not `HEAD`, because nothing is
written and requiring a clean tree would disarm it mid-refactor, which is when it is wanted. It
reports every failure rather than the first, and runs no subprocess.

Neither it nor `tests/test_batteries.py` can see:

- **an anchor that still resolves while the code around it moved**, so the mutant would be `KILLED`
  about a property nobody tests any more. **Nothing detects this.** It is why a mutant's `name`
  states what the breakage *is* rather than what the edit does: the name is what a reader compares
  against the code, and it is the only guard there is;
- **whether the mutants still die.** Only running the battery says that.

A green check is not a green run. Run the battery.

## Reading a SURVIVED row

**A `SURVIVED` row is a claim about a *pair* — the mutant and the selector named in its `kills` —
and it does not say which half failed.** Before believing that a survivor means the behaviour is
untested, **run the mutant against the whole suite** — but run it as
`uv run pytest --ignore=tests/test_batteries.py`, and the flag is not optional. If something else
kills it, the battery was right about the risk and wrong about the witness: the row names the wrong
test, and the fix is the selector, not a new test. If nothing kills it, the gap is real. One command
separates two diagnoses that look identical in the report, and the wrong one costs a test nobody
needed.

**🛑 Why the flag: this remedy has a false-positive mode, and it fires on exactly the batteries that
cover `tools/`.** The whole suite includes
[`tests/test_batteries.py`](https://github.com/lucagattoni/pinakes/blob/main/tests/test_batteries.py),
whose `test_every_anchor_still_resolves_exactly_once_in_the_file_it_names` fails on **any** edit to a
battery target — which is what a mutant is. So the suite goes red for a survivor as readily as for a
kill, and *"something else killed it"* is exactly the wrong conclusion. **Measured 20260826 11:43 UTC**, not
argued: applying `tools-fragments.toml`'s first mutant to `tools/fragments.py` and running the two
files separately gave the intended killer **exit 1** *and*
`tests/test_batteries.py` **exit 1**, `1 failed, 10 passed`, the failure being the anchor check.
Restored, both green, 51 passed. **`tools/mutate.py` is not affected and its report was never
wrong** — it runs only the selector a row names. The false positive belongs to *this paragraph's
advice*, and it existed from the day the advice was written.

**And be suspicious of a target whose every assertion goes through one summarising helper.** If the
tests for a function all compare its output through something that reduces a sequence to a
count-by-kind — a census, a set, a sorted list — then **mutants that change the *order* of that
sequence and not its contents will survive every one of them**, because the helper deletes exactly
the property the mutant changed. Measured on `src/pinakes/pairing.py` at `cd9f009`, 20260825: its
actions are a list, `documents.path` is `UNIQUE`, so the order *is* the behaviour — and a mutant that
moved a `SoftDelete` past an `Adopt` produced an identical census and **was killed by nothing in the
repository: 2 165 tests, of which the 267 in the three modules covering that code are the ones that
were supposed to.** The remedy is a named property asserting the ordering directly
(`retires_before_adopting()`), not another assertion routed through the same helper.
