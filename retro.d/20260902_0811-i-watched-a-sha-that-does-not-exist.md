## I armed a CI watcher on a sha I had composed, not read (20260902 08:11)

Three consecutive tips had their CI verdicts lost to supersession, so I armed a bounded watcher on
`main`'s tip and told the user I would land nothing until it reported. It polled and reported
nothing. I read that silence as correct and said so in as many words: *"My bounded poll has produced
no output yet, which is correct — it only writes when every workflow on that sha reports."*

It was not correct. The watcher was polling
`6a9245aca7bb5aeb0d0b30ba1c4ab4a5bd9b5cbb`. The tip is `6a9245aff04805cff66ed3d1c4f17d72b6fab4dc`.
The two agree on the seven characters I had in front of me and diverge on the thirty-three I did not.
**I expanded a short sha into a full one by writing plausible hex.** `gh run list --commit <that>`
returns `[]`, the loop's `[ -n "$row" ]` guard never passes, and the watcher runs to exhaustion
printing an empty verdict block. It could not have reported a red build. It could not have reported
anything.

The verdict arrived from the coder's watcher instead, and I verified it myself: run 33606706108, CI
completed/success, 15 of 15 jobs green, headSha matching the real tip. So the outcome was fine and the
instrument was worthless, which is the worst pairing — nothing about the result told me the tool was
broken. I found it only when stopping the task printed the command back to me.

**Two failures, and the second is the bad one.**

The first is composing an identifier instead of reading it — `git rev-parse` was one call away, and the
repo already carries this rule for timestamps (*read the clock, never compose it*). It generalises: a
sha, a run id, a version, a line number. If it identifies something, read it from the thing.

The second is that I had a null result and treated it as a measurement. Zero rows from `gh` and zero
output from the watcher are the same shape as *not finished yet*, and I picked the reading that
matched what I expected. **A selector that has never been shown to fire cannot report absence** — this
is written down, and I had cited it in this very session while reviewing someone else's work.

**What would have caught it, cheaply:** before arming any watcher, run its query once in the
foreground and confirm it returns a non-empty row. A watcher whose first poll matches nothing is not
waiting; it is misaddressed. That check costs one command and is the difference between a hold that
means something and a hold that is decoration.

This is the third instance in one night of the same family: a status list read without asking what it
was capable of containing (a false RED), a workflow absent rather than cancelled because its path
filter never matched, and now a query addressed at nothing. In all three the empty or partial answer
was read as information about the instrument's world rather than about the instrument.

**A postscript, because it happened while this file was being written.** Investigating the above, I
found two landed fragments linking a sibling by filename — forbidden by `retro.d/README.md` because
the path stops resolving once everything is spliced into one document. I proved it (`make docs` exit
2, two strict-mode warnings naming that link), fixed both, and then ran `git checkout -- retro.d/` to
undo the splice. That restored the two fragments to `HEAD`, **discarding the fix I had just made**,
and deleted this file, which was untracked and had been consumed by `--apply`. The repo warns about
exactly this — *commit before mutating; `git checkout` restores to the last commit, not to the
pre-mutation state.* I had also been told the count: `ls retro.d/*.md | wc -l` printed **24** where
25 was correct, and I read the number without checking it against what should have been there. **A
count you do not predict before you read it cannot surprise you**, which is the same defect as the
watcher — an instrument consulted with no expectation attached reports nothing either way.
