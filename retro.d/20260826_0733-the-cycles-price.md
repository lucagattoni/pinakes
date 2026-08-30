## The cycle's price, found by building the fix and backing it out (20260826 07:33)

**MEDIUM — the obvious remedy for a defect had a cost nobody had counted, and counting it required
writing the code and throwing it away.** S16's cycle class (`a ↔ b`) looks like it wants a clean
refusal: `pair()` raises before anything is applied instead of emitting a plan that crashes halfway.
The coder built exactly that, it worked, and **backed it out** — it breaks five committed tests, and
three of them are guards that exist *only while a cycle still produces a plan*, including
`test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row`, which pins **the silent-loss
shape S2 exists to prevent** and can only observe it by watching a plan be applied and fail.

**So the cycle's remedy is not "add a temporary path". It is "add a temporary path *and* replace
three of S2's guards".** A build-order row reading *make cycles work* would have under-scoped it
exactly as *make swaps work* under-scoped the chain — the same error, one class along, and it would
have been discovered mid-increment by someone with a fix already written.

**The judgement worth keeping is the refusal to land it.** Refusing a cycle cleanly is a **behaviour
decision** costing S2 coverage, not an implementation detail of an ordering fix, so it did not belong
in that increment however well it worked. Backing out working code because it answers a question
nobody asked is harder than shipping it, and it is what the *never assume what the plans have not
decided* rule actually costs when it bites.

**LOW — and one of the three guards contradicts itself in a way that will block precisely the person
who settles the cycle.** Its docstring: *"The sync's own outcome is deliberately not asserted… what
this test pins is that no live document loses its row, which must hold **however that defect is
settled**."* Its body: `contextlib.suppress(sqlite3.IntegrityError)`, which **pins the exception
type**. Settle the cycle by raising anything else and the test fails, with a docstring promising it
would not. **A test's intent and its implementation can disagree, and the docstring is the half that
gets read** — nothing checks the other one against it.
