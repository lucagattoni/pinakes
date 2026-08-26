## Taking eight decisions into the documents — what the writing found (20260825 18:55)

The decisions were taken by the user at 20260825 18:16. This is what surfaced while writing them
into the files, and every item is something the deciding pass did not know.

**HIGH — a correction about false precision was itself a timezone error, and it nearly propagated.**
The decision record listed three defects in `docs/VERIFICATION.md`'s scope sentence. Two were
already resolved before the pass began: the 923→890 row count was corrected earlier the same day,
and the *"impossible"* provenance stamp is not impossible — `c23359f` is
`2026-08-25T13:42:55+01:00`, i.e. **12:42:55 UTC**, so the 12:49 UTC measurement is seven minutes
*after* it. An adversary read a local timestamp as UTC. **Had the planner trusted the list rather
than checking it, it would have "fixed" a correct stamp into a wrong one** — a repair that
manufactures the defect it repairs. Checked with `git show -s --format=%ad --date=iso-local`, not
by reading.

**HIGH — the two numbers in one sentence rotted the same way, and the earlier correction pass fixed
only one of them.** The same sentence carried *"890 rows"* (corrected) and *"62 of the 67 test
modules"* (left). The module figure was wrong on **both** halves: there are **74** modules and
**63** carry a row. **A sentence with two numbers of one class is a sentence where correcting one
and stopping is the likely failure** — the reader's eye treats the sentence as handled.

**HIGH — the obvious way to count that sentence reports 74 of 74 and finds nothing.** Counting
"modules named in the document" by testing whether each filename appears in the text is wrong here,
because **the preamble itself lists the eleven unnamed modules by name**. The measurement instrument
is contaminated by the prose it measures. The gate's own `REFERENCE` regex — which matches only a
`tests/x.py::y` reference — gives 63. This was hit live, mid-pass, and the wrong number was on
screen before the right one.

**HIGH — the bounded audit found a cluster, not an instance, and the cause was structural.** D-34
was licensed on one unrowed promise found by sampling. Auditing a single module found **14 of
`tests/test_serve.py`'s 31 tests unrowed**, two of them security boundaries: the MCP path-refusal
(`../../etc/passwd`) and the labelling of retrieved text as evidence rather than instruction.
**The cause was not neglect** — the server's rows lived under *the links release* and *page
citations*, and **no section owned the server boundary**. A missing section is invisible to every
gate and to every reader who checks whether *a* row exists. Fixed by adding the section, not by
adding rows to the wrong ones.

**MEDIUM — a tripwire whose condition was already met on the day it was armed.** The
staged-channel-gates clause said *"two entries exist and are deliberate… if a third appears, that is
the drift this rule exists to catch."* `docs/DESIGN.md` had carried a third entry of the same
shape since **five days before the clause was written**. It reported drift that was not drift, and
cost two separate readers a full pass. **A rule that counts instances rots; a rule that names a
class does not.** It now forbids a class — no plan, no increment, no numbered item, no version
number — and says index, routing and naming entries are permitted and uncounted.

**MEDIUM — a count went stale eleven lines from a row that already carried the right one.**
`docs/README.md` said the sweep held *"fifteen confirmed defects"* in its prose and *"Sixteen
defects"* in the table below it. Both were written the same day. **Proximity is not consistency**,
and the same file is where a routing table already carries the instruction *"this row deliberately
states no count"* — a remedy that existed one row away and was not applied.

**HIGH, and the worst of these — a gate was cited as evidence for a property it cannot see.** A
blockquote annotating a table row was written *inside* the table, which renders it as a table cell.
The repair moved it after the last row **with no blank line**, so Python-Markdown's `tables`
extension swallowed it as one more `<tr>` — a cell whose text begins with a literal `>`. **`mkdocs
build --strict` exits 0 on the broken form and on the fixed one alike**, so *"`make docs` EXIT=0"*,
offered in a commit message as proof the repair worked, **certified nothing about the repair**. The
generalisation is the same one this project already applies to tests and to mutation batteries, and
it had not been carried across to gates: **make the gate red on purpose first. If it cannot fail on
the broken form, it is not evidence for the fixed one.** It is also the same failure as
`check.sh | tail` reporting `tail`'s exit status — a green signal that is not a function of the
property anyone cares about — and the two were hit by two different sessions within an hour.

**LOW, and it cuts against this pass — the writing changed the number the writing states.** The
scope sentence records the table's row count. Adding fourteen rows moved it from 890 to 904, so a
count copied from the parent commit would have been falsified **by the edit that copied it**. Stated
in the file rather than silently re-measured, because it is the third time in one day a change here
invalidated a pointer to itself.
