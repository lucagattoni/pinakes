- **Mutation batteries are committed, one per target, in `tools/batteries/`.** 73 mutants written
  across six increments existed only in session scratchpads; all 73 are `KILLED` against the tree
  they describe. `tools/mutate.py --check-anchors <battery>…` resolves every anchor against the
  **working tree** and exits — no subprocess, milliseconds — so *do the committed batteries still
  hold?* is cheap enough to ask. It reports every failure rather than the first, refuses when two
  batteries claim one file, and says on success which two rots it cannot see. A run still takes one
  battery at a time. `tests/test_batteries.py` gates the same properties inside `./check.sh`, plus
  the `kills` selectors resolving — the rot `--check-anchors` deliberately does not look for. The
  convention, the naming and what to do when an anchor rots:
  [`tools/batteries/README.md`](https://github.com/lucagattoni/pinakes/blob/main/tools/batteries/README.md).
