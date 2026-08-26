## A ratio over a growing denominator, and a stamp that should never have been read twice (20260826 11:51)

Two conventions were relying on someone being careful. Both now say what to run instead.

**MEDIUM — three figures I put into `docs/BUILDING.md` were wrong within four hours, and the second
reason is the one that matters.** The rule cited *207 of 248 changed files opened, 83%, 90% on
multi-pass increments*. The first reason they moved is ordinary: the measuring tool's scan could not
match an **extensionless filename or a `.lock`**, so `Makefile` and `uv.lock` were reported as
*opened by nobody* on every increment that touched them — a gap section confidently naming what the
tool cannot see. Fixed by its author; the figures became 211, 85%, 92%.

**The second reason has no fix: the corpus is alive.** It is this repository's own transcripts, and
the sessions measuring it are writing into it while it is measured. `--measure` moved a published
figure from **96.1% to 95.8% between two runs with no code change at all**. **A ratio over a growing
denominator has a shelf-life measured in minutes.** So the paragraph now quotes the *command* —
`python3 tools/review_ledger.py <increment>` — and no percentage, which is the same conclusion
`docs/VERIFICATION.md` reached the same morning by a different route: two sessions dictating counts
from two trees, neither containing the other's change.

**The general form, arrived at from opposite ends by two sessions in one morning:** *a stamped
measurement that no longer matches the tree is **dated**, not false; a restated count is simply
wrong.* One of us met it by dictating counts from two trees, the other by watching a corpus grow
under a measurement. **That it was reached twice independently is better evidence that it is a
property of working here than either route is on its own.**

**LOW — and the counterexample keeps the rule honest.** The stamp gate proposed for
`tools/fragments.py` compares a heading's timestamp to its own filename. **Both values are inside
the file**, so it is immune to everything above: no corpus, no denominator, nothing to grow. It is
the exception that shows what the rule is really about — not *never state a number*, but **never
state a number whose subject can move without the document knowing.**

**MEDIUM — and the convention that gate will enforce did not exist in writing.** `retro.d/README.md`
showed a heading with a timestamp and never said where the timestamp came from, which left
*name-early, head-late* looking like a legitimate workflow and made a **tolerance** look reasonable.
It is now written: **the heading's stamp is a *copy* of the filename's prefix — one reading of the
clock, written twice.** That makes exact equality correct by construction rather than by taste, and
it was a coder's question about tolerance that exposed the gap: **a gate cannot be specified against
a convention nobody wrote down.**
