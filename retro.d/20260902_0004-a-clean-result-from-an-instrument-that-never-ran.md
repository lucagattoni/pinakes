## A clean result from an instrument that never ran (20260902 00:04)

Twice within twenty minutes, two unrelated instruments returned a clean result over a population
neither had reached.

The first was this increment's eighth adversarial pass. It returned `verdict: CLEAN, findings: []`.
Its five lenses had all been killed by a session limit before doing any work: `agents_done: 0,
agents_error: 5`. The verdict was not wrong about its input — my own script returns CLEAN when the
finding list is empty, and the list was empty. It was wrong about what an empty list meant. Passes
5, 6 and 7 had each found a false sentence, so this CLEAN would have ended the loop. Reviewing the
same commit by hand instead found two more false sentences, both written by me in the pass before.

The second was a probe I wrote minutes later, asking how many `retro.d/` fragments have ever carried
a second `## ` heading. It read each fragment at the last commit that *touched* it. For a fragment
consumed into `docs/RETROSPECTIVES.md` at a release, the last commit that touched it is the one that
**deleted** it, where `git show <commit>:<path>` yields nothing — so it examined 15 of 127 and
skipped 112 in silence. It reported `0 of 127`. Reading each at the newest commit where the file still
existed reports `2 of 127`, and those two turned out to be exactly the evidence a peer's open
question needed.

**The standing rule here covers the step after this one.** It says a null result carries no
information until the selector is shown able to fire, and that once the selector is proven a null
becomes a finding. Both selectors here were fine. `grep`ping for a second heading works; an
adversarial lens works. What neither run established is that the instrument ever **reached** its
population — a different question from whether it can fire, and the one that failed.

So the number to demand is the denominator, and it is never the default output. `agents_done`
against `agent_count`; `examined` and `skipped` against the list you started from. I had to add both
by hand, and in both cases the honest count is what exposed the result. Until an instrument says how
many items it actually looked at, it has not reported a result — because `CLEAN, 0 findings` and
`0 of 127` are precisely what a real clean run looks like, and nothing in either output distinguishes
the two.
