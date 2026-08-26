- **Every decided item now carries a build-order row, and the registers that disagreed about them
  have been reconciled against the tree.** Three pieces of decided work had an **owner and no queue
  position anywhere in the repository** — the `_toml.py` unknown-key remedy, the paid re-extraction
  loop's deferral trigger, and the G5 gate re-run, which sat in that state for **21 days**. They now
  have rows in the sweep plan's new § *Decided work with an owner and no build order*, each linking
  to the plan that owns the decision rather than restating it. D-36's build, which read *build
  unscheduled*, gained a position; S16 and S18 gained rows they never had; and S2 is recorded as
  built rather than queued.
- **A dated snapshot no longer reads as a work queue.** The *Actionable* table in the 20260825 plans
  sweep held **27 rows with Status, Blocked-on and Owner columns**, and **twelve of them had stopped
  describing the tree** — eleven claiming *LIVE* or *user-decision* for work that was built,
  answered, declined, deferred or ruled between 18:16 and 18:41 that same evening — **wrong for
  twelve hours**, and row 1 read *S2 · LIVE · blocked on nothing* from the moment S2 landed. The cause was
  structural rather than neglect: **that file carries two registers of the same facts**, and the
  pass that took the decisions updated one and not the other. The table now states that it is a
  snapshot, and that **where it and a `## Build order` disagree, the build order wins**.
