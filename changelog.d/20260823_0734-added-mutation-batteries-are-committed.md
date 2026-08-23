- **Mutation batteries are committed, one per target, in `tools/batteries/`.** 73 mutants written
  across six increments existed only in session scratchpads; a fourth battery covers `mutate.py`
  itself, for 91 in all, and every one is `KILLED` against the tree it describes. `tools/mutate.py
  --check-anchors <battery>…` resolves every anchor against the **working tree** and exits — no
  subprocess, milliseconds — so *do the committed batteries still hold?* is cheap enough to ask. It
  reports every failure rather than the first, refuses when two batteries claim one file, and says
  on success which two rots it cannot see. A run still takes one battery at a time, and each battery
  declares `mutants = N` so the corpus cannot shrink silently. `tests/test_batteries.py` gates the
  same properties inside `./check.sh`, plus the `kills` selectors resolving — the axis the record
  says actually rots. **It is a resolvability gate, not a regression gate:** nothing runs a battery
  automatically, and `mutate.py` exits 0 when mutants survive. The convention, the naming and what
  to do when an anchor rots:
  [`tools/batteries/README.md`](https://github.com/lucagattoni/pinakes/blob/main/tools/batteries/README.md).
