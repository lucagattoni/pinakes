## A gate cited by a procedure it cannot read (20260822 06:35)

`docs/RELEASING.md`'s sweep table names five places a release stales. One is STATUS's *Published on
PyPI* prose. Its "where the new entry goes" row answers: **`python3 tools/release_order_gate.py`
decides it.** No pattern in that gate matched the list. So the procedure delegated a placement
decision to a check that could not read the document, and the green line `5 sequences in release
order` was read as covering a list it had never opened.

It drifted, as delegated-to-nobody things do: `0.25.1 → 0.25.3 → 0.25.2 → 0.25.4`, wrong on SemVer
*and* on verification time, surviving every green run from 20260821 to 20260822.

**The generalisable shape is not "a missing pattern". It is a citation nobody checked.** A document
naming a tool as the authority for something is a claim about that tool's coverage, and it is
exactly the kind of claim that is written once and never re-read. Grep the *other* direction
occasionally: for each gate, what do the documents say it covers, and does it?

Three things that fell out of building it, each worth more than the fix:

- **A gate reads an order; it cannot see a count.** Landed the same day, from the other side: a
  concurrent session appended "thirty-seven" to a sentence that still said "thirty-six", one line
  apart, through a green `check.sh`, a green `make docs` and a green `release_order_gate`. Caught by
  grepping the neighbourhood, not by reading the diff — the wrong half was *context*, so it never
  appeared in the diff at all. Counts stay a documentation rule for that reason.
- **"Tolerate it" needs a direction, or it is a hole.** This list is legitimately short between a
  release landing and its verification, because a claim about the index is held back until it is
  verified *from* the index. Exempting it from agreement is right; exempting it from *direction* is
  not. It may lag every other sequence and may never lead one — a paragraph about a release the
  CHANGELOG has never heard of is a claim nothing else records. The first draft had the exemption
  and no direction, and nothing could have told the two apart.
- **Say what the exemption costs, in the gate.** Because a missing newest entry is legal, an entry
  written in a shape the pattern does not match is indistinguishable from one not yet written —
  silently unchecked. The floor catches wholesale rot; it does not catch one mis-shaped newest
  entry. Undocumented limits get trusted past.

And one environmental trap, found before it could produce a false green: **this repo has no
`.python-version`**, so `uv` gave a fresh worktree CPython 3.14.7 while the primary checkout and CI
run 3.13. A green `./check.sh` in a new worktree is therefore not evidence about the interpreter
anything else uses. Pinned by hand here; the root fix is a proposal, not this increment's.
