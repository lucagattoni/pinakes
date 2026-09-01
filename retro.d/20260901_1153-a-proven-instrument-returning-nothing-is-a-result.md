## Two of us searched for how a file was deleted; it had never been deleted (20260901 11:53)

A fixture written into the real `retro.d/` by a runaway probe was gone by the time anyone looked for
it. A peer went after the mechanism properly: `grep -r 'git clean'` across **every** `*.jsonl` under
the project's session directory, then `grep -r` for any `rm` naming the file. Both returned nothing.
They reported it honestly — *"an untracked file with no `git` record and no `rm` on record is exactly
the class of event that leaves no evidence, which is itself the finding"* — and I had reached the same
dead end from the other side.

The file was in my own scratchpad. I had moved it there during recovery, when I backed up what was
untracked, and neither of us thought to look in the place the recovery notes said it went.

**The error is not that we missed a directory.** It is what we did with a null result. The standing
rule here is that *a null result carries no information until the selector is shown able to fire* — and
these selectors **had** fired: the same greps, over the same files, returned a583's six `rm -f
retro.d/*.md` calls and acea's two. The instrument was proven on the run that produced the zero. So
the zero was not an absence of evidence; it was evidence, and what it said was **the premise is
wrong** — nothing deleted the file because the file was never deleted.

That is the half of the rule I had never written down. Once the selector is proven, a null stops being
a gap and becomes a finding, and the finding is usually about the question rather than the world. We
each kept the question ("what deleted it?") and spent the result on doubting our coverage.

**The tell was available and cheap.** Both of us had already searched for the deletion; neither of us
had searched for the *file*. One `find` over the enclosing directories would have ended it in seconds,
and `find` is the query that does not presuppose the event. When a mechanism search comes back empty on
a proven instrument, the next query should drop the mechanism, not widen it — ask where the thing is,
not what removed it.

Fourth time on this one incident that a symptom was matched to a named mechanism before the premise was
checked, and the first where the unchecked premise was mine.
