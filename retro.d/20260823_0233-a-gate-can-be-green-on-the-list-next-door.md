## A gate can be green because it is reading the list next door

The *Published versions* row drifted four releases while a check named after it ran green on every
commit. The check was real, the row was wrong, and both statements were true at once: the gate's
sixth sequence reads the *Published on PyPI* prose, and the row is a different list forty lines
down in the same file, under the same heading.

**What made it invisible was the naming, not the code.** A reader auditing "is the PyPI list
checked?" finds a sequence called *the Published on PyPI prose*, sees it green, and stops. Nothing
in that report says which of the two lists under that heading it read. The lesson generalises past
this file: when one document holds two lists of the same thing, a gate covering one of them reads
as covering both, and the *coverage* claim is what needs the test — not the ordering.

**The corollary for `within`.** Scoping a pattern to a region introduces a failure the line-anchored
sequences never had: the anchor can match somewhere else. Zero matches is safe, because an empty
sequence trips the floor and the floor's message fits. Two matches is not, because reading the first
is a silent choice — the anchor deciding for itself which region it meant, which is the
"derived, never declared" mistake this module refuses everywhere else, one layer down. So it is a
refusal, not a heuristic.

**And a fixture proves scoping only if it would break without it.** The tree these tests build
writes version numbers *after* the enumeration and in descending order, mirroring the real cell. A
`within` that stopped scoping reads them into the sequence and the tests go red. Without those
trailing numbers every test here would pass over a bare unscoped pattern — the fixture would be
asserting the thing it was built to assume.

**On the floor: an exact count is declared, and still wrong here.** Setting the floor to the 41
versions present would be a literal, not a derivation — but `check()` skips a sequence whose floor
failed, and `check_membership` then skips it too, so deleting one release would report *"the pattern
has stopped matching what it names"* and never say which release went missing. The precise
diagnostic is worth more than the redundant one. Declared-not-derived is about where a number comes
from; it does not settle what the number should be.
