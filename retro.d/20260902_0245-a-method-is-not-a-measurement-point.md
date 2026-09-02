## A method is not a measurement point, and `--all` is not a corpus (20260902 02:45)

I corrected a count by naming a better *instrument* and thought that finished the job. It did not.
The first version of row 14 said **116 fragments, exactly one**, measured over the live directory and
stated as a fact about the corpus. The correction replaced it with **129 paths, 239 versions**, taken
from the object store — the right instrument, and the row said so: `git rev-list --all --objects`.

Re-checking my own branch before landing it, that number reproduced against nothing. `--all` is not a
corpus. It is *every ref any branch happens to hold at the instant it runs*, so it counted unlanded
work on my branch and on a peer's, and it had drifted to **132 paths / 243 versions** inside an hour —
without a single fragment being written to `main`.

The tell was visible in the row and I had not looked: **three denominators for one directory**. Row 14
said 129 and, four sentences later, *10 of 126*. Row 17 said 131. One of those was all-refs, one was
`main`, one was a moment. A row whose whole argument is that a count must state its population was
carrying a numerator and a denominator drawn from two different ones.

Pinned to `origin/main` at `7751f96`, landed history only, everything reconciles: **126 retro.d paths,
233 versions**, `changelog.d` **177**, combined **303**. Both of row 14's denominators become the same
126. The conclusions all survive — still exactly **two** two-heading fragments, still the same two
files, still `10 of 126` unstamped at **7.9%**, still `0 of 52` unprefixed stems beginning with any
digit. Only the totals were wrong, and only because they had no anchor.

**The rule this leaves:** a measurement is reproducible when it states an instrument *and* a point —
a ref and a sha, not `--all` and not `HEAD`. Prefer the landed history as the population, because it
is the only one that does not change when someone else commits. And when a single row carries two
numbers about the same set, check they came from the same run before checking they are right: I
verified the instrument and never verified that the two halves were counting the same things.

The same defect, three times in one day, each time caught by someone re-running rather than re-reading.
