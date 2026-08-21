# The mutation harness — a committed `tools/mutate.py`

**Status: proposed 20260821 07:45 — not scheduled.** One increment, buildable whenever the deep
release's queue allows; nothing blocks it and it blocks nothing.

## Why this exists

The mutation step ([`docs/BUILDING.md`](../docs/BUILDING.md) § 4) is the procedure's one
silently-failing step with no executable guard: a broken harness reports SURVIVED and
KILLED exactly like a working one. The record (`docs/RETROSPECTIVES.md`, G1 20260801 → E5
20260812) counts more than a dozen invalid runs or silently destructive restores across ten
increments — six of them the identical `git checkout` trap, still recurring after four write-ups,
and E5's own words are *"knowing the trap was not enough to avoid it"*. The precedent is
`tools/land.py`: when prose has failed repeatedly against a class that fails silently, the rule
gets a tool.

## What it is

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

## Tests

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

## What it does not do

Cross-file mutants, generated mutation operators, and mutating test files themselves stay manual —
the tool refuses loudly rather than approximating. `docs/BUILDING.md` § 4 points here once the
tool lands; until then its written rules are the procedure.

## Exit criteria

The six tests above; the tool used for its own increment's mutation pass; a
`docs/VERIFICATION.md` row per refusal.
