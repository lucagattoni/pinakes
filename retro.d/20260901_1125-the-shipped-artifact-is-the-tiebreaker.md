## When a gate and a convention disagree, the shipped artifact is the tiebreaker — and it costs one grep (20260901 11:25)

`main` went red on a link I wrote. The gate said the anchor did not exist; the gate's own error
message said to put it in a code span. Two peers reproduced it independently, diagnosed it
identically, and both recommended the same fix. Everything pointed one way: **my fragment was
wrong, correct it.**

It was not wrong. `retro.d/README.md:40-48` *instructs* fragment authors to write exactly that form,
and one grep settled which of the two was defective:

    $ grep -c '](#[a-z0-9_-]*-20[0-9]\{6\}-[0-9]\{4\})' docs/RETROSPECTIVES.md
    2
    $ sed -n '4034p' docs/RETROSPECTIVES.md      # links to the heading at :3945
    ([*measured the launcher, not the work*](#measure_sync_cpupy-measured-the-launcher-not-the-work-20260805-1737))

The form is **live in the published document and `mkdocs --strict` passes over it**. So the link was
right about where it was going, and the gate is half-built: `tools/markdown_link_gate.py` models a
fragment's *disappearance* at splice time (`:296-305`, because `--apply` deletes it) and not its
*destination*. The fix I applied is still the code span — `main` was blocking three branches — but it
is now recorded as **a temporary degradation of a correct link**, with a build-order row to remove
it, rather than as a correction. Those are different entries in the register, and only one of them
gets undone later.

**Two things to keep.**

**A gate is evidence about the tree, not about the convention.** When a checker and a documented
instruction contradict each other, at least one is a defect and the checker is not automatically the
survivor. The tiebreaker is the artifact the convention exists to produce — here, the published
document, where the disputed form already worked. That is a grep, not an argument, and it is
available before any of the reasoning starts.

**Two peers agreeing is not two independent checks when the error message framed them both.** Both
reproduced the failure faithfully and neither asked whether the form already shipped, because the
gate's message had already named the fragment as the thing to fix. Convergence measured agreement
with the framing, not with the tree. The question that separated them from it — *does this form
already work somewhere?* — was not a better inference; it was a different population, and nobody had
named one. It is the sibling of *a null result carries no information until the selector is shown
able to fire*: **a shared premise makes independent agents into one agent.**

Related, and the reason this fragment exists at all: the same landing found that four of the eight
rows parked in `plans/20260825_1240-run-pinakes-sweep.md` were already done — a register whose
stated purpose is to stop work ageing, ageing at 50%. Every remaining row now carries a command that
says whether it is still live, because a row is a claim about the tree on the day it was written and
nothing re-checks it.
