## S19, measured twice independently — and the row that disagreed is the useful one (20260826 07:20)

S19 said `pair()` emits an inapplicable order for renames that are not cycles. Until today that was
**an argument from reading `pairing.py`**, and the plan said so in a provenance paragraph. Both
halves have now been run: the coder reproduced it end to end, and the planner re-drove `pair()` from
a **separately written probe** rather than checking the coder's output.

**MEDIUM — three rows matched exactly, and the fourth differed for a reason worth keeping.** On
cycle, non-cycle-two and chain-of-three the two probes emitted identical action sequences. On
*rename onto a free name* one probe reported `RefreshMetadata` and the other `Skip` — because one
construction changed the untouched document's sidecar hash and the other did not. **The row is green
either way and the disagreement changes nothing**, but recording *why* two measurements of "the same
thing" differ is what makes the three that agreed worth anything. A silent reconciliation would have
left a reader unable to tell agreement from coincidence.

**MEDIUM — the control was designed to kill the plausible-but-wrong fix, not to demonstrate the
bug.** The obvious pinning case is the two-file shift. The coder argued for a **chain of three**
instead: its valid order is *strictly reverse*, so no accident of path-sorting can produce it, and
**a fix that merely reorders two adjacent actions passes the two-file case while failing this one.**
That is the difference between a test that proves the bug existed and a test that constrains the fix.

**LOW — and it converted a build-order row from under-scoped to scoped.** Before the measurement,
*"make swaps work"* was a defensible reading of S16. After it, the classes are distinct and
measured: **ordering the applicable plans fixes the whole chain class; cycles need a temporary path
and a separate mechanism.** The plan now says so, and asks that **the cycle case be shown still
failing** in the commit that fixes the chain — otherwise *"swaps still crash"* becomes *"swaps are
fixed"* in the next summary, which is precisely how S17 was recorded as open after being cured.
