- **A symlink that resolves to nothing is reported by `pnk sync` rather than skipped in silence.**
  The source walk asks `is_file()`, which is false for a symlink whose target is missing or whose
  links loop, and the path was then dropped without a word — indistinguishable from a path that was
  never there. `pnk sync` now names it: *"symlink could not be resolved, so it was not indexed"*,
  and says the target is missing, unreadable, or looping — three causes rather than two, because a
  target this process cannot reach is indistinguishable from one that was never there, and nothing
  at that point can tell you which of the three it hit. A symlink to a real **directory** is an ordinary alias and is not reported; a
  symlink to a real document is indexed exactly as before; and a healthy tree says nothing about
  symlinks at all.
