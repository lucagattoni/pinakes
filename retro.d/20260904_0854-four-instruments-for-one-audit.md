## Row 41 — four instruments for one audit, and the fix was already written down (20260904 08:54)

**The audit itself was one afternoon's work. Getting an instrument that could be trusted took four
attempts, and every failure was the audit's own subject turned on itself: a measuring device that
did not contain what it claimed to measure.**

**HIGH — the decisive bug was a rule this repository already states, in a context I did not
recognise as the same machine.** `CLAUDE.md` tells a mutation harness to *clear the module's
`__pycache__` after writing and after restoring*, because CPython invalidates bytecode on
(mtime-to-the-second, size). This audit edits a test file, runs pytest, restores, and repeats —
many times a second — which is precisely that shape. I did not apply the rule, because I was
building "an audit" rather than "a mutation battery". **Two of fifteen sites then returned a
different verdict on repeat**, and one site was reported vacuous by a batch run while three
separate single-site runs called it sound. Clearing `__pycache__` took the instability to **zero of
fifteen**. A rule filed under the wrong noun is a rule you will break.

**HIGH — "still passes with its instrument disabled" is three findings wearing one label, and only
one of them is a defect.** The probe cannot, by itself, tell apart: *(a)* a test whose assertions
do not depend on the injected condition at all; *(b)* a test where the real environment produces
that condition anyway, so the fake is redundant; *(c)* a mis-attributed site, where the probe
disabled an injection and then ran a test that never used it. All three print the same word. Case
*(c)* was my first instrument attributing injections inside **helpers** to whatever test happened to
sit above them. Case *(b)* is real and stayed: a 300-character filename raises `ENAMETOOLONG` on
this machine for real — `NAME_MAX` is 255, measured — so that injection decides nothing *here*,
while the test's own comment records the opposite on CI. **That site cannot be ruled from this
machine at all**, and saying so is the result; picking either answer would have been an invention.

**MEDIUM — the count moved 5 → 3 → 2 across instruments, and only the last one is reportable.**
Every intermediate number was a true statement about a broken measurement. The discipline that
saved it was cheap and mechanical: probe every site **twice** and report only verdicts that agree,
then cross-check the flagged ones by hand. The one genuine finding survived all four instruments.

**MEDIUM — what the audit found, stated against its own trigger rather than against a preference.**
Fifteen injection sites on `pathlib`/`os`/`paths` predicates; **one genuinely vacuous test**, now
fixed. The trigger for writing a general rule was *more than one further vacuous test*. **One is not
more than one, so no rule was written** — deliberately, because a rule invented from a single
instance is the ceremony this repository keeps warning about, and because the honest reading of a
boundary result is to report the boundary rather than round toward the outcome that produces a
deliverable.
