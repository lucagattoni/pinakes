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
| **Gated in `./check.sh`** | that every anchor still **resolves**, that every `kills` selector names a **test that exists**, that no file is claimed twice, that each battery still carries the number of mutants it declares, and that every **section header** names one of the two reserved forms |
| **NOT gated** | **that the mutants still get killed.** Nothing runs a battery automatically |

**`tools/mutate.py` exits 0 when mutants SURVIVE** — deliberately: *"A SURVIVED row is a real
finding… It is not a harness failure, so this exits 0 — read the rows."* So the exit code cannot
carry a coverage regression, and anything CI-shaped built on top of this needs its own check on the
survivor count. `tests/test_batteries.py` is a **resolvability gate**, not a regression gate.

**And the denominator.** Every battery has exactly one primary target, and `ls
tools/batteries/*.toml` is the count — **do not restate it here**, because nothing turns red when it
moves: `tests/test_batteries.py` **does** read this prose, but only to check that every battery
outside `tools/` is **named** here and that the phrase *starting point, not a coverage claim*
survives — never for a number. **That clause read *"checks anchors and `kills` selectors, never this
prose"* until 20260831**, which would send a session that had just tripped the gate to debug the
wrong thing. It said
*"Nine … Seven"* from 20260826, when three batteries landed in one day and one was never added to
the total, until 20260830. **Three batteries are named for a module under `src/`** — `src-pinakes-init.toml`, over the check
that decides whether a KB's `.pinakes/` can reach a remote; `src-pinakes-pairing.toml`, which
spans **two** files, `src/pinakes/pairing.py` and `src/pinakes/sync.py`, because the guarantee it
mutates spans both; and `src-pinakes-budget-ledger.toml`, which spans **three** —
`src/pinakes/budget/ledger.py`, `src/pinakes/budget/accountant.py` and
`src/pinakes/extract/claude.py` — because the money path's kills live *between* the estimate and
the ledger rather than at either end of it. **It is the first battery over the paid path at all**,
added 20260902 after a money assertion that had never held by construction went red on a refreshed
exchange rate. **Named for is not covers**: eight files under `src/` are mutated by some
battery, `src/pinakes/serve.py` among them via `tools-mcp_handshake_gate.toml` — which is why a
`src-pinakes-serve.toml` proposed on 20260831 was refused by
`test_no_file_is_claimed_by_two_batteries` and its rows appended to the handshake gate instead.
**No battery is *named* for an invariant** — a primary target is a file, so none can be — but two
mutate [`docs/INVARIANTS.md`](../../docs/INVARIANTS.md) territory and say so in their own headers:
`src-pinakes-init.toml` over whether `.pinakes/` can leave the machine, `src-pinakes-pairing.toml`
over ULID permanence. **This read *"No invariant … has a battery of its own"* until 20260831** —
true of the filenames, false of the coverage.

**The churn figures here are frozen to a window *and a tree*, and must not be re-measured into a
rolling one.** Over **20260801–20260901, on `main` at `f0dde97`**, the covered files change 3–29
times. The two that stand out are the two this paragraph has always argued about: `src/pinakes/cli.py`
at **29**, mutated twice by `src-pinakes-init.toml` without appearing in its name, and
`src/pinakes/doctor.py` at **23**, which still has no battery at all. The highest-churn file whose
battery *is* named for it is `tools/release_order_gate.py` at **13**; `src/pinakes/sync.py` is at
**18**. **`src/pinakes/serve.py` sits at 4, which is the point** — it earned its rows from one
measured trap (macOS recycles a thread id the moment its thread is reclaimed, so a test keyed on
`get_ident()` passed against unfixed code), not from churn. Churn is a prompt here, never the
criterion. **The figures this paragraph carried before — *39*, *52*, *36*, a *1–13* range — were
`--since="30 days ago"` read on 20260825 over a repository whose first commit is 2026-07-25**: near-
lifetime counts wearing a 30-day label, which stopped describing the tree as the window slid off the
repo's first week, without a word changing. A window that names its dates and its sha goes stale
honestly; a rolling one rewrites its own past.
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
it is cut. The separator is a middle dot: `# 0.30.0 · what the section is about`.

**The header is gated; the fence and the ordering are not.**
`tests/test_batteries.py::test_every_section_header_names_the_release_it_belongs_to` refuses a third
form. It reads the header out of the raw bytes — `tomllib` drops comments — so a section is whatever
sits **fenced between two rule lines**, and a rule may be drawn with box-drawing `─` *or* ASCII `-`.
Both shapes are in the tree and two batteries mix them internally, so the fence is not even a
per-file property: a checker matching one shape read 34 of 36 headers and skipped a header that had
drifted. Nothing checks that a date is a real date, or that sections actually run oldest-first.

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
