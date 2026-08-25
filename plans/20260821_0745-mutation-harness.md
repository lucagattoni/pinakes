# The mutation harness — a committed `tools/mutate.py`

**Status: BUILT and released in 0.27.0, 20260822 06:19.** One increment, as planned.

**What shipped beside what this plan asked for.** All six numbered steps and both controls are
built as written. Five things the plan did not name were measured while building it, and each is
now a refusal of its own: a **skipped** test exits 0 exactly like a passing one, so a selector that
skips in this checkout reports SURVIVED for every mutant aimed at it; an **already-red** selector
reports KILLED for every mutant, including the ones nothing catches — both closed by a pre-flight
run per selector, which also times it and bounds the mutated run; **`SIGHUP` and `SIGQUIT` skip
`finally` exactly as `SIGTERM` does**; **`PYTEST_ADDOPTS`** is inherited, so `-x` in the operator's
shell narrows a two-test kill to one; and **`PYTHONPYCACHEPREFIX`** moves every `.pyc` out of the
clearing's reach. One more came from review: pytest's `<error>` tag covers a *collection* failure
**and** a *setup or teardown* failure, which are opposite events, and conflating them tallied a
genuine assertion-kill as `0 killed`.

**The two fields the record asks for and this plan does not specify, so they were not built**:
`expect_green` (T4's *"control that had to stay green"* column) and a per-mutant zero-kill
allowance. Both are decisions, not omissions.

> ### ❌ DECLINED 20260825 18:16 by the user — `expect_green` and the per-mutant zero-kill allowance
>
> **Measured, not argued.** `expect_green` exists in exactly **two commits** in the whole history and
> in **no** source, test, doc or CHANGELOG entry. Across **136 mutants in six committed batteries,
> zero** ask for a green control. `load_battery` validates presence only and rejects no unknown key,
> so an `expect_green = …` written today would be **parsed, ignored, and reported to nobody**.
>
> **The recorded practice is better than the field would be.** A misbehaving mutant is re-aimed,
> replaced, or not written — three times over in the committed batteries, each with its reason in
> place (*"The survivor was the battery working"*). Three batteries carry *"Mutant 1 is the control"*
> and one carries an explicit *"No control here"* with its reason. **A committed convention already
> answers the batch-level need.**
>
> **And the demand is thinner than it looked.** Of the five filled entries in T4's table, one is
> about *which assertion fired* and one records tests that *fail* to catch — **neither is expressible
> as a green control** at all.
>
> **Decisively: it is not the guard for the hole that is actually open.** `tools/batteries/README.md`
> names one thing nothing catches — *an anchor that still matches while the code around it moved* —
> and its stated remedy is a human reading the diff the mutant produces. `expect_green` does not
> reach that, and adding it would look like it did.
>
> **What would re-open this:** a battery whose author can state a control they cannot express by
> re-aiming a mutant. None of the six can.

**Exit criteria, met:** the six tests are 52; the tool was used for its own increment's mutation
pass — **25 mutants against its own guards, 25 killed** — and `docs/VERIFICATION.md` carries ten
rows in § *Release machinery*.

## Why this exists · **CLOSED 20260822, built and released in 0.27.0**

The mutation step ([`docs/BUILDING.md`](../docs/BUILDING.md) § 4) is the procedure's one
silently-failing step with no executable guard: a broken harness reports SURVIVED and
KILLED exactly like a working one. The record (`docs/RETROSPECTIVES.md`, G1 20260801 → E5
20260812) counts more than a dozen invalid runs or silently destructive restores across ten
increments — six of them the identical `git checkout` trap, still recurring after four write-ups,
and E5's own words are *"knowing the trap was not enough to avoid it"*. The precedent is
`tools/land.py`: when prose has failed repeatedly against a class that fails silently, the rule
gets a tool.

## What it is · **CLOSED 20260822, built and released in 0.27.0 — its "per-increment battery" framing was reversed in 0.29.0; batteries are committed in `tools/batteries/`**

A runner for the per-increment mutation battery. Input: a list of mutants — `(file, old, new)`
plus the test selector expected to kill each. For each mutant it:

1. **Refuses if the target file differs from `HEAD`** — the restore below is only as precise as
   what it restores to, and an uncommitted fix in the target is exactly what a restore destroys.
2. Snapshots the file's bytes, **asserts `old` occurs exactly once**, writes the mutant.
3. **Deletes the module's `__pycache__` entries** after the write and again after the restore —
   CPython invalidates on (mtime-to-the-second, size), so a same-length mutant applied and
   reverted within one second otherwise runs from stale bytecode (T3).
4. Runs `pytest` on the given selector **without `-x`**, recording which tests failed.
5. Restores **from the snapshot** — never `git checkout` — and verifies the restored bytes equal
   the snapshot, in a `finally`, so a killed run cannot poison the mutants after it (L6).
6. Reports one row per mutant: KILLED (by which tests) or SURVIVED.

**Controls the report refuses to run without.** A batch reporting zero kills exits non-zero as a
broken-harness result, not a clean bill (`--allow-zero-kills` for the rare deliberate probe of a
backstop documented as unpinned). A syntactically invalid mutant — pytest `ERROR`, not `FAILED` —
is its own outcome, never counted as killed or as survived; T4 measured both misreadings.

## Tests · **CLOSED 20260822, built and released in 0.27.0**

Drive the real script as a subprocess (the `tools/paid_path_gate.py` / `tools/fragments.py
--repo` precedent), against a scratch repo:

- an anchor matching zero times, or twice, refuses before writing, naming the file and anchor;
- a target file dirty against `HEAD` refuses before writing anything;
- a same-length mutant is detected — and the test must fail against a harness with the
  `__pycache__` invalidation removed, or it has not pinned the invalidation;
- after a run the target's bytes equal the pre-run bytes, including when pytest is killed mid-run;
- a zero-kill batch exits non-zero with the broken-harness message, and `--allow-zero-kills`
  overrides it;
- an invalid-syntax mutant reports its own outcome, distinct from KILLED and SURVIVED.

## What it does not do · **CLOSED 20260822, built and released in 0.27.0**

Cross-file mutants, generated mutation operators, and mutating test files themselves stay manual —
the tool refuses loudly rather than approximating. `docs/BUILDING.md` § 4 points here once the
tool lands; until then its written rules are the procedure.

## Exit criteria · **CLOSED 20260822, built and released in 0.27.0**

The six tests above; the tool used for its own increment's mutation pass; a
`docs/VERIFICATION.md` row per refusal.
