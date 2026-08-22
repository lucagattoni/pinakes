## A gate must not derive a constant from the document it polices (20260822 17:52)

Membership's first draft derived each sequence's start version from the sequence itself — "the
oldest release it contains" — and justified it in the commit message: *the starts are observable and
monotonic; they never move backwards, because releases are never deleted.* Every clause of that is
true and the conclusion is still wrong. **The gate does not observe releases. It observes the
document.** Delete STATUS's `0.2.0` row and the derived start becomes `0.2.1`: the sequence is still
sorted, still contiguous, still internally consistent, and the gate reports green on precisely the
deletion it was built to catch.

It is the same failure the gate's own docstring already refuses one paragraph earlier — *the
direction is declared per sequence, never inferred, because a badly scrambled file would otherwise
elect its own answer.* I read that sentence while editing the file and then wrote the inferred
version of a different constant. **A rule stated about one field does not defend the next field
somebody adds.** Four declared constants cost four lines and cannot be argued into being wrong.

The general shape, worth checking on any gate here: **for each constant the gate uses, ask where it
came from. If the answer is "the thing being checked", it is not a constant, it is an echo.**

### A status read is not a status gated on

`CLAUDE.md` names this trap in its piped costume: `check | tail && git commit` reports `tail`'s
status, so a failing checker looks green. I hit the *unpiped* one and it is worth naming separately,
because the written rule did not cover it and I had read that rule the same day:

    ./check.sh > log 2>&1; echo "exit=$?"      # status printed, and read, and correct
    git add -A && git commit ...              # runs regardless, on the next line

The status was captured, printed, and true. Nothing consumed it. A commit landed over a red tree —
a lint error, caught later — and the log shows a green-looking sequence of steps. The pipe was never
the mechanism; **the mechanism is that the exit status must be what the next command reads**, and a
human reading it off the screen is not the next command. The fix is one wrapper:

    ./check.sh > log 2>&1; RC=$?
    if [ $RC -ne 0 ]; then …report…; else …commit…; fi

### And a third instance of *verify the remedy, not only the finding*

The exception mechanism for `0.11.0` was agreed with the planner as a **loose match** — find the
version anywhere in a `## ` heading. Implementing it meant first finding where that heading actually
is: `docs/ROADMAP.md:1721`, **inside `# Part 5`**, with the release table linking to it on purpose.
`0.11.0` has no Part 4 section by design. The loose match would have taken that heading as its
release section and failed twice on a correct document — placement, because Part 5 declares no
range, and ordering, because it follows `0.27.2`.

The finding was right: membership needs an exception mechanism. The remedy attached to it was wrong,
and the risk that killed it had been named *in the same message that proposed it* — "matching a
version anywhere widens what counts as a release section" — and read by both of us as hypothetical.
It was not hypothetical; the widened set already had a legitimate member. **A risk stated beside a
remedy is not a risk that has been checked.**
