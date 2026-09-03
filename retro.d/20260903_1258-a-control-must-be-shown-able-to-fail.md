## A control must be shown able to fail (20260903 12:58)

**HIGH — and it recurred an hour and a half after the same class was written down, by the same
session, in this tree.** Row 8's symlink guard reported a symlink to a real *directory* as
*"resolves to nothing … its target is missing or the link loops"* — false on both counts, because
`is_file()` is False for a directory target exactly as it is for a dangling one.

The part worth keeping is not the bug. It is that **a control had been written against precisely
this risk, and it could not fail.** Its docstring said so out loud:

> Without it, `unresolvable` could be populated by `is_symlink()` alone — which would report every
> aliased document in a KB that uses links deliberately, and `sync.py` already has a branch
> explaining that `docs/alias -> docs/real` is a supported shape.

The shape named there is a link to a **directory**. The shape the body built was
`alias.md -> elsewhere.md`, a link to a **file** — which passes `is_file()` and therefore never
reaches the `is_symlink()` branch at all. The assertion held for the correct guard and the broken
one alike. Measured, not argued: with the fix reverted, the new directory-symlink test fails and
**the other six symlink tests stay green**, which is the control demonstrating its own vacuity.

**This is [[a-fixture-named-for-a-scenario-it-did-not-build]] again.** That fragment is stamped
**20260903 10:24 UTC**; the commit carrying this instance is `6226b09`, **20260903 12:02 UTC**
(both read with one instrument, `TZ=UTC git log --date=format-local:`, because `format:` renders
in the committer's own offset and mixing the two silently compares different clocks). That fragment's rule — *does the fixture
build the state the name describes?* — was already written, already in the tree, and did not
transfer, because the second instance did not look like the first: this was a **control**, added
deliberately against a named risk, in a test file that had just been reviewed. Believing a control
is the failure mode; writing one is not enough.

**The repository already owns the remedy in another register.** `tools/batteries/README.md`
requires killing one known-catchable mutant before believing a battery — *"a run with no kills is a
broken harness, not a clean bill."* A control is the same instrument: it asserts that something
does **not** happen, so nothing about its green tells you it was ever wired to the code. **Revert
the guard and watch the control go red**, or it certifies nothing. That is the same test as
*"pinned by test X" is a claim about a failing test*, applied to the negative case, where it is
easier to skip because there is no fix to revert — you have to reach for the *broken* version on
purpose.

**And it happened a third time in the same increment, caught by the mutation pass rather than by
reading.** The battery row that shrinks the closed set — drop `"pdf"` from `SOURCE_TYPES` — was
pointed at the control written to catch exactly that, `test_every_valid_source_type_is_still_accepted`.
It **SURVIVED**. The control's loop is `for source_type in SOURCE_TYPES:`, so it iterates the
constant the mutant shrinks: remove a member and the loop simply stops testing it.

The diagnosis matters more than the fix, and `tools/batteries/README.md` § *Reading a SURVIVED row*
names both possibilities: the row is a claim about a **pair**, and either half can be wrong. Here
the coverage was fine and the **witness** was wrong — with the mutant applied,
`tests/test_chunk.py` goes red at line 745, because
`test_source_types_names_every_value_source_type_can_return` derives the expected members from
`source_type()` over real filenames and never reads the tuple. So the repair was the selector, not
a new test.

Three instances, one shape: **an assertion that draws its expectation from the thing it is
checking can only ever agree with it.** A control looping over the constant, a fixture built from
the code's own notion of the state, a docstring describing intent beside code that does something
else. None of them can fail, and all three read as coverage. The only instrument that found any of
them was one that tried to *break* the code and watched what did not notice.
