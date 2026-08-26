## The remedy for a bad survivor had a false-positive mode, and it was in the advice (20260826 11:46)

`tools/batteries/README.md` § *Reading a SURVIVED row* told you to **run the mutant against the whole
suite** to tell a mis-named witness from a real gap. **That advice has a false positive, and it fires
on exactly the batteries covering `tools/`.**

**MEDIUM — the whole suite includes the test that fails on any edit to a battery target.**
`tests/test_batteries.py::test_every_anchor_still_resolves_exactly_once_in_the_file_it_names` checks
that each battery's `old` string still resolves in the file it names — and **a mutant is precisely an
edit to that string.** So the suite goes red for a survivor exactly as readily as for a kill, and
*"something else killed it"* — the conclusion the paragraph tells you to draw — is unreachable from
the evidence it tells you to gather.

**Measured, not argued.** Applying `tools-fragments.toml`'s first mutant to `tools/fragments.py`
(`return line.rstrip() == "---"` → `return False`) and running the two files separately:

| | exit | |
|---|---|---|
| the row's own `kills` selector | **1** | a genuine kill — the behaviour is tested |
| `tests/test_batteries.py` | **1** | `1 failed, 10 passed` — the anchor check, not a behaviour test |

Restored, `__pycache__` cleared, both green again: 51 passed. The fix is one flag —
`uv run pytest --ignore=tests/test_batteries.py` — now in the paragraph, with the reason beside it.

**LOW, and it is the part worth generalising: `tools/mutate.py` was never wrong.** It runs only the
selector a row names, so its report was honest throughout. **The defect lived in the prose that told
a human what to do next**, and prose is not covered by anything. A tool can be correct, its tests
green, its battery complete — and the sentence telling you how to read its output can still send you
to the wrong diagnosis. **Found by a coder following the instruction literally and noticing the kill
was the wrong shape**, which is the only way this class is ever found.

**And the correction improved on the framing it corrected.** The first version of this finding — mine
— said a whole-suite mutant run *"scored a kill that was an artifact"*, which reads as a defect in
the harness. It is not: the harness never made the claim. Locating a defect in the **advice** rather
than the tool is what makes it fixable in one flag instead of a redesign.
