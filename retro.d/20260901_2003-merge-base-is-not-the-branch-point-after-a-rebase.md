## `git merge-base` is not the branch point after a rebase (20260901 20:03)

**Four agents in one review pass raised the same false finding, and every command each of them ran
was correct.** A comment in a mutation battery said the live `retro.d/` directory *"was 4 files when
this was built and all 4 already passed"*. Two independent lenses reported it false; two independent
refuters, told to refute, each confirmed it false instead. One went further and re-ran the gate at
the merge-base to produce a measured count of 12. The sentence was true.

**The branch had been rebased.** `git merge-base HEAD origin/main` returned `8540e27`, and everyone
read that as the branch point. The reflog says otherwise:

    …@{8}: branch: Created from main      -> 0aea036
    …@{2}: rebase (finish): … onto 8540e27be…

`0fd4a86`, the commit that wrote the sentence, has author date `2026-09-01T08:19`. `8540e27` has
author date `19:00` — **eleven hours later**. The merge-base was a commit that did not exist when
the sentence was written, and eight retro fragments landed on `main` during those eleven hours. At
`0aea036`, `retro.d/` holds exactly four fragments and the gate passes all four.

**A rebase moves the merge-base forward and leaves no trace in the commit graph.** After it, the
merge-base names *where the branch was replayed onto*, never where its work began. Any claim of the
form "when this was written, the tree held X" must be measured at the reflog's `branch: Created
from`, or at the authoring commit's own parent — never at `merge-base`.

**What makes this worth recording is not the wrong number, it is the four-agent agreement.** The
finder and the refuter are supposed to be independent, and they were: they ran different commands in
different orders. They agreed because they shared a *premise* nobody stated — that merge-base is the
branch point — and no amount of independent re-measurement can catch an error in the population you
both selected. This repository already carries the rule: **a claim resting on a set you selected or
an instrument you chose must state the selector.** Here the reviewers failed it and the author had
not: the sentence names its own selector, *"when this was built"*, and the reviewers substituted a
different one.

**The cheap defence is to make the selector executable.** The sentence now reads with its sha in the
neighbouring comment, so the next reader is told which tree to measure rather than left to infer it.
