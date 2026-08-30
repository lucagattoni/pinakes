## The marker was 0-for-2 because the procedure never asked for it (20260826 07:27)

**MEDIUM — a convention with a 0-for-2 record was blamed on the people following it, and the
procedure had never contained it.** `docs/STATUS.md`'s hold marker had been written twice and missed
twice, and that record is what justified building a gate (D-35 layer 2). It is a good gate. But
`docs/RELEASING.md` — the document a release operator actually follows, whose sweep table exists
precisely to name every place a release goes stale — **never mentioned the marker at all.** A release
cut by following it verbatim produces the false line, every time, correctly. **Before building a gate
because a convention keeps being missed, check that the convention is written where the person doing
the work would read it.** Both were worth doing here; only one of them was diagnosed.

**MEDIUM — the live marker carried a claim its own gate had deliberately rejected.** Line 3 read
*"landed on `main`, NOT tagged and NOT on PyPI"*. The coder had explicitly cut *NOT tagged* from the
gate's suggested text, because it is a claim about **git** that goes false at `git tag` while the
version is still unpublished — the line would be half-wrong for the whole tag-to-publish interval,
with the gate green over it (`HOLD` requires only `⏸` and a bold span naming the published version).
**The reasoning had been recorded in the gate's docstring and the document it governs was never
brought into line.** A decision written down next to the code is not a decision applied to the data.

**LOW, and it is the third instance today of one trap.** Driving the gate red on purpose, the first
measurement was `uv run python tools/status_header_gate.py 2>&1 | grep -v warning; echo $?` — which
reports **`grep`'s** status, not the gate's, and printed `0` for a run that had just failed. The
coder hit the identical shape with `| tail -1` an hour earlier and wrote it up as *"a rule written
about `check.sh` got read as being about `check.sh`"*. **The rule is not about a file; it is about
whatever command's exit status you are actually reading** — and an ad-hoc pipe typed to inspect a
result is exactly where it is forgotten, because it does not look like a gate. Re-measured bare:
**exit 1 without the marker, exit 0 with it.**
