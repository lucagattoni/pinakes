- **A rule for landing beside another session, because the tool that looks like one is not one.**
  `tools/shared_file_overlap.py` compares a branch to `origin/main` and never to another branch, so
  it reports *none* while a peer holds a branch touching the same files — a merge-safety check read
  as a peer check. [`docs/RELEASING.md` § *Landing beside a peer*](RELEASING.md) now says to
  intersect file sets against every live branch directly, and to settle the **order** rather than
  only the overlap: a peer's new gate can be red on `main` until your fix lands, which makes the
  order forced rather than negotiable. **You find that by running their gate, not by asking them** —
  they are running it on their own tree, where it passes. Both halves were measured on 20260823,
  between the two sessions that met them.
