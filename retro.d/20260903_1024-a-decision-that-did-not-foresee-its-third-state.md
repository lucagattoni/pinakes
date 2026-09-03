## A decision that did not foresee its third state (20260903 10:24)

**MEDIUM — an answered decision can still be short a case, and building it is what finds out.**
D-37 was answered 20260825: *option E — gate the move hint on the orphaned sidecar, **not** the
mint count.* It is a clear instruction and it is right. Enumerating the states it applies to,
before writing anything, turned up **three** where the decision reasons about two:

| on disk after the change | orphaned sidecar | id minted | hint should fire |
|---|---|---|---|
| file and sidecar both deleted | no | no | **no** — this was the S6 false positive |
| file moved and edited, sidecar left | yes | yes | yes |
| **only the file deleted, sidecar left** | **yes** | **no** | **yes, but nothing was minted** |

Option E fixes *when* the hint fires and is silent on *what it says*, so the third state passed the
new gate and went on printing *"so a new id was minted"* — false. The wording is implementation, so
it was mine to take, and the sentence now reports the state observed rather than the conclusion
inferred. **A decision that settles a predicate has not thereby settled the sentence the predicate
prints.**

**The same shape, twice in one increment.** S8 records `-k -1` and `-k -100`. Enumerating instead
of trusting the record found `-k 0`: the width is read as `limit or manifest.retrieval.final_k`, so
a falsy `0` silently meant *use the default* — the user asks for nothing and receives ten passages.
A third arm of a defect whose record listed two.

**The transferable move is the table, not the finding.** Both came from writing out every state the
mechanism can be in and checking each against the rule, rather than checking the rule against the
states someone had already written down. **A recorded finding enumerates the cases its finder
happened to try, and reads exactly like a complete list.**
