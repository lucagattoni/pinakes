## I measured the live directory and answered about the corpus (20260902 00:07)

A ruling needed to know how often a retro fragment carries a second `## ` heading. I counted the
live directory — **0 of 14** — and told a peer the question was "entirely prospective". The number
was right. The sentence was about a different population, and it was wrong: across every fragment
that has ever existed there are **two**, and one of them is the case the ruling turns on.

`retro.d/` is a **consuming** directory. Every release splices its fragments into
`docs/RETROSPECTIVES.md` and deletes them, so the live directory is not a sample of the corpus —
it is the handful written since the last release. Counting it and generalising is not a small
extrapolation from a large sample; it is a claim about 129 things made by looking at 14. The peer
found the two, and had it not, the ruling would have been justified by a population that excluded
its own counterexample.

**Then the correction repeated the mistake one level down.** Asked to check the full history, I
walked `git log` per path and read each fragment at the newest commit that *touched* it. For a
consumed fragment that commit is the one that **deleted** it, so `git show` returns empty. My probe
reported "0 commits touched" for six paths — a self-contradiction, since those paths came out of the
log — and I only noticed because my total disagreed with the peer's. Their probe had the same defect
and skipped 115 of 127 silently. Two independent probes, the same blind spot, because it is a
property of the directory and not of either implementation.

What settled it was changing instrument rather than fixing the query: `git rev-list --all --objects`
enumerates every blob ever reachable and `git cat-file` reads one by hash. There is no path-to-commit
lookup, so there is nothing to get wrong — **129 paths, 239 distinct versions, `unreadable: 0`**, and
the count fires twice. A probe that cannot report what it failed to read is worth less than one that
reads less and says so.

**The last step was the one that nearly went wrong in the other direction.** Two instances looked
like enough to weaken the ruling, since the second fragment stamps neither heading. The obvious move
was to set it aside as pre-convention — and that is false: **10 of 126 fragments have an unstamped
first heading, scattered to the day before this was written**. Stamping never became universal, so
there is no cohort boundary to hide behind. It is ordinary non-compliance, it licenses nothing about
second headings, and the ruling stands at n=1. The reason it stands is not the reason I first had.

**The rule.** Before generalising a count, name the population the number came from and ask whether
the directory deletes. Where a probe can silently skip, prefer the instrument with no lookup to get
wrong — and make it report what it could not read, because a zero and an unreachable set look
identical in the output.
