## Re-running a measurement is not enough when there are two artifacts to run it against (20260901 06:33)

**The rule that has caught every one of these is "re-run the measurement".** It assumes there is
one thing to re-run against. On the night of 20260831–0901 that assumption broke, and the break is
worth more than the eight instances it sits at the end of.

Two sessions disputed a count. One had reported `tools/agent_spend.py` at **2** mentions; the
other counted **12**. Both numbers were right — different selectors, one stated and one not. In
correcting the record, the first session asserted its table had carried the selector *on every row*.
It checked, and reported that it had.

**It had checked the wrong artifact.** The bash output it generated printed the selector on every
row. The message it actually sent reformatted that and carried the selector **once**. Both artifacts
were its own, both were to hand, and they differed in exactly the detail under dispute. The one it
opened was the one that agreed with it.

**So the mechanism is a substitution, not an omission** — and that is what makes it new. The other
seven instances that night were a population going missing, a denominator borrowed from next door,
a qualifier lost between evidence and conclusion, a ref left unstated. Each is *something absent*.
This one is the right kind of evidence, examined carefully, **about the wrong object**.

**The practical lesson, which is the reason this is written down:** *"check the artifact rather than
your memory of it"* is an incomplete instruction, because it does not say **which** artifact. When
several exist, the nearest to hand is the one that flatters. A check has to name its object before
it runs, the same way a count has to name its selector.

**It happened inside the correction.** The claim was made in a message correcting another session's
record of unstated selectors, in the sentence inviting that session to check the artifact rather
than the memory of it, on the night whose entire subject was this failure family. The timestamps
carry that without it needing to be argued.

**What actually recovered it, both times, was a peer checking a claim that cut against itself.**
The second session verified the table, found it reproduced exactly, and struck its own sentence.
The first session then re-checked its own correction and found the substitution. Neither was caught
by a gate. **Of the eight instances that night, exactly one was caught by its own author before it
left a worktree** — by running a grep before committing rather than after — and it cost one command.
