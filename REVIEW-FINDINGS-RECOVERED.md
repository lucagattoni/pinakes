# Adversarial review of S16/S19 — findings RECOVERED from dead agents

**The workflow returned `{"raised":0,"confirmed":[],"refuted":[]}` and that was a LIE OF OMISSION.**
17 of 19 agents died on a session limit; `.filter(Boolean)` erased them. Two finder agents had
already written their findings, and those transcripts survived on disk. **Nothing here has been
refuted — every refuter died — so each finding is a raised claim, not a confirmed defect.**

Recovered from `<the session's workflow transcript directory, local only>`.

---

## 1. [MEDIUM] A single recorded per-document failure inside a reordered chain re-opens S16: uncaught sqlite3.IntegrityError, half-applied index, doctor OK

- **File:** `src/pinakes/sync.py`:1461
- **Raised by:** `agent-a5b8b862bc84c94fb.jsonl`

**Claim.** The order pairing emits is only applicable while EVERY action succeeds. `_apply`'s handler at sync.py:1461 catches `(PinakesError, OSError, ValueError)` — not `sqlite3.IntegrityError` — and on a recorded failure it rolls back, so the failed action's row never leaves its old path. The loop at sync.py:1165 then applies the very next action, which the new topological pass placed there *precisely because* it depends on that move. It writes onto the still-held path, `documents.path` UNIQUE fires, and the raw `sqlite3.IntegrityError` escapes `_apply`, `_run`, `sync()` and `cli.main` (which catches only `PinakesError`). This is the full S16 symptom set the increment claims to fix, reached through the module's own first-class 'failures are recorded, the run continues' path. Nothing in `_order_for_path_availability`'s docstring, in `tests/test_pairing.py`, or in `tests/test_sync.py::test_a_rename_chain_syncs_and_every_document_keeps_its_id` names this boundary — every new test exercises only the all-succeed case. Not a regression (main crashes on the same input, earlier), but the fixed class is narrower than the record says, and the crash now lands AFTER partial commits instead of before any.

**Failing input.** Three paid-extracted PDFs a.pdf/b.pdf/c.pdf indexed with a paid backend. Reorganise the folder as a chain — c.pdf→d.pdf, b.pdf→c.pdf, a.pdf→b.pdf, sidecars travelling — and edit the middle one's bytes while it moves. Run `pnk sync` with a free effective backend. (Equivalently: any chain where one document raises OSError/ValueError at index time.)

**Evidence.** Reproduced in the worktree. `pair()` correctly orders the chain [Adopt(c.pdf's doc→d.pdf), Adopt(b.pdf's doc→c.pdf), Adopt(a.pdf's doc→b.pdf)]. The second action raises PaidExtractionRequiredError (decision 14, the designed graceful failure), is recorded and rolled back, so its row stays at docs/b.pdf. The third action then hits: `*** RAW sqlite3.IntegrityError ESCAPED sync(): UNIQUE constraint failed: documents.path`. Index left as [('docs/a.pdf','active'), ('docs/b.pdf','active'), ('docs/d.pdf','active')] while disk holds ['b.pdf','c.pdf','d.pdf'] — two active rows pointing at paths that do not exist, `set_meta`/`_scan_linked_kbs`/`_derive_edges` all skipped. `doctor.diagnose()` on that KB flags nothing about it and even lists the phantom `docs/a.pdf` in its 'paid extraction not requested' warning. The same shape reproduces with a plain markdown chain and an embedding failure. Verified against a control: the identical chain with no failure syncs cleanly (renamed=3, minted=0, deleted=0).

---

## 2. [MEDIUM] _order_for_path_availability is O(n^2) in the action count and fires on any single ordering constraint — 0.08s to 4.9s at 40k documents

- **File:** `src/pinakes/pairing.py`:594
- **Raised by:** `agent-a5b8b862bc84c94fb.jsonl`

**Claim.** The Kahn loop keeps `ready` as a plain list: line 582 does `ready.pop(0)` (O(len(ready))) and line 594 rebuilds it with `ready = sorted([*ready, *newly])` on EVERY iteration, even when `newly` is empty. `ready` starts holding every unconstrained action, so both operations are O(n) per emitted action and the pass is O(n^2) over the whole plan. It runs in full whenever `blocked_by` is non-empty — i.e. one constrained action drags all n actions through the quadratic loop. Two of the triggers are exactly what this increment is about (any rename chain, any swap) and one is a plan that was ALREADY applicable before this change and gains nothing from being sorted: the same-path `SoftDelete` + `Adopt` pair emitted when one sidecar's id disagrees with its index row. A heap (`heapq`) or a deque makes it O(n log n) with no change in output — the pass is already proven complete and stable, so this is purely the queue implementation.

**Failing input.** A KB of N unchanged documents (all Skip) plus ONE document whose `.pnk.yaml` id disagrees with its index row — e.g. a sidecar restored from git or copied from another clone. That emits SoftDelete+Adopt at one path, already in the right order, which is enough to set `blocked_by` and run the sort over all N+2 actions.

**Evidence.** Measured in the worktree with `uv run python`. Whole `pair()`, no constraint vs one constraint: n=5000 0.007s/0.079s; n=10000 0.016s/0.314s; n=20000 0.043s/1.240s; n=40000 0.082s/4.926s; n=80000 0.18s/20.75s; n=120000 0.27s/46.12s. `_order_for_path_availability` isolated: 0.070s @5k, 0.296s @10k, 1.179s @20k, 4.809s @40k — 4x per doubling, so all of the cost is here. Invisible at the documented 300-document RFC corpus scale; seconds to a minute on every sync for a KB in the tens of thousands of documents, for as long as the constraint persists.

---

## 3. [LOW] Cycle actions are appended to the END of the plan, not left in place — the docstring's 'unchanged behaviour, deliberately' is measurably wrong

- **File:** `src/pinakes/pairing.py`:600
- **Raised by:** `agent-a5b8b862bc84c94fb.jsonl`

**Claim.** Line 600 (`ordered.extend(actions[index] for index in sorted(remaining))`) preserves the cyclic actions' order among themselves but moves them after every non-cyclic action. The comment above it at lines 596-598 says they 'go out in their original relative order — unchanged behaviour, deliberately ... so a swap fails at its first write exactly as it does today'. That is true of the swap and false of the plan: a sync containing an unresolvable name swap now commits every other action first — including `Mint`, which writes a permanent-ULID `.pnk.yaml` into the user's tree via `_mint`/`create_sidecar` — and only then crashes. On main the swap crashed first and none of it happened. The outcome is arguably an improvement, but it is an undocumented behaviour change on the deferred half, and `test_a_name_swap_is_left_in_its_original_order_because_no_order_works` cannot see it: it asserts only the two Adopts' relative order, never their position in the plan.

**Failing input.** Two documents a.md and b.md indexed, then their names and sidecars swapped past each other (an unresolvable cycle), plus one brand-new file z.md added in the same sync. Run `pnk sync`.

**Evidence.** Reproduced with the ordering pass on and monkeypatched off in the same worktree. POST-FIX: crashed on `UNIQUE constraint failed: documents.path`, rows = [docs/a.md active, docs/b.md active, docs/z.md active], sidecars on disk = ['a.md.pnk.yaml','b.md.pnk.yaml','z.md.pnk.yaml']. PRE-FIX (identical world, `_order_for_path_availability` replaced by identity): crashed on the same error, rows = [docs/a.md, docs/b.md], sidecars on disk = ['a.md.pnk.yaml','b.md.pnk.yaml'] — no z.md row and no z.md sidecar written.

---

## 4. [LOW] `emitted` in _order_for_path_availability is written and never read

- **File:** `src/pinakes/pairing.py`:580
- **Raised by:** `agent-a5b8b862bc84c94fb.jsonl`

**Claim.** `emitted: set[int] = set()` is declared at line 580 and populated at line 584 (`emitted.add(index)`), but nothing ever reads it — the cycle set is recovered from `remaining` at line 600 instead. It reads like a guard that participates in the topological sort's correctness and does not. It costs a set insertion per action inside the loop that is already the quadratic hot spot, and it survives ruff and pyright strict (both green in `./check.sh`), so no gate will remove it.

**Failing input.** Any plan with at least one ordering constraint — e.g. the three-document rename chain in `tests/test_pairing.py::test_a_rename_chain_of_three_is_ordered_so_every_move_lands_on_a_free_path`.

**Evidence.** `grep -n emitted src/pinakes/pairing.py` returns only the declaration (580), the write (584), and prose mentions in the docstring/comments (528, 596). Deleting both lines changes no observable behaviour: the cycle bucket at line 600 is derived from `remaining`, which is maintained independently. Confirmed by reading the whole function; `./check.sh` is green with the dead variable present, so neither ruff nor pyright reports it.

---

## 5. [HIGH] The chain fix holds only if every action succeeds: sqlite3.IntegrityError still escapes uncaught, so S16's exact crash survives whenever one chain member fails to index

- **File:** `src/pinakes/sync.py`:1461
- **Raised by:** `agent-ad491810b66d6175c.jsonl`

**Claim.** `_order_for_path_availability` creates a dependency BETWEEN actions (action N frees the path action N+1 writes), but the executor has no notion of it. `_apply`'s `except (PinakesError, OSError, ValueError)` catches every per-document failure and *continues* — deliberately, per its own docstring ("one broken file cannot block a thousand good ones", "failures are recorded, the run continues") — and a caught failure ROLLS BACK, leaving that document's row at its old path. The next action in the ordered chain then writes onto that still-occupied path and raises `sqlite3.IntegrityError`, which is not in the except tuple, is not a `PinakesError`, and so escapes `_apply` -> `_run` -> `sync()` -> `cli.main()`'s `except PinakesError` (src/pinakes/cli.py:1857). The process dies on a raw traceback and the index is left describing paths that no longer exist. That is S16's full symptom set, reproduced on this branch. This is a RESIDUE, not a regression (main crashes on the same input too) — but nothing in the branch records it, while `src/pinakes/pairing.py:513` states unqualified that this function "is the only thing that makes a rename chain applicable" and `tests/test_sync.py::test_a_rename_chain_syncs_and_every_document_keeps_its_id` covers only the all-succeed path. Containment is one line: adding `sqlite3.IntegrityError` to `_apply`'s except tuple would turn both this residue and the deliberately-deferred cycle class into a recorded failure with a remedy instead of a traceback.

**Failing input.** KB with docs/a.md, docs/b.md, docs/c.md indexed. Rename the chain on disk last-first (c.md->d.md, b.md->c.md, a.md->b.md, sidecars with them), then save d.md in a non-UTF-8 encoding — b"# Gamma\n\n\xff\xfe legacy encoding\n" — the exact trigger tests/test_sync.py::test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row already uses. Ordered plan is [Adopt(c_id -> d.md), Adopt(b_id -> c.md), Adopt(a_id -> b.md)]; the first fails on UnicodeDecodeError (recorded, rolled back, c_id still holds docs/c.md), the second collides. Any caught failure class reaches this: OSError from a file replaced between the walk and the write, ExtractorMissingError (verified separately with a chain ending in a .pdf name while the [pdf] extra is absent), BudgetRefusedError, SidecarError.

**Evidence.** Ran end to end at HEAD ec73b1f with the repo's own FakeBackend, no monkeypatching (script: <a local scratchpad path, not committed>). Output: `SYNC2 RAISED: sqlite3.IntegrityError: UNIQUE constraint failed: documents.path`; index after = docs/a.md, docs/b.md, docs/c.md (all active); disk after = b.md, c.md, d.md. Only docs/d.md gets a `failures` row; the three rows now pointing at nonexistent paths are reported clean. A second, independent unpatched witness (repro4.py, chain ending in a .pdf name with pypdfium2 not installed) produces the identical traceback.

WHAT I PROVED CLEAN, so the parent has the negative results too. (1) PERMUTATION: over 600k randomised pair() walks (up to 5 pre-existing rows, 6 paths, deleted rows, paid/free backends, force/explicit-extract) the ordered list is always a multiset permutation of the unordered one — 0 drops, 0 duplicates. Structurally: `remaining` starts as `blocked_by` (every dep set non-empty, self-edges excluded at pairing.py:583), initial `ready` is its exact complement, a dependent is appended to `newly` only in the same step it is `del`eted from `remaining` (so `remaining.get` returns None on any later visit), and the tail appends exactly `sorted(remaining)`. (2) NO NEW FAILURES: 0 plans that applied cleanly pre-fix fail post-fix; 27 034 that failed pre-fix now apply. (3) IDENTICAL OUTCOME: when both orders apply cleanly, the final documents table is byte-identical in 300k cases — no ULID moves, none is dropped or regenerated. (4) Every residual failure in 500k walks is a genuine cycle (Kahn leftover non-empty), never a chain the sort mis-ordered. (5) `--rebuild` is a strict no-op: `before` is empty so no target has a live holder and the pass returns the input list unchanged (0/20 000 order changes); `--sidecars-only` returns before pair(); doctor never calls pair(). (6) `pair()` never emits two writers aiming at one path, never two actions vacating one path (so `frees.setdefault` first-wins is safe), and never an action that frees its own target — asserted over 300k walks. (7) Chains of length 2..8, with and without sidecars, with and without a Mint landing on the freed head path, all apply. (8) No leftover of the backed-out cycle-refusal work: no dead error class, no unused import, ruff and ruff format clean on pairing.py, and tests/test_pairing.py + test_sync.py + test_verification.py + test_batteries.py are green (187 passed, 1 skipped).

---

## 6. [LOW] Battery row declares a `kills` selector for a mutant it says in prose is expected to survive — and the mutant does survive that test

- **File:** `tools/batteries/src-pinakes-pairing.toml`:325
- **Raised by:** `agent-ad491810b66d6175c.jsonl`

**Claim.** The row `a SoftDelete stops being recorded as freeing the path it retires` (line 310) opens with "**Expected to SURVIVE, and committed saying so.**" but its machine-readable `kills` field (line 325) claims `tests/test_pairing.py::test_a_retire_and_an_adopt_at_one_path_keep_their_order` dies. The battery format has no expected-survivor key — `tools/mutate.py` requires exactly `file`, `old`, `new`, `kills` — and `tests/test_batteries.py` gates only that the selector RESOLVES, never that it kills. So the file does not in fact commit saying so in the field that matters: `mutants = 16` counts this as a sixteenth kill claim, and tools/batteries/README.md's contract ("Each row says: break the code this way, and this named test dies") is false for this row. The prose is otherwise correct — the branch really is unreachable, see the evidence — so the defect is the contradictory field, not the reasoning.

**Failing input.** Apply the row's own `old`->`new` to src/pinakes/pairing.py (`case SoftDelete(path=path): return path` -> `return None` in `_vacates`) and run the selector the row names.

**Evidence.** Applied every pairing.py mutant in the battery in memory (no file touched) and ran each declared selector: rows 0, 1, 2, 7, 10, 12, 13, 14 all KILLED; row 15 -> `PASSED (mutant SURVIVED)`. Reasoning check: with SoftDelete no longer recorded as freeing, `frees` has no entry for docs/a.md, so the Adopt's `freed_by` is None, the `continue` at pairing.py:590 fires, `blocked_by` is empty and the pass returns the list untouched — the [SoftDelete, Adopt] order the same-path loop already produced. Separately confirmed the prose's unreachability claim is true: mutating `_vacates` and re-running 300k randomised walks changed the emitted order in 0 plans and made 0 applicable plans inapplicable. Scripts: scratchpad/rev-inv/mutcheck.py and scratchpad/rev-inv/probe_softdelete.py.

---

## 7. [LOW] "unchanged behaviour, deliberately" is measurably false for a plan holding both a chain and a cycle — the leftovers are moved to the end of the list, not left in place

- **File:** `src/pinakes/pairing.py`:597
- **Raised by:** `agent-ad491810b66d6175c.jsonl`

**Claim.** The comment at line 597 says the cyclic actions "go out in their original relative order — unchanged behaviour, deliberately — so a swap fails at its first write exactly as it does today". Relative order among the leftovers is preserved, but `ordered.extend(actions[index] for index in sorted(remaining))` at line 600 appends them AFTER every emitted action, so their absolute position moves and strictly more of the plan is applied before the crash. `_apply` commits per action, so a mixed plan that previously left the index untouched now leaves it half-migrated. A future reader relying on "unchanged behaviour" for the cycle class would be wrong. Second, latent half: that tail is emitted in INDEX order, not dependency order, so an action merely downstream of a cycle can be placed before the leftover that frees its path. I could not turn that into a distinct failure — in 500k walks every leftover set was a true cycle and the plan crashed either way — so it is latent rather than observed, and it becomes live the moment the deferred cycle case is settled by any means other than refusing the whole plan.

**Failing input.** One plan containing both a rename chain (D0..D2 at docs/f0..f2.md each moving to the next name, sidecars travelling) and a two-file name swap (S1 at docs/s1.md and S2 at docs/s2.md exchanging names).

**Evidence.** scratchpad/rev-inv/structured.py, n=3 chain + swap. Pre-fix order: crash at action 0, `UNIQUE constraint failed: documents.path @ Adopt(D0 -> docs/f1.md)`, rows after crash = all five documents at their ORIGINAL paths, nothing committed. Post-fix order: crash at `Adopt(S2 -> docs/s1.md)`, rows after crash = D0 at docs/f1.md, D1 at docs/f2.md, D2 at docs/f3.md — the entire chain committed — with S1/S2 unmoved. Same for n=2 and n=5. Both runs exit on an uncaught IntegrityError, and a re-run after the user resolves the swap still converges, so this is a documentation defect rather than a data defect.

---
