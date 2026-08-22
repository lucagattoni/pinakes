## Verify the remedy, not only the finding (20260822 07:25)

`docs/BUILDING.md` § 5 already says *a fix applied under review inherits the review's confidence and
none of its scrutiny*. This is its sibling, and it is about the review pass rather than the commit
after it: **a correct finding arrives with a proposed remedy attached, and the remedy is the half
nobody re-checks.** The finding survives scrutiny; the remedy rides in behind it.

Two instances the same night, in two sessions working concurrently, each caught only because the
second pass argued with the *fix* rather than stopping at the defect:

- **A remedy that would have manufactured a false green.** A classify bug was real and confirmed. Its
  proposed fix would have made the check report success on input it had never examined — a repair
  that removed the symptom by removing the observation.
- **A remedy that was right and unbounded.** STATUS's *Published on PyPI* list is legitimately short
  between a release landing and its verification, because a claim about the index is held back until
  it is verified *from* the index. Exempting that sequence from the release-order gate's agreement
  check was correct. Exempting it **without a direction** was a hole with a docstring: no input could
  distinguish a working exemption from a missing one. It became *may lag, never lead* — the list may
  fall behind every other sequence and may never name a release the CHANGELOG has not heard of.

A review culture that re-checks only findings ships both of these at full confidence. Both were
defensible, both were proposed by the agent that had just been right about something, and that is
exactly what makes a remedy hard to doubt.

**The cheap test:** state what input would look different if the remedy were absent. If none exists,
the remedy is unfalsifiable and the test written for it will be a tautology — the same failure E7
recorded, where a guard whose input is built by its own validator cannot be shown to guard anything.

**A coda from the concurrent session, worth keeping beside this.** The night's most serious defect —
`pnk serve` raising `ModuleNotFoundError` on every fresh install of every published version, from a
lower-bound-only dependency pin that 37 `--frozen` CI invocations never resolve — was not found by a
test, a gate or a review. It was found by someone asking *what should we build next* and installing
the product to answer it. `docs/BUILDING.md` warns that a test seam defines a region no test reaches;
here **the region no test reached was the product itself.** Reproduced independently in both
sessions before it was written down.
