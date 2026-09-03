## A docstring can claim a surface the code never reached (20260903 12:58)

**HIGH — written as intent, committed as fact, and it was the only record of the gap.** The
closed-set constant added in row 8 carried this, in my own words:

> That is what lets the CLI and the MCP server refuse one at the boundary instead of returning an
> empty result the user reads as an empty KB.

The guard was wired into `pnk search`'s argparse and **nowhere else**. `pinakes_search` built its
`Filters` from whatever the client sent, so `source_type="markdwon"` still returned zero passages
under *"nothing matched the filters"* — the exact defect the increment existed to close, alive on
the surface `CLAUDE.md`'s naming table lists beside the CLI, under a sentence stating it was
closed. `eval.py`'s question loader had it too, where an unrefused typo scores that question zero
recall on every run and reads off an eval table as a retrieval regression rather than as a typo.

**The mechanism is ordinary and that is why it is worth a fragment.** The docstring was written
while the fix was being designed, when *"the CLI and the MCP server"* was a true description of the
plan. The plan then shrank to the surface that was in front of me, and the sentence did not. No
gate compares a docstring to the code it sits beside, and a reader has no way to tell a statement
of intent from a statement of fact once both are committed.

**Two things follow.** First, a claim about *another* module belongs in a test, not a docstring —
the check now lives in one helper the three surfaces call, so the sentence and the code cannot
drift again. Second, when a fix names surfaces, **enumerate the constructors** rather than the
surfaces: `grep -rn 'Filters(' src tools` is two seconds and finds every entry point, where
recalling which surfaces exist finds the ones you were already thinking about.
