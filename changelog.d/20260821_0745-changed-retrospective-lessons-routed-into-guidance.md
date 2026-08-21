- **The build guidance now carries the retrospectives' recurring lessons.** `docs/BUILDING.md`
  gains the mutation-harness discipline (commit before mutating, anchor asserted once,
  `__pycache__` cleared, no `-x`, one known kill first), the gate-exit-status rule, the CI-matrix
  leg check and two rules for reading a plan; `docs/RETROSPECTIVES.md` § *Start here* gains four
  rows routing the post-20260801 failure classes — mutation passes, measurement tools, test seams
  and review fixes; `CLAUDE.md` § *Changing retrieval* names which corpus can license a change,
  its live-plan block slims to pointers with the deep plan's E6 status recorded in the plan
  itself; and `plans/` gains a proposal for a committed mutation harness, `tools/mutate.py`.
