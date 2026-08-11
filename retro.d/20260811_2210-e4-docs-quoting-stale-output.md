---
category: lesson
---

## The same GUIDE block quoted a retired sentence twice — so the second time it became a gate

E1 rewrote `pnk search`'s escalation notice and left `docs/GUIDE.md` displaying the sentence it had
just replaced. Its retrospective recorded that nothing in the repo could have caught it. **E4
rewrote the same sentence and left the same block stale again**, caught only because someone grepped
for the old wording before shipping.

**Why every existing check is blind to it.** The prose is well-formed. Every link resolves.
`mkdocs build --strict` is green. `tests/test_verification.py` checks that named tests exist, not
that quoted output is current. A fenced block showing a previous build's output is *correct
Markdown describing a program that no longer exists*, and nothing in this repo reads it as anything
else.

**The checkable half is the negative one.** Diffing a fenced block against real output would need
the command, its models and a corpus. "Every printed constant must appear in the docs" is simply
false — most should not. But **a sentence this build can no longer print must appear nowhere**, and
that is a grep. `tests/test_docs_quote_the_shipped_sentences.py` holds the retirement list, one row
per retired sentence with what replaced it; retiring a sentence is a deliberate act, so adding the
row is part of it.

**Two things that make the gate honest rather than decorative.** It searches `src/` as well as
`docs/`, because a retired sentence surviving in a docstring is the same defect one layer in — and
this project's docstrings are where its reasoning lives. And it was run against the pre-E4 tree,
where all four rows fail: a gate never observed failing is a gate nobody has tested.
