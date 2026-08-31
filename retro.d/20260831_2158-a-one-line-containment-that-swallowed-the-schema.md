## S16's residue — "containment is one line", and the line was too wide (20260831)

**The review was right about the defect and wrong about the fix, and the two are easy to accept
together.** Two independent adversarial agents found the same residue on the S16 branch: ordering a
rename chain creates a dependency between actions that the executor knows nothing about, so one
member failing to index leaves its row in place and the next action collides. Both wrote the same
remedy: add `sqlite3.IntegrityError` to `_apply`'s except tuple. One of them called it "containment
is one line", which it is.

It is also one line that swallows `chunks(doc_id, ordinal)`, `nodes(kind, key)`, the `links` and
`edges` primary keys, and the CHECKs on `documents.state`, `links.origin` and `nodes.kind`. Each of
those fires only when Pinakes itself is wrong. `_apply` records a failure and **continues** — so a
bare catch would file an invariant breach as one document's problem and let the run report success
around it, which is the exact silent shape `docs/INVARIANTS.md` exists to prevent. **The finding's
severity was HIGH and its proposed fix would have opened a second hole to close the first.**

**The third option was not in the branch, not in the plan, and not in either review.** It came out
of asking one question the reviews had not: how wide is `IntegrityError` here, actually? Reading
`store.py` answered it, and `exc.sqlite_errorname` — measured on the interpreter rather than
remembered from the docs — turned out to separate `SQLITE_CONSTRAINT_UNIQUE` (2067) from
`SQLITE_CONSTRAINT_CHECK` (275) and `SQLITE_CONSTRAINT_PRIMARYKEY` (1555). That made a narrow catch
cheap, so the decision put to the user was three options rather than the two the branch offered. **A
review's recommended fix inherits the framing of the review, and a reviewer who has just proved a
defect is not the least biased party about its remedy.**

**The battery found the hole in my own test, which is the part worth keeping.** The witness for the
narrow behaviour had three negative cases — a duplicate primary key, a CHECK breach, a
`chunks(doc_id, ordinal)` collision — and it passed. It also passed with the `sqlite_errorname`
clause deleted, because **all three fail on the column substring alone**, so the clause the whole
decision rests on was never exercised. The case that separates them is
`NOT NULL constraint failed: documents.path`: the right column under the wrong error code. Three
plausible negative cases agreeing with each other is not coverage — they have to disagree about the
clause under test, and nothing but writing the mutant asks whether they do.

**The exit code came from the adversarial pass, not the build.** Catching an exception trades a
crash for something quieter by construction, so the question "does `pnk sync` still exit non-zero?"
had to be asked separately. It does — `report.ok` is `not self.failures` — but nothing pinned it,
and a later edit to `ok` could have turned a contained failure into a silent success with every
test green. It is asserted now.
