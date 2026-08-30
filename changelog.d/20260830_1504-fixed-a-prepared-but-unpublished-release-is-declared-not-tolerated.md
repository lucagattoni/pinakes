- **`release_order_gate` no longer has to choose between a false claim and a red gate.** 0.30.3 was
  prepared 20260825, never tagged, and reached no index — its fix ships inside 0.31.0. Both PyPI
  sequences declare `newest_may_lag`, so while 0.30.3 was the newest thing missing the gate was
  legitimately green; the moment the post-publish sweep added 0.31.0 it became an **interior hole**,
  which lag does not cover and must not. **Lag explains a missing newest; only a declared absence
  explains a missing middle.** 0.30.3 is now declared absent from the *Published on PyPI* prose and
  the *Published versions* row — the two lists that record what an index actually serves — and from
  **nothing else**: it stays expected in `CHANGELOG.md`'s headings and link definitions,
  `docs/ROADMAP.md`'s table and sections, and `docs/STATUS.md`'s release roadmap, because it is a
  real release *document* and only never a published artifact. Both declarations read one shared
  constant, so the two reasons cannot drift apart, and the allowance is printed on the green run —
  a tolerated gap and a declared one are otherwise identical from an exit status. Unlike 0.11.0's
  exception beside it, **this one never retires**: PyPI does not accept a version twice and nothing
  was uploaded under 0.30.3, so the only way to delete the declaration is to add 0.30.3 to a list of
  published versions, which is the claim it exists to refuse.
