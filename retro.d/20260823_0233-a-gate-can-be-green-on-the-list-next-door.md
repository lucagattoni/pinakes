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

## A constant bounds the damage; a relation catches the start

The first fix made the row a sequence with permission to lag, bounded by `MAX_VERIFICATION_LAG`.
That is a real check and it would have caught both drifts — *eventually*. Counting the history says
how late: 29 commits sat in the window where the row was behind and the bound was silent, and both
drifts passed through it on the way to being caught.

The bound is a constant, and the thing it approximates is a **relation**. The row may lag the
release documents because an entry waits for index verification; it may not lag the *other list
recording that same verification*, because there is no interval during which one is true and the
other is not. Written that way the rule needs no tolerance at all, and the measurement bears it out:
zero false positives in 67 commits, red at the first commit of the drift rather than the eleventh.

**The general form:** when a bound needs a tolerance, ask what the tolerance is standing in for. A
number chosen to be loose enough for the legitimate case is by construction also loose enough for
some illegitimate ones. If the legitimate case can be *named* — here, "both lists are waiting on the
same verification" — the relation that names it is both tighter and simpler than the number.

**Keep the constant anyway.** It is not redundant: it catches a drift in which *both* lists are
forgotten together, which the relation cannot see. Two checks over one sequence, catching different
failures at different moments, is the correct outcome — and the test that exercises the deep drift
now asserts **both** fire, so neither can be deleted while it stays green.
