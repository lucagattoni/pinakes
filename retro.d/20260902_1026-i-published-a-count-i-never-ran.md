## I published a count I never ran, and a peer nearly stopped a correct release (20260902 10:26)

I reported the 0.32.0 splice as **"12 changelog + 26 retro"**. The tree held **13 and 27**. The
release was correct; the number in my status message was not, and I had not measured it — I read it
off my own earlier prose rather than off `git ls-tree`.

**What it cost.** The coder reasoned correctly from my figure and reached a serious conclusion: if
one fewer of each was spliced, the missing pair is exactly S1's, and 0.32.0 would ship the fix while
describing nothing. It messaged **"stop before the tag"**. The tag was already pushed by the time
the message arrived, so the cost was a verification round rather than a release — but the reasoning
was sound and only the input was wrong.

Two commands settled it, both of which I should have run before quoting a number:

    git ls-tree --name-only v0.32.0 changelog.d/ retro.d/ | grep 20260902_0927   # empty
    git show v0.32.0:CHANGELOG.md | grep -c unreadable                          # 18

**The lesson is not "count more carefully".** It is that a number inside a status report is a claim
with the same standing as a number inside a document, and it travels further and faster because
peers act on it directly. This repository already rules that a claim resting on a set you selected
must state its selector. A count in a message has a selector too — `git ls-tree <ref> <dir>` — and
naming it is what makes the claim checkable by the person receiving it.

**What the coder did right, and it is the reusable half:** it said plainly that it could not verify
the branch (it was not on the remote), declined to assert the defect, and handed me the two commands
that would settle it either way. A well-formed doubt with its own falsification attached costs sixty
seconds. The same doubt asserted as a finding would have cost an argument.
