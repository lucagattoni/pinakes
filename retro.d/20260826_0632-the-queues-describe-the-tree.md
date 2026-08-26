## Reconciling the queues — two registers of one fact, and an owner with nowhere to queue (20260826 06:32)

The increment was meant to close a scheduling gap `CLAUDE.md` names in bold. It found the gap was
the smaller half.

**HIGH — a file that holds two registers of the same facts will diverge, and no gate can see it.**
`plans/20260825_1252-plans-sweep-findings.md` carries a 27-row *Actionable* table with **Status,
Blocked-on and Owner** columns, and a § *Open questions* list of thirteen bullets. They describe the
same decisions. The 20260825 18:16–18:41 pass updated the bullets, inline, carefully — and never
touched the table. **Twelve of the 27 rows stopped describing the tree** — eleven of them stating
*LIVE* (eight) or *UNCLEAR* (three) for work that was built, answered, declined, deferred or ruled
that evening. This is the repository's own recorded failure — *a `##` heading is a status claim and
nothing gates it* — moved one level in, **into a table cell**, where reading the item's body does not
help because the body is the cell. **The fix is not to maintain both.** It is to say which one wins:
a dated snapshot carries a disposition, a `## Build order` carries the queue, and where they
disagree the build order is right by construction.

**HIGH — an owner is not a schedule, and the difference is measured in weeks.** Three decided items
had an owner and **no queue position anywhere**: the `_toml.py` unknown-key remedy, the paid
re-extraction loop's trigger, and the G5 gate re-run — which sat that way for **21 days** while
every sweep that read headings passed over it. The seam is structural: an item whose owning plan has
no `## Build order` has nowhere to be queued, and `docs/README.md` routes to *files*, not to work.
Parking them in one named section beat both alternatives — a fourth register would repeat the defect
above, and a build order per plan makes a coder read four files to learn what is next, which is how
the seam formed.

**HIGH — the top of the coder's queue was a claim nobody had re-checked, and checking it took nine
minutes.** `CLAUDE.md` said S16 was *"still live, reproduced on `main` 20260826"*. **Nothing in the
sweep plan supported that date** — the only run on record is `32442db`, **20260825 18:18**, which is
*before* S2's fix landed at 04:06 the next morning. And S2's fix is known to have **cured S17 as a
side effect**, so "does it also cure S16?" was a live question that no document had asked. Reproduced
end to end against a `src/` tree byte-identical to `origin/main`: **it is still live**, all three
failures intact. The finding is not that the claim was false — it happened to be true — but that
**nobody could have known, and it was written as though someone did**. A defect recorded against a
moving tree needs its sha; S17 was recorded the same way and had already been fixed.

**MEDIUM — reading names instead of targets put a false claim in a file that exists to state a
denominator honestly.** `tools/batteries/README.md` named `src/pinakes/cli.py` among *"the two
highest-churn modules … [that] still have none"*. `src-pinakes-init.toml` mutates it **twice**. The
same error hides more: `tools-mcp_handshake_gate.toml` reaches **seven** files including `Makefile`,
`check.sh`, `pyproject.toml` and both CI workflows. **A battery's name is not its coverage**, and
the question has a one-line answer nobody was asking —
`grep -h 'file = ' tools/batteries/*.toml | sort -u`. Its own gate could not catch it:
`tests/test_batteries.py` forces a battery whose stem does not begin `tools-` to be named in the
README, and checks nothing about what the batteries reach.

**MEDIUM — I invented a duration inside a pass about unmeasured claims.** I wrote *"fourteen hours"*
for how long the table said `S2 · LIVE`, four times across four files, and **never computed it**.
**That count is not re-derivable from git and this sentence is the only record of it** — the error
was corrected *before* the first commit, so history contains this description and not one instance.
Stated here rather than left to look like a measurement: it is a report of a working tree nobody
else can inspect, which is the weakest kind of claim this repository accepts and it is accepted only
because a retrospective has no other way to describe what it caught. S2
landed at 04:06 and the pass ran at 06:19: **two hours**. The eleven decision rows were the
twelve-hour ones. Two different numbers had been collapsed into one invented figure that flattered
the finding. Caught only because the timestamps had to be re-derived for an unrelated reason.

**MEDIUM — and the reason they had to be re-derived: `--date=format-local` where the rule says UTC.**
Local here is UTC+1, so `3876b57` went into three files as *05:06* when it is **04:06 UTC**. The
retrospective fragment written **twelve hours earlier** records an adversary making the same
substitution in the other direction, and says it *"would have 'fixed' a correct stamp into a wrong
one"*. **Reading that fragment did not prevent repeating it**, which is worth more than the fix: the
guard has to be in the command, not in the memory of a lesson. `git log` takes `--date=format-local`
and `TZ=UTC git log` gives the rule's answer; nothing warns you which you typed.

**LOW — `main` moved twice during the pass, and once it falsified a row as it was being written.**
A branch recorded as unowned — its author's session ended, and a direct message to the only other
candidate failed `HTTP 409` — landed while that row was being drafted. A peer said so; the claim was
verified against `git ls-remote` rather than relayed, and the row was deleted before it was
committed. The rule that saved it is the cheap one: **verify at the moment of landing, not at the
start.**
