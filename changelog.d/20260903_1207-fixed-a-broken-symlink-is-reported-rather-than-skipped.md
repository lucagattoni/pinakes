- **A symlink that resolves to nothing is reported by `pnk sync` rather than skipped in silence.**
  The source walk asks `is_file()`, which is false for a symlink whose target is missing or whose
  links loop, and the path was then dropped without a word — indistinguishable from a path that was
  never there. `pnk sync` now names it: *"symlink resolves to nothing, so it was not indexed"*, with
  the reason. A symlink to a real document is indexed exactly as before, and a healthy tree says
  nothing about symlinks at all.
