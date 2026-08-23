## A document's version stamp is the one claim in it nothing can check

`docs/GUIDE.md` opened with *"Every command here was run against 0.2.0 (20260728 16:40)"* and was
published, unchanged, for twenty-six releases. Nothing was broken by it and no gate could see it:
`./check.sh` proves the release *sequences* agree across five documents, `mkdocs --strict` proves
every link resolves, and `tools/template_drift_gate.py` proves the template matches its archive —
**none of them reads a sentence claiming a command was run.**

The stamp is not a small lie. It is the sentence a reader uses to decide whether to trust the other
eight hundred lines, and it was wrong in the direction that costs most: it claimed *more*
verification than had happened. Nine output blocks had drifted behind it, and the two most
misleading were the ones a reader would act on — a euro estimate quoted 30% high, and three separate
statements that only one surface in Pinakes can spend money when `pnk ask --deep` had been the
second for four weeks.

**The pattern is that a stale doc rots fastest exactly where it was most specific.** Prose survives
a release; a quoted output block does not, because it pins a number, a version string and a wording
all at once, and any one of the three moving falsifies it. Nine blocks drifted while the paragraphs
around them stayed true. That is an argument for keeping worked examples — they are what catch the
drift — and against ever writing one without a way to re-run it.

**Two things this pass could not do, and said so rather than faking.** The paid `--deep` transcript
would cost real money to reproduce, so it is kept and labelled as a `0.24.0` run with the one figure
that has since moved named explicitly. And re-running the two-KB link walkthrough would change every
ULID in the section without making a sentence truer. **The distinction that matters is between an
output nobody re-ran and an output nobody re-ran *and did not say so*.** Only the second is a defect.

**A near miss worth recording.** The first draft of the label said the paid block's command "is now
quoted at €0.20" — the figure measured at `-k 2`. The block's own command passes no `-k`, and at the
default passage count it quotes `€0.21`. One cent, and the wrong kind of wrong: two invocations
collapsed into one number, which is precisely the invented precision the label existed to prevent.
Caught by re-reading the command the block actually shows instead of the one measured beside it.
