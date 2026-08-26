## Every review pass rebuilds the map, and the fourth one pays most for it (20260826 07:40)

Measuring where adversarial review spends its tokens, and building the tool that carries the answer
forward, produced four things worth keeping. Three are about this repository's review loop; one is
about measurement itself, and it is the one that generalises.

**The cost is re-derivation, and it scales with the pass rather than away from it.** Over the 910
subagent transcripts here, **35.6% of a later review pass's raw tokens go to turns whose only file
access was a file an earlier pass over the same increment had already opened** — against **3.0%**
for turns that opened something new. 96% of what the median later pass opens was already opened by an earlier
one. And the share **rises with how expensive the pass is**: 40.1% over the 69 passes costing
more than 5M raw tokens. The reason is arithmetic rather than psychology — a file read at turn 6 of
a 90-turn pass is re-transmitted by all 84 turns after it, so the earlier and longer the pass, the
more a redundant read costs. *Lesson: the expensive part of a review pass is not the reviewing. It
is standing the map back up, and the passes best placed to find something rare are the ones paying
most for ground that was already walked.*

**What a pass re-derives is not mainly file content, and counting tool calls said otherwise until
the labels were read.** Reviewers here overwhelmingly *run* things: their own detached worktree,
their own scratch KB, `pytest` inside it, a throwaway probe script, then `git worktree remove`. On
one increment, **seventeen separate passes wrote and ran `uv run --frozen pytest
tests/test_pairing.py`**, and **seven independently discovered that `timeout` is not installed on
this machine** — each paying full price for the discovery. *Lesson: the carry that matters is the
probe, not the file list. A map of what was read helps a reader; a command that already ran helps a
worker.*

**And the coverage hole nobody was looking for.** The tool reports, per increment, the changed files
no pass ever opened: **211 of 248 across the corpus (85%; 92% on multi-pass increments)**. The
misses are not noise. `src/pinakes/__init__.py` — where `__version__` lives — was never opened
across the **41** passes over `20260823_0718-mutation-batteries`. And **no review pass in this
corpus has ever opened the `changelog.d/` or `retro.d/` fragment its own increment wrote**: the
files that carry this project's memory forward are the ones its review procedure never reads.
*Lesson: "reviewed until clean" is a claim about what the passes looked at, and until something
lists the diff beside the reads, nobody knows what that was.*

**The method lesson, which is the one that generalises: a mutant that survives is a question, and
the answer was that my reasoning was backwards.** The battery's first run left one row alive — the
mutant that flipped path normalisation from last-match to first-match. The test it named asserted a
property the fixture never created, so the mutant was unobservable. Answering *why* it survived
found that the shipped rule was the wrong one: last-match reduced `tests/demo-kb/docs/x.md` to
`docs/x.md`, which is not a file, and the tracked-file screen then discarded it. **102 tracked paths
are shaped that way.** The written justification for last-match — that a branch directory might
contain `docs` — was simply false: a branch is `20260807_2143-docs-audit-findings`, where `docs` is
bounded by hyphens and the `/docs/` marker never matches it. Every gate was green throughout.

Two corollaries, both earned in the same hour:

- **Then measure the fix rather than asserting it.** The natural write-up was *"every review pass
  that read the demo KB vanished from the map"*. Checked: **28 of 49,000 read targets normalise
  differently, 27 of them recovered, and the published shares do not move at all.** Real, silent,
  and small. The defect class deserved the fix; the sentence deserved the smaller number.
- **A number in a docstring is a claim with no gate on it, so give it a command.** `--measure`
  re-derives every figure in this tool's own docstring, under the key printed beside it. Two of
  those figures moved during the build, when the two defects above were fixed — and updating them
  cost one command instead of one act of remembering. This is the direct answer to the failure
  recorded in [`tools/review_pass_gate.py`](https://github.com/lucagattoni/pinakes/blob/main/tools/review_pass_gate.py),
  which shipped three measured claims that a change made in the same increment falsified.
