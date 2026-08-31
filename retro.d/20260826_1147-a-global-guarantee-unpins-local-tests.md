## S16/S19 — A fix that enforces a property globally unpins every test that asserted it locally (20260826 11:47)

**HIGH — the finding is about the mutation harness, not about renames, and it is the most portable
thing this increment produced.** The ordering pass makes *"no action writes a path a live row still
holds"* true of **every** plan. Two mutants in `src-pinakes-pairing.toml` died on `main` to that
property being **locally** violated — a `SoftDelete` landing after the `Adopt` it belongs before —
so both became invisible the moment the property was guaranteed globally. **Neither
`--check-anchors` nor `tests/test_batteries.py` can see this happen**: the anchor still resolves and
the `kills` selector still names a test that exists, which is the entire contract those checks hold.
The generalisable rule: **when a change makes a property hold by construction, every test that
asserted that property by observation stops discriminating** — and a battery is exactly a corpus of
such tests. Run the battery after a change of that shape; the anchors resolving is not a substitute.

**The one that had nothing underneath it was still worth the run.** *Inverted guard* was killed by
eleven other tests: the battery was right about the risk and wrong about the witness, which
`tools/batteries/README.md` already names. It was repointed **and renamed** — its old name described
the in-place half, which the ordering pass now repairs, and what still dies is the other branch.
**A row's name is a claim too, and it rotted without its anchor moving.**

**HIGH — the one that did have something underneath it was an untested route to breaking ULID
permanence.** *An orphaned sidecar counts as a claim* survived on the branch and **nothing in 2 212
tests saw it**. Reading why found a second reader of `claimed_by_id` that the ordering had been
standing in front of: a file with **no sidecar of its own**, whose index id turns up claimed
elsewhere, is read as *"this row's identity has moved"* and its path is left to be minted fresh. Let
an orphaned `.pnk.yaml` count and that fires on an untouched document sitting beside it — **re-minted
under a new id, the original retired, every inbound `pnk://` link dead**. That is
[`docs/INVARIANTS.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/INVARIANTS.md)'s first
invariant, reachable with the user doing nothing wrong, and it had no test. The new one asserts the
action **kind**, not the order — the half a global ordering guarantee cannot repair — and was watched
red under the mutant first: `Skip` becomes `Rename`.

**MEDIUM — the battery README's own remedy has a false-positive mode.** It says: before believing a
survivor, run the mutant against the whole suite. The whole suite contains `tests/test_batteries.py`,
whose anchor check fails on **any** edit to a battery target — so a mutant that dies only to that is
**not killed**, and a run reporting `1 failed, 2 221 passed` reads as a clean bill. `tools/mutate.py`
is blameless: it runs only the named selector and its report was honest. **The defect was in the
advice, which makes it a one-flag fix** (`--ignore=tests/test_batteries.py`) rather than a redesign.

**MEDIUM — working code was written, tested, and backed out, and that was the right call.** Making a
rename cycle raise cleanly from `pair()` is tidier than letting it fail at the first write: nothing
is applied, so nothing is half-applied. It broke five committed tests, and **three of them are guards
that exist only while a cycle still produces a plan** — including one pinning the silent-loss shape
the previous increment exists to prevent, which can only observe it by watching a plan be applied and
fail. **Refusing the cycle is a decision about behaviour that costs coverage of a different defect,
not an implementation detail of an ordering fix.** The price is now recorded where the next person
reaching for it will start from it: not *"add a temporary path"* but *"add a temporary path **and**
replace three guards."*

**LOW, and a lesson about test seams rather than about this code: a stability test that could not
reach the thing it tested.** The ordering pass returns early when a plan has no constraints — so the
test that pinned *"a plan needing no constraint comes out unchanged"* never entered the topological
sort at all. A mutant emitting ready actions in arbitrary order therefore changed the output of every
constrained plan and survived that test **and the whole suite**. **A test named for a property is not
evidence it reached the code implementing it**; the repair was a plan carrying a constraint *and*
untouched actions beside it, so the sort runs and the unconstrained actions are observable.

**LOW — `ty` caught two typing defects `pyright` strict passed**, both in new test code, both real
(an attribute read off a union member that does not have it). `check.sh` calls `ty` a fast pre-check
and *never* the gate, which remains right — but on this increment it was the only checker that saw
them, and that is worth one line in the record rather than a re-litigation of the policy.
