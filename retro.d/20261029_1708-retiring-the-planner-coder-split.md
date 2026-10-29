## Retiring the planner/coder split (20261029 17:08)

**MEDIUM — the split was carrying four things that are not about roles, and deleting the role rules
alone would have taken them with it.** The user's instruction was to remove the distinction
completely; reading what each rule actually did, before deleting it, found these:

| What the role rule was doing | Where it lives now |
|---|---|
| Making concurrent sessions ask each other before writing | **Kept**, with *role* replaced by *task*: ask every live peer for its task and file set, wait, re-check at landing |
| Keeping every increment out of `CHANGELOG.md` and `RETROSPECTIVES.md` (the planner edited them, so nobody else could collide) | **Kept** as the fragment rule, whose own README already gave the real reason: sessions run at once and these are the two files every increment would edit |
| Making a document and the test that reads it change atomically (*content mine, keystrokes yours* existed only because the author and the committer were two agents) | **Kept** as one sentence: a `docs/VERIFICATION.md` row or a counted paragraph a test asserts changes in the commit that makes it true |
| Telling a builder's brief apart from a reviewer's | **Kept, and now stated.** `tools/review_ledger.py` classifies a subagent by the first 400 characters of its brief. The old planner wrote briefs that opened *"You are the implementing coder"*; with no planner, nothing told the agent to open a builder's brief with its job, and a builder's brief can carry reviewer words from whatever the lead writes into it, so a brief without a builder phrase would be counted as a review pass of the work it wrote |

**What was not changed, and why.** The `IMPLEMENTER` and `REVIEWER` names inside
`tools/review_ledger.py` and its test classify *briefs*, which survive the split as a builder and a
reviewer subagent; renaming them would also stop them matching the briefs already in the transcript
corpus. Plans, retrospectives, release records and in-code incident narratives keep their wording,
because they record who did what on the day. `CLAUDE.md` carries one sentence saying to read both
words in them as the one agent, so the old text still resolves without being rewritten.

**What is not known.** The pause handover left open whether the ownership boundary cost throughput:
two measurements, neither a population. Removing it settles the process, not that question.
