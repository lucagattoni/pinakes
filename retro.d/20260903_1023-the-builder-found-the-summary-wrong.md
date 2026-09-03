## The summary sentence disagreed with the table one screen above it (20260903 10:23)

**MEDIUM — a plan's prose register and its own table register drifted apart, and the person who
noticed was the one *building* from it, not anyone reading it.**

`plans/20260825_1240-run-pinakes-sweep.md` carried, in its build-order discussion, the sentence
*"S1, S5, S6, S8, S9 all share one shape — an input the tool accepts and then mishandles, rather
than refuses"*. Its own findings table, some four hundred lines earlier in the same file, defines **S6** as a
message that fires **on ordinary deletion** — no input is involved anywhere in it. The user
performs a correct, complete deletion and the tool makes a false statement about what it did.

Three things are worth keeping out of it.

**The generalisation was the defect, not a typo.** Four of the five findings really did share that
shape, which is exactly why the fifth was swept in without anyone re-reading it. A summary is a
claim about a set, and a claim about a set is only as good as the member you checked last.

**The document's two registers had already been recorded as a failure mode here — twice — and it
still recurred inside the file doing the recording.** `20260825_1252-plans-sweep-findings.md` holds
two registers of the same facts and twelve of its 27 rows stopped describing the tree; the rule
written from that says *where a dated snapshot and a `## Build order` disagree, the build order
wins*. What this instance adds: the two registers can be **prose and a table in one file**, close
enough that nobody thinks of them as two registers at all.

**Building is a stronger read than reading.** Nothing about the sentence looks wrong. It reads as a
competent summary, and it survived every pass over this plan until a coder had to decide whether S6
belonged in the same guard as S8 and S9 — a question the sentence answers wrongly and a build
answers correctly. The same pass returned two other things the plan did not have: a third arm of S8
(`-k 0` is falsy, so `limit or manifest.retrieval.final_k` silently substitutes the default) and a
third state of S6 under its decided fix. **Cheapest available review of a planning document: give it
to someone who has to act on it.**

Corrected in place: the sentence is now a three-mechanism table — a mishandled input (S5, S8, S9,
and S1 shipped in 0.32.0), a false reporting predicate (S6), and state that never clears (S7, which
the original sentence never mentioned at all).
